#!/usr/bin/env python3
import argparse
import json
import logging
import pprint
import random
from logging.config import dictConfig

import requests

from app import log
from app.controllers.subprocesses.subprocess_helper import Subprocess
from app.controllers.subprocesses.utils import (
    query_to_dict,
    dict_to_hash,
    retrieve_workflow,
    get_cube_url_from_pfdcm,
    substitute_dicom_tags,
    do_cube_create_user,
    retrieve_pfdcm_url,
    update_workflow_response,
    update_status_flag,
)
from app.models.workflow import (
    State,
    WorkflowRequestSchema,
    WorkflowDBSchema,
    WorkflowStatusResponseSchema,
    Error,
)

dictConfig(log.log_config)
logger = logging.getLogger('pflink-logger')
d = {'workername': 'STATUS_MGR', 'log_color': "\33[36m", 'key': ""}


def define_parameters():
    """
    Define the CLI arguments accepted by this manager class
    """
    parser = argparse.ArgumentParser(description='Process arguments passed through CLI')
    parser.add_argument('--data', type=str)
    parser.add_argument('--test', default=False, action='store_true')
    return parser


class StatusManager:
    """
    This module updates the state of a workflow in the DB
    """
    def __init__(self, args):
        """
        Set something here
        """
        self.args = args


    def run(self):
        dict_data = json.loads(self.args.data)
        wf_key = dict_to_hash(dict_data)
        d['key'] = wf_key
        self.update_workflow_status(wf_key, self.args.test)


    def update_workflow_status(self, key: str, test: bool):
        """
        Update the status of a workflow object in the DB
        """
        workflow = retrieve_workflow(key, test)
        # If the status of the workflow is currently being updated by another process
        # Do nothing and exit
        if self.is_status_subprocess_running(workflow):
            return

        logger.info(f"Working on fetching the current status, locking DB flag.", extra=d)
        update_status_flag(key, False, test)

        if test:
            updated_status = self.get_simulated_status(workflow)
        else:
            updated_status = self.get_current_status(workflow.request, workflow.response, workflow.feed_id_generated)

        updated_response = self.update_workflow_progress(updated_status)
        pretty_response = pprint.pformat(workflow.response.__dict__)
        logger.debug(f"Updated response: {pretty_response}.", extra=d)
        logger.info(f"Current status is {workflow.response.workflow_state}.", extra=d)
        update_workflow_response(key, updated_response, test)
        logger.info(f"Finished writing updated status to the DB, releasing lock.", extra=d)
        update_status_flag(key, True, test)


    def update_workflow_progress(self, response: WorkflowStatusResponseSchema):
        """
        Update the overall workflow progress of a workflow from its current
        workflow state.
        """
        MAX_STATE = 4
        index = 0
        for elem in State:
            if response.workflow_state == elem:
                state_progress = int(response.state_progress.replace('%',''))

                response.workflow_progress_perc = min(100, max(response.workflow_progress_perc,
                                                      self.__progress_percent(index,MAX_STATE,state_progress)))
            index += 1
        return response


    def __progress_percent(self,curr_state: int, total_states: int, state_progress: int) -> int:
        """
        Return the percentage of states completed when the total no. of states and
        current state is given.
        """
        progress_percent = round((curr_state/total_states) * 100 + (state_progress/total_states))
        return  progress_percent


    def is_status_subprocess_running(self, workflow: WorkflowDBSchema) -> bool:
        """
        Return true if the following conditions are true:
          1) Workflow is NOT stale
          2) No other subprocess is running with the same name and args
        """

        # get the number of status subprocess running in the background
        status_mgr_subprocess = Subprocess("app/controllers/subprocesses/status.py", self.args.data)
        proc_count = status_mgr_subprocess.get_process_count()
        return not workflow.stale and not proc_count



    def get_current_status(
            self,
            request: WorkflowRequestSchema,
            status: WorkflowStatusResponseSchema,
            feed_id: str,
    ) -> WorkflowStatusResponseSchema:
        """
        Return the status of a workflow in `pflink` by asking `pfdcm` & `cube`. The sequence is as follows:
            1) Ask `pfdcm` about the status of a study
            2) Ask `cube` about the status of the feed created using the study
            3) Serialize both the results to a response schema
            4) Return the response
        """
        pfdcm_resp = self.get_pfdcm_status(request)
        cube_resp = self._get_feed_status(request, feed_id)
        status = self._parse_response(pfdcm_resp, cube_resp, status)
        return status


    def get_pfdcm_status(self, request: WorkflowRequestSchema):
        """
        Get the status of PACS from `pfdcm`
        by running the synchronous API of `pfdcm`
        """
        try:
            pfdcm_url = retrieve_pfdcm_url(request.pfdcm_info.pfdcm_service)
            pfdcm_status_url = f'{pfdcm_url}/PACS/sync/pypx/'
            headers = {'Content-Type': 'application/json', 'accept': 'application/json'}

            pfdcm_body = {
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
                    "then": 'status',
                    "thenArgs": "",
                    "dblogbasepath": request.pfdcm_info.db_log_path,
                    "json_response": True
                }
            }
            pretty_json = pprint.pformat(pfdcm_body)
            logger.debug(f"POSTing the below request at {pfdcm_status_url} to get status: {pretty_json}", extra=d)
            response = requests.post(pfdcm_status_url, json=pfdcm_body, headers=headers)
            logger.debug(f'Execution time to get status:{response.elapsed.total_seconds()} seconds', extra=d)
            d_response = json.loads(response.text)
            d_response["service_name"] = request.pfdcm_info.pfdcm_service
            return d_response
        except Exception as ex:
            logger.error(f"{Error.pfdcm.value}  {str(ex)} for pfdcm_service {request.pfdcm_info.pfdcm_service}",
                         extra=d)
            return {"error": Error.pfdcm.value + f" {str(ex)} for pfdcm_service {request.pfdcm_info.pfdcm_service}"}


    def _get_feed_status(self, request: WorkflowRequestSchema, feed_id: str) -> dict:
        """
        Get the status of a feed inside `CUBE`
        1) Create/get a cube client using user_name
        2) Fetch feed details using the client
        3) Serialize for information
        4) Return a suitable response
        """
        pfdcm_url = retrieve_pfdcm_url(request.pfdcm_info.pfdcm_service)
        cube_url = get_cube_url_from_pfdcm(pfdcm_url, request.pfdcm_info.cube_service)

        # create a client using the username
        cl = do_cube_create_user(cube_url, request.cube_user_info.username, request.cube_user_info.password)
        pacs_search_params = dict((k, v) for k, v in request.PACS_directive.__dict__.items())
        pacs_search_params["pacs_identifier"] = request.pfdcm_info.PACS_service
        register_count = cl.getPACSfilesCount(pacs_search_params)
        logger.info(f"Registered files are: {register_count}", extra=d)

        if feed_id == "":
            return {"register_count": register_count}
        try:
            # substitute dicom values for dicom tags present in feed name
            requested_feed_name = request.workflow_info.feed_name
            pacs_details = cl.getPACSdetails(pacs_search_params)
            feed_name = substitute_dicom_tags(requested_feed_name, pacs_details)

            # search for feed
            logger.debug(f"Request CUBE at {cube_url} for feed id: {feed_id} and feed name: {feed_name}", extra=d)
            resp = cl.getFeed({"id": feed_id})
            pretty_response = pprint.pformat(resp)
            logger.debug(f"Response from CUBE : {pretty_response}", extra=d)
            resp["register_count"] = register_count

            # if cancelled or errored jobs, recursively figure out the list of
            # errored jobs
            if resp.get("errored_jobs") or resp.get("cancelled_jobs"):
                l_inst_resp = cl.getPluginInstances({"feed_id": feed_id})
                l_error = [d_instance['plugin_name'] for d_instance in l_inst_resp['data']
                           if d_instance['status']=='finishedWithError' or d_instance['status'] == 'cancelled']
                resp["errored_plugins"] = str(l_error)

            return resp
        except Exception as ex:
            logger.error(f"{Error.cube.value} {str(ex)}", extra=d)
            return {"error": Error.cube.value + str(ex)}


    def get_analysis_status(self, response: dict) -> dict:
        """
        Get details about an analysis running on the given feed
        """
        analysis_details = {}

        created = response['created_jobs']
        waiting = response['waiting_jobs']
        scheduled = response['scheduled_jobs']
        started = response['started_jobs']
        registering = response['registering_jobs']
        finished = response['finished_jobs']
        errored = response['errored_jobs']
        cancelled = response['cancelled_jobs']

        total = created + waiting + scheduled + started + registering + finished + errored + cancelled

        if total > 1:
            feed_progress = round((finished / total) * 100)
            analysis_details['progress'] = str(feed_progress) + "%"

            if errored > 0 or cancelled > 0:
                analysis_details["error"] = f"{(errored + cancelled)} job(s) failed : {response['errored_plugins']}"
            if feed_progress == 100:
                analysis_details["state"] = State.COMPLETED
            else:
                analysis_details["state"] = State.ANALYZING

        return analysis_details


    def _parse_response(
            self,
            pfdcm_response: dict,
            cube_response: dict,
            status: WorkflowStatusResponseSchema,
    ) -> WorkflowStatusResponseSchema:
        """
        Parse JSON object for workflow status response
        """
        # status = WorkflowStatusResponseSchema()

        pfdcm_has_error = pfdcm_response.get("error")
        cube_has_error = cube_response.get("error")
        if pfdcm_has_error:
            status.status = False
            status.error = pfdcm_response["error"]
            return status
        valid = pfdcm_response.get('pypx')
        if not valid:
            status.status = False
            status.error = Error.PACS.value + f" {pfdcm_response['message']} for pfdcm_service" \
                                              f" {pfdcm_response['service_name']}"
            return status

        study = pfdcm_response['pypx']['then']['00-status']['study']
        file_count = 0
        for l_series in pfdcm_response['pypx']['data']:
            for series in l_series["series"]:
                file_count += int(series["NumberOfSeriesRelatedInstances"]["value"])

        logger.info(f"Total number of files in this request: {file_count}.", extra=d)

        if study:
            total_images = file_count
            total_registered = cube_response["register_count"]
            total_reg_perc = round((total_registered / total_images) * 100)
            status.workflow_state = State.REGISTERING
            status.state_progress = str(total_reg_perc) + "%"
        else:
            status.error = Error.study.value
            status.status = False
            return status

        if cube_has_error:
            status.status = False
            status.error = cube_response["error"]
            return status

        if cube_response.get('id'):
            status.workflow_state = State.ANALYZING
            status.feed_name = cube_response['name']
            status.feed_id = cube_response['id']
            status.state_progress = "0%"

            # check if analysis is scheduled
            analysis = self.get_analysis_status(cube_response)
            if analysis:
                analysis_has_error = analysis.get("error")
                status.workflow_state = analysis["state"]
                status.state_progress = analysis["progress"]
                if analysis_has_error:
                    status.error = analysis["error"]
                    status.status = False
                    return status

        return status


    def get_simulated_status(self, workflow: WorkflowDBSchema) -> WorkflowStatusResponseSchema:
        """
        Run a simulation of workflow progress and return an updated status
        """
        MAX_N = 9999
        PROGRESS_JUMP = 25
        current_status = workflow.response

        match current_status.workflow_state:

            case State.INITIALIZING:
                current_status.workflow_state = State.REGISTERING
                current_status.state_progress = "25%"

            case State.REGISTERING:
                progress = self.__get_progress_from_text(current_status.state_progress)
                if progress >= 100:
                    current_status.workflow_state = State.ANALYZING
                    current_status.state_progress = '100%'
                    current_status.feed_id = random.randint(0, MAX_N)
                    d_directive = query_to_dict(workflow.request)['PACS_directive']
                    current_status.feed_name = substitute_dicom_tags(workflow.request.workflow_info.feed_name, d_directive)
                else:
                    progress += PROGRESS_JUMP
                    current_status.state_progress = str(progress) + '%'

            case State.ANALYZING:
                progress = self.__get_progress_from_text(current_status.state_progress)
                if progress >= 100:
                    current_status.workflow_state = State.COMPLETED
                else:
                    progress += PROGRESS_JUMP
                    current_status.state_progress = str(progress) + '%'

        return current_status


    def __get_progress_from_text(self, progress: str):
        """
        Convert progress percentage defined in text to integer
        """
        progress = progress.replace('%', '')
        return int(progress)


if __name__ == "__main__":
    """
    Main entry point
    """
    parser = define_parameters()
    args = parser.parse_args()
    status_manager = StatusManager(args)
    status_manager.run()
