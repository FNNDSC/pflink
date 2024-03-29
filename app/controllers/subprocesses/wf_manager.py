import argparse
import json
import logging
import pprint
import subprocess
import time
from logging.config import dictConfig

import requests

from app import log
from app.controllers.subprocesses.python_chris_client import PythonChrisClient
from app.controllers.subprocesses.subprocess_helper import Subprocess
from app.controllers.subprocesses.utils import (
    request_to_dict,
    dict_to_hash,
    update_workflow,
    retrieve_workflow,
    get_cube_url_from_pfdcm,
    substitute_dicom_tags,
    do_cube_create_user,
    retrieve_pfdcm_url,
)
from app.models.workflow import (
    Error,
    State,
    Warnings,
    WorkflowRequestSchema,
    WorkflowDBSchema,
    WorkflowStatusResponseSchema,
)

dictConfig(log.log_config)
logger = logging.getLogger('pflink-logger')
d = {'workername': 'WORKFLOW_MGR', 'key' : "",'log_color': "\33[33m"}


def define_parameters():
    """
    Define CLI parameters for this module here
    """
    parser = argparse.ArgumentParser(description='Process arguments')
    parser.add_argument('--data', type=str)
    parser.add_argument('--test', default=False, action='store_true')
    return parser

class WorkflowManager:
    """
    This module manages different states of a workflow by constantly checking the status of a workflow in the DB.
    """
    def __init__(self,args):
        """
        set some parameters here
        """
        self.args = args

    def run(self):
        d_data = json.loads(self.args.data)
        key = dict_to_hash(d_data)
        d['key'] = key
        self.manage_workflow(key, self.args.test)

    def manage_workflow(self, db_key: str, test: bool):
        """
        Manage workflow:
        Schedule task based on status from the DB
        """
        SLEEP_TIME = 10
        MAX_RETRIES = 50
        pl_inst_id = 0

        workflow = retrieve_workflow(db_key, test)
        logger.info(f"Fetching request status from the DB. Current status is {workflow.response.workflow_state}.",
                    extra=d)

        workflow = self.analysis_retry(workflow, db_key)

        if not workflow.response.status or test:
            # Do nothing and return
            reason = f"Workflow request failed. {workflow.response.error}." if not workflow.response.status \
                else f"Workflow already started."
            logger.warning(f"Cannot restart this workflow request. {reason}"
                           f" Kindly delete this request to restart using the delete API end point.", extra=d)
            return

        request = workflow.request

        pfdcm_url = retrieve_pfdcm_url(request.pfdcm_info.pfdcm_service)
        cube_url = get_cube_url_from_pfdcm(pfdcm_url, request.pfdcm_info.cube_service)

        while not workflow.response.workflow_state == State.ANALYZING and MAX_RETRIES > 0 and workflow.response.status:

            workflow.started = True
            update_workflow(db_key, workflow)
            MAX_RETRIES -= 1
            logger.debug(f"{MAX_RETRIES} iterations left.", extra=d)
            if workflow.stale:

                match workflow.response.workflow_state:

                    case State.INITIALIZING:
                        logger.info("Requesting PACS retrieve.", extra=d)
                        self.do_pfdcm_retrieve(request, pfdcm_url)

                    case State.REGISTERING:
                        logger.info(f"Registering progress is {workflow.response.state_progress} complete.", extra=d)
                        logger.info(f"Current feed request status is {workflow.feed_requested}", extra=d)

                        if workflow.response.state_progress == "100%" and not workflow.feed_requested:
                            try:
                                resp = self.do_cube_create_feed(request, cube_url, workflow.service_retry)
                                pl_inst_id = resp["pl_inst_id"]
                                feed_id = resp["feed_id"]
                                logger.info(f"New feed created with feed_id {feed_id}.", extra=d)
                                workflow.feed_id_generated = feed_id
                                logger.info(f"Setting feed requested status to True in the DB", extra=d)
                                workflow.feed_requested = True
                                update_workflow(db_key, workflow)
                                self.do_cube_start_analysis(pl_inst_id, request, cube_url)
                            except Exception as ex:
                                logger.error(Error.analysis.value + str(ex), extra=d)
                                workflow.response.error = Error.analysis.value + str(ex)
                                workflow.response.status = False
                                update_workflow(db_key, workflow)

                    case State.COMPLETED:
                        logger.info(f"Request is now complete. Exiting while loop. ", extra=d)
                        return
            else:
                logger.info(f"Database is stale. No task performed.", extra=d)

            logger.info(f"Calling status update subprocess.", extra=d)
            self.update_status(request)

            logger.info(f"Sleeping for {SLEEP_TIME} seconds.", extra=d)
            time.sleep(SLEEP_TIME)

            workflow = retrieve_workflow(db_key)
            logger.info(f"Fetching request status from DB. Current status is {workflow.response.workflow_state}.",
                        extra=d)

            # Reset workflow if pflink reached MAX no. of retries
            if MAX_RETRIES == 0:
                logger.warning(f"Maximum retry limit reached. Resetting request flag to NOT STARTED.", extra=d)
                workflow.started = False
                update_workflow(db_key, workflow)
                logger.info("Exiting manager subprocess.", extra=d)

        logger.info(f"Exiting while loop. End of workflow_manager.", extra=d)

    def analysis_retry(self, workflow: WorkflowDBSchema, db_key: str):
        """
        Retry analysis on failures
        """
        # Reset workflow status if max service_retry is not reached
        if self.is_retry_valid(workflow):
            logger.warning(f"Retrying request.{5 - workflow.service_retry}/5 retries left.", extra=d)
            logger.warning(f"Setting feed requested status to False in the DB", extra=d)
            if workflow.feed_requested:
                workflow.service_retry += 1
                workflow.feed_requested = False
            workflow.feed_id_generated = ""
            workflow.started = False

            # reset the current response object
            workflow.response = WorkflowStatusResponseSchema()

            # set to 'registering state' for manager to retry analysis
            workflow.response.workflow_state = State.REGISTERING
            workflow.response.state_progress = "100%"

            update_workflow(db_key, workflow)
            if workflow.service_retry >= 5: logger.warning(Warnings.max_analysis_retry.value, extra=d)
            workflow = retrieve_workflow(db_key)
        return workflow

    def is_retry_valid(self, workflow: WorkflowDBSchema) -> bool:
        """
        Check and return True if the following conditions are met:
          1) no. of retries is < 5
          2) workflow is in failed status
          3) workflow is in Analyzing state
          4) feed is generated (by workflow manager) matches feed is found (by status manager)
        """
        return (workflow.service_retry < 5
                and not workflow.response.status
                and workflow.response.workflow_state == State.ANALYZING
                and workflow.feed_id_generated == workflow.response.feed_id)

    def update_status(self, request: WorkflowRequestSchema):
        """
        Trigger an update status in
        a separate python process
        """
        d_data = request_to_dict(request)
        str_data = json.dumps(d_data)
        status_mgr_subprocess = Subprocess("app/controllers/subprocesses/status.py", str_data)
        proc_count = status_mgr_subprocess.get_process_count()
        logger.info(f"{proc_count} subprocess of status manager running on the system.", extra=d)
        if proc_count > 0:
            logger.info(f"No new status subprocess started.", extra=d)
            return
        d_cmd = ["python", "app/controllers/subprocesses/status.py", "--data", str_data]
        pretty_cmd = pprint.pformat(d_cmd)
        time.sleep(2)
        logger.debug(f"New status subprocess started with command: {pretty_cmd}", extra=d)
        process = subprocess.Popen(d_cmd)

    def pfdcm_do(self, verb: str, then_args: dict, request: WorkflowRequestSchema, url: str):
        """
        A reusable method to either retrieve, push or register dicoms using pfdcm
        by running the threaded API of `pfdcm`
        """
        then_args = json.dumps(then_args, separators=(',', ':'))
        pfdcm_dicom_api = f'{url}/PACS/thread/pypx/'
        headers = {'Content-Type': 'application/json', 'accept': 'application/json'}
        body = {
            "PACSservice": {
                "value": request.pfdcm_info.PACS_service
            },
            "listenerService": {
                "value": "default"
            },
            "PACSdirective": {
                "AccessionNumber": request.PACS_directive.AccessionNumber,
                "PatientID": request.PACS_directive.PatientID,
                "PatientName": request.PACS_directive.PatientName,
                "PatientBirthDate": request.PACS_directive.PatientBirthDate,
                "PatientAge": request.PACS_directive.PatientAge,
                "PatientSex": request.PACS_directive.PatientSex,
                "StudyDate": request.PACS_directive.StudyDate,
                "StudyDescription": request.PACS_directive.StudyDescription,
                "StudyInstanceUID": request.PACS_directive.StudyInstanceUID,
                "Modality": request.PACS_directive.Modality,
                "ModalitiesInStudy": request.PACS_directive.ModalitiesInStudy,
                "PerformedStationAETitle": request.PACS_directive.PerformedStationAETitle,
                "NumberOfSeriesRelatedInstances": request.PACS_directive.NumberOfSeriesRelatedInstances,
                "InstanceNumber": request.PACS_directive.InstanceNumber,
                "SeriesDate": request.PACS_directive.SeriesDate,
                "SeriesDescription": request.PACS_directive.SeriesDescription,
                "SeriesInstanceUID": request.PACS_directive.SeriesInstanceUID,
                "ProtocolName": request.PACS_directive.ProtocolName,
                "AcquisitionProtocolDescription": request.PACS_directive.AcquisitionProtocolDescription,
                "AcquisitionProtocolName": request.PACS_directive.AcquisitionProtocolName,
                "withFeedBack": True,
                "then": verb,
                "thenArgs": then_args,
                "dblogbasepath": '/home/dicom/log',
                "json_response": False
            }
        }
        pretty_json = pprint.pformat(body)
        logger.debug(f"POSTing the below request at {pfdcm_dicom_api} to {verb}: {pretty_json}", extra=d)
        response = requests.post(pfdcm_dicom_api, json=body, headers=headers)
        logger.debug(f'Execution time to request {verb}:{response.elapsed.total_seconds()} seconds', extra=d)

    def do_pfdcm_retrieve(self, dicom: WorkflowRequestSchema, pfdcm_url: str):
        """
        Retrieve PACS using pfdcm
        """
        retrieve_args = {}
        self.pfdcm_do("retrieve", retrieve_args, dicom, pfdcm_url)


    def do_cube_create_feed(self, request: WorkflowRequestSchema, cube_url: str, retries: int) -> dict:
        """
        Create a new feed in `CUBE` if not already present
        """
        pacs_search_params = dict((k, v) for k, v in request.PACS_directive.__dict__.items())
        pacs_search_params["pacs_identifier"] = request.pfdcm_info.PACS_service
        client = do_cube_create_user(cube_url,
                                     request.cube_user_info.username,
                                     request.cube_user_info.password)
        logger.debug(f"Created client details {client}", extra=d)

        logger.debug(f"Fetching PACS details for {pacs_search_params}", extra=d)
        pacs_details = {}
        try:
            pacs_details = client.getPACSdetails(pacs_search_params)
        except Exception as ex:
            logger.info(f"Error receiving PACS details: {ex}", extra=d)
            raise Exception(f"Error receiving PACS details: {ex}")

        feed_name = substitute_dicom_tags(request.workflow_info.feed_name, pacs_details)
        logger.info(f"Fetching data path..", extra=d)
        data_path = client.getSwiftPath(pacs_search_params)
        logger.debug(f"Received data path: {data_path}", extra=d)
        if retries > 0:
            feed_name = feed_name + f"-retry#{retries}"
        feed_name = self.shorten(feed_name)

        # Get plugin Id
        plugin_search_params = {"name": "pl-dircopy"}
        plugin_id = client.getPluginId(plugin_search_params)

        logger.info(f"Creating a new feed with feed name {feed_name}", extra=d)

        # create a feed
        feed_params = {'title': feed_name, 'dir': data_path}
        feed_response = client.createFeed(plugin_id, feed_params)
        return {"feed_id": feed_response["feed_id"], "pl_inst_id": feed_response["id"]}

    def do_cube_start_analysis(self, previous_id: str, request: WorkflowRequestSchema, cube_url: str):
        """
        Create a new node (plugin instance) on an existing feed in `CUBE`
        """
        client = do_cube_create_user(cube_url,
                                     request.cube_user_info.username,
                                     request.cube_user_info.password)
        if request.workflow_info.plugin_name:
            self.__run_plugin_instance(previous_id, request, client)
        if request.workflow_info.pipeline_name:
            self.__run_pipeline_instance(previous_id, request, client)

    def shorten(self, s, width=100, placeholder='[...]'):
        """
        Validate a given feed name for size = 100 chars
        if size exceeds, trim the name and add a suffix placeholder
        """
        return s[:width] if len(s) <= width else s[:width - len(placeholder)] + placeholder

    def __run_plugin_instance(self, previous_id: str, request: WorkflowRequestSchema, client: PythonChrisClient):
        """
        Run a plugin instance on an existing (previous) plugin instance ID in CUBE
        """
        # search for plugin
        plugin_search_params = {"name": request.workflow_info.plugin_name,
                                "version": request.workflow_info.plugin_version}
        logger.info(f"Adding plugin: {plugin_search_params} to pl_inst: {previous_id}", extra=d)
        plugin_id = client.getPluginId(plugin_search_params)

        # convert CLI params from string to a JSON dictionary
        feed_params = self.str_to_param_dict(request.workflow_info.plugin_params)
        feed_params["previous_id"] = previous_id
        logger.debug(f"Creating new analysis with plugin: {plugin_search_params}  and parameters: {feed_params}",
                     extra=d)
        feed_resp = client.createFeed(plugin_id, feed_params)

    def __run_pipeline_instance(self, previous_id: str, request: WorkflowRequestSchema, client: PythonChrisClient):
        """
        Run a workflow instance on an existing (previous) plugin instance ID in CUBE
        """
        # search for pipeline
        pipeline_search_params = {"name": request.workflow_info.pipeline_name}
        logger.info(f"Adding pipeline: {pipeline_search_params} to pl_inst: {previous_id}", extra=d)
        pipeline_id = client.getPipelineId(pipeline_search_params)
        pipeline_params = {"previous_plugin_inst_id": previous_id, "name": request.workflow_info.pipeline_name}
        logger.debug(f"Creating new analysis with pipeline: {pipeline_search_params}.",
                     extra=d)
        feed_resp = client.createWorkflow(str(pipeline_id), pipeline_params)

    def str_to_param_dict(self, params: str) -> dict:
        """
        Convert CLI arguments passed as string to a dictionary of parameters
        """
        d_params = {}
        params_text = params.strip()
        params_dict = params_text.split('--')

        for param in params_dict:
            if param == "":
                continue
            param = param.strip()
            items = param.split(' ', 1)
            if len(items) == 1:
                d_params[items[0]] = True
            else:
                d_params[items[0]] = items[1]

        return d_params


if __name__ == "__main__":
    """
    Main entry point of this script
    """
    parser = define_parameters()
    args = parser.parse_args()
    workflow_manager = WorkflowManager(args)
    workflow_manager.run()


