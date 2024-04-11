import argparse
import json
import logging
import time
from logging.config import dictConfig
from typing import Final
import requests
from typing import List
from app import log
from app.controllers.subprocesses.subprocess_helper import Subprocess
from app.controllers.subprocesses.utils import (
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
d = {'workername': 'WORKFLOW_MGR', 'key': "", 'log_color': "\33[33m"}


def define_parameters():
    """
    Define CLI parameters for this module here
    """
    parser = argparse.ArgumentParser(description='Process arguments')
    parser.add_argument('--data', type=str)
    parser.add_argument('--test', default=False, action='store_true')
    return parser


def shorten(s, width=100, placeholder='[...]'):
    """
    Validate a given feed name for size = 100 chars
    if size exceeds, trim the name and add a suffix placeholder
    """
    return s[:width] if len(s) <= width else s[:width - len(placeholder)] + placeholder


def str_to_param_dict(params: str) -> dict:
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


class WorkflowError(Exception):
    def __init__(self, message, errors):
        # Call the base class constructor with the parameters it needs
        super(WorkflowError, self).__init__(message)

        # Now for your custom code...
        self.errors = errors


class WorkflowManager:
    """
    This module manages different states of a workflow by constantly checking the status of a workflow in the DB.
    """

    def __init__(self, args):
        """
        Initialize class variables
        """
        self.args = args
        self.__client = None
        self.__workflow = None
        self.__request = None
        self.__pfdcm_URL = ""

    def run(self):
        d_data = json.loads(self.args.data)
        key = dict_to_hash(d_data)
        d['key'] = key
        self.fetch_and_load(key, self.args.test)
        self.manage_workflow(key, self.args.test)
        response = self.__workflow.response
        logger.info(f"Workflow manager exited with status {response.status} and\
                        current workflow state as {response.workflow_state}", extra=d)

    def fetch_and_load(self, db_key: str, test: bool):
        """
        Retrieve data from the DB using the appropriate key and database type.

        The first thing this method does is to retrieve the current data related to db_key from the DB.
        The data/workflow record contains all kinds of information related to a workflow i.e.
            1) Original request sent to create  a new workflow
            2) The most recent updated status of the workflow that can be sent to a client in response
            3) Some system flags to manage both the subprocess: 1) workflow_manager 2) status_manager
            4) Some data relevant to the initial creation of a record in the DB: 1) creation date 2) unique id
        """
        self.__workflow = retrieve_workflow(db_key, test)
        self.__request = self.__workflow.request
        self.__pfdcm_URL = retrieve_pfdcm_url(self.__request.pfdcm_info.pfdcm_service)
        cube_url = get_cube_url_from_pfdcm(self.__pfdcm_URL, self.__request.pfdcm_info.cube_service)
        self.__client = do_cube_create_user(cube_url,
                                            self.__request.cube_user_info.username,
                                            self.__request.cube_user_info.password)

    def manage_workflow(self, db_key: str, test: bool):
        """
        The purpose of this method is to manage the workflow request sent by a client to `pflink`.

        This method runs a loop with certain terminating conditions is started that can do the following tasks:
            1) Based on the current STATE, start (or wait for*) the next task.
            2) Start a new status_manager subprocess and wait for N seconds
            3) Fetch the current STATE from the DB and continue.

        * If the DB is marked as "STALE", it means that a status manager process is currently working on
          updating the DB. In this case, the workflow manager simply waits and does not run any task.
        """
        SLEEP_TIME: Final[int] = 10  # wait time before checking the DB
        max_iter: int = 10  # max number of iterations inside while loop
        proceed: bool = True  # flag to control while loop

        while proceed and max_iter > 0:
            logger.info(f"Current workflow state is {self.__workflow.response.workflow_state}", extra=d)

            # if DB is not being currently updated
            if self.__workflow.stale:
                match self.__workflow.response.workflow_state:
                    # request a retrieve
                    case State.INITIALIZING:
                        self.register_pacsfiles()
                    # create an analysis
                    case State.REGISTERING:
                        self.create_analysis(db_key)
                    # check on analysis and retry if needs be
                    case State.ANALYZING:
                        proceed = self.retry_analysis(db_key)
                    # do nothing and exit
                    case State.COMPLETED:
                        return
            # request for status update, sleep, and get the latest from DB
            self.__workflow = self.update_and_wait(SLEEP_TIME, db_key, test)
            max_iter -= 1

    def create_analysis(self, key: str):
        """
        A method to create a new analysis in a CUBE instance. This is a multistep process,
        and requires multiple calls to CUBE's API using a python-chris client.
        The following tasks are needed to be done in order to create a new analysis in CUBE.
            1) Create a CUBE client instance using credentials and URL of CUBE
            2) Search for the plugin `pl-dircopy` in CUBE
            3) Search for the relevant data path containing the required data
            4) Create a new `pl-dircopy` instance in CUBE on the data path
            5) Search for required plugin or pipeline inside CUBE
            6) Create a new instance of the plugin or pipeline with the previous `dircopy` instance
        """
        # if PACS files registering is in progress or feed already requested, do nothing and exit
        if not self.__workflow.response.state_progress == "100%" and self.__workflow.feed_requested:
            return

        logger.info(f"Creating new analysis.", extra=d)
        try:
            dircopy_id = self.get_plugin_id('pl-dircopy')
            data_path = self.get_data_path(self.__request)
            feed_name = self.get_feed_name()
            feed_id, plinst_id = self.create_new_feed(feed_name, data_path, dircopy_id)
            self.__workflow.feed_id_generated = feed_id
            self.__workflow.feed_requested = True
            self.run_plugin_or_pipeline_instance(plinst_id)
        except WorkflowError as er:
            logger.error(f"{er}, error: {er.errors}", extra=d)
            self.__workflow.response.error = f"{er}:{er.errors}"
            self.__workflow.response.status = False
        finally:
            update_workflow(key, self.__workflow)

    def get_feed_name(self) -> str:
        """
        Get feed name to be used to create a new feed in CUBE. This includes the following steps:
          1) Get PACS details from CUBE using requested PACS directive
          2) Substitute requested feed name with PACS details
          3) Append retry count if necessary
          4) Shorten feed name if required
        """
        request = self.__request
        pacs_search_params = dict((k, v) for k, v in request.PACS_directive.__dict__.items())
        pacs_search_params["pacs_identifier"] = request.pfdcm_info.PACS_service  # specify "PACS identifier" for CUBE
        try:
            pacs_details = self.__client.getPACSdetails(pacs_search_params)
            feed_name = substitute_dicom_tags(self.__request.workflow_info.feed_name, pacs_details)
            if self.__workflow.service_retry > 0:
                feed_name = feed_name + f"-retry#{self.__workflow.service_retry}"
            feed_name = shorten(feed_name)
            return feed_name
        except WorkflowError as er:
            raise WorkflowError("Feed name could not be created.", er)

    def run_plugin_or_pipeline_instance(self, prev_id: str):
        """
        A method to decide whether to add a new pipeline or plugin instance to an existing
        plugin instance, and run it.
        """
        request = self.__request
        try:
            if request.workflow_info.plugin_name:
                # convert CLI params from string to a JSON dictionary
                plugin_params = str_to_param_dict(request.workflow_info.plugin_params)
                plugin_params["previous_id"] = prev_id
                plugin_id = self.get_plugin_id(request.workflow_info.plugin_name,
                                               request.workflow_info.plugin_version)
                self.run_plugin(plugin_id, prev_id, plugin_params)
            if request.workflow_info.pipeline_name:
                pipeline_id = self.get_pipeline_id(request.workflow_info.pipeline_name)
                self.run_pipeline(pipeline_id, request.workflow_info.pipeline_name, prev_id)
        except WorkflowError as er:
            raise WorkflowError("Analysis could not be run.", er)

    def register_pacsfiles(self):
        """
        This method uses the async API endpoint of `pfdcm` to send a single 'retrieve' request that in
        turn uses `oxidicom` to push and register PACS files to a CUBE instance
        """
        logger.info("Requesting PFDCM to register PACS files.", extra=d)
        request = self.__request
        pfdcm_dicom_api = f'{self.__pfdcm_URL}/PACS/thread/pypx/'
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
                "then": "retrieve",
                "thenArgs": '',
                "dblogbasepath": '/home/dicom/log',
                "json_response": False
            }
        }
        try:
            response = requests.post(pfdcm_dicom_api, json=body, headers=headers)
            return response
        except WorkflowError as er:
            logger.error(er, extra=d)

    def get_plugin_id(self, name: str, version: str = "") -> str:
        """
        Method to search for a particular plugin with its version and return its ID
        """
        plugin_search_params = {"name": name, "version": version}
        logger.info(f"Searching plugin {name}:{version} in CUBE", extra=d)
        try:
            plugin_id: str = self.__client.getPluginId(plugin_search_params)
            return plugin_id
        except Exception as er:
            raise WorkflowError("Plugin could not be found.", er)

    def get_data_path(self, request: WorkflowRequestSchema) -> str:
        """
        Method to get a list of data path from CUBE containing all the files that match the given PACS
        details
        """
        logger.info("Getting PACS data path from CUBE.", extra=d)
        pacs_search_params = dict((k, v) for k, v in request.PACS_directive.__dict__.items())
        pacs_search_params["pacs_identifier"] = request.pfdcm_info.PACS_service  # specify "PACS identifier" for CUBE
        try:
            data_path = self.__client.getSwiftPath(pacs_search_params)
            return data_path
        except WorkflowError as er:
            raise WorkflowError("Data path could not be found.", er)

    def get_pipeline_id(self, name: str) -> str:
        """Method to search for a particular pipeline and return its ID"""
        pipeline_search_params = {"name": name}
        try:
            pipeline_id = self.__client.getPipelineId(pipeline_search_params)
            return str(pipeline_id)
        except WorkflowError as er:
            raise WorkflowError("Pipeline could not be found.", er)

    def run_pipeline(self, pipeline_id: str, name: str, prev_id: str) -> dict:
        """Run a pipeline instance of a previous plugin instance ID"""
        logger.info(f"Running pipeline on {prev_id}", extra=d)
        pipeline_params = {"previous_plugin_inst_id": prev_id, "name": name}
        try:
            feed_resp: dict = self.__client.createWorkflow(pipeline_id, pipeline_params)
            return feed_resp
        except WorkflowError as er:
            raise WorkflowError("Pipeline could not be run.", er)

    def run_plugin(self, plugin_id: str, prev_id: str, plugin_params: dict) -> str:
        """Run a plugin instance on a previous plugin instance ID"""
        logger.info(f"Running plugin on {prev_id}", extra=d)
        plugin_params["previous_id"] = prev_id
        try:
            resp = self.__client.createFeed(plugin_id, plugin_params)
            return resp
        except WorkflowError as err:
            raise WorkflowError("Plugin could not be run.", err)

    def create_new_feed(self, feed_name: str, data_path: str, dircopy_id: str) -> (str, str):
        """
        Method to create a new feed in CUBE
        """
        logger.info(f"Creating new feed with name: {feed_name}.", extra=d)
        feed_params = {'title': feed_name, 'dir': data_path}
        try:
            feed_response = self.__client.createFeed(dircopy_id, feed_params)
            return feed_response["feed_id"], feed_response["id"]
        except WorkflowError as er:
            raise WorkflowError("Feed could not be created.", er)

    def task_producer(self):
        """
        A method to add new tasks to the task queue
        """
        pass

    def task_consumer(self):
        """
        A method to dequeue and run tasks
        """
        pass

    def update_and_wait(self, sleep: int, db_key: str, test: bool) -> WorkflowDBSchema:
        """
        1) Create a new status manager sub-process to update the DB
        2) sleep for N seconds
        3) retrieve the latest data from the DB
        """
        logger.info("Creating new status manager.", extra=d)
        self.update_status()
        logger.info(f"Sleeping for {sleep} seconds.", extra=d)
        time.sleep(sleep)
        workflow = retrieve_workflow(db_key, test)
        return workflow

    def retry_analysis(self, db_key: str) -> bool:
        """
        Retry analysis on failures
        """
        if not self.is_retry_valid():
            return False

        logger.warning(f"Retrying request.{5 - self.__workflow.service_retry}/5 retries left.", extra=d)
        if self.__workflow.feed_requested:
            logger.warning(f"Setting feed requested status to False in the DB", extra=d)
            self.__workflow.service_retry += 1
            self.__workflow.feed_requested = False
        self.__workflow.feed_id_generated = ""
        self.__workflow.started = False

        # reset the current response object
        self.__workflow.response = WorkflowStatusResponseSchema()

        # set to 'registering state' for manager to retry analysis
        self.__workflow.response.workflow_state = State.REGISTERING
        self.__workflow.response.state_progress = "100%"

        update_workflow(db_key, self.__workflow)
        if self.__workflow.service_retry >= 5: logger.warning(Warnings.max_analysis_retry.value, extra=d)
        return True

    def is_retry_valid(self) -> bool:
        """
        Check and return True if the following conditions are met:
          1) no. of retries is < 5
          2) workflow is in failed status
          3) workflow is in Analyzing state
          4) feed is generated (by workflow manager) matches feed is found (by status manager)
        """
        logger.info(f"Checking if workflow qualifies for retry.", extra=d)
        workflow = self.__workflow
        return (workflow.service_retry < 5
                and not workflow.response.status
                and workflow.response.workflow_state == State.ANALYZING
                and workflow.feed_id_generated == workflow.response.feed_id)

    def update_status(self):
        """Start an update status in a separate python process"""
        status_mgr_subprocess = Subprocess("app/controllers/subprocesses/status.py", self.args.data)
        resp: str = status_mgr_subprocess.run()
        logger.info(resp, extra=d)


def main():
    # parse CLI arguments
    parser = define_parameters()
    args = parser.parse_args()

    # Run an instance of WorkflowManager class with the specified args
    workflow_manager = WorkflowManager(args)
    workflow_manager.run()


if __name__ == "__main__":
    """
    Main entry point of this script
    """
    main()
