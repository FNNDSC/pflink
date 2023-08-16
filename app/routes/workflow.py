from fastapi import APIRouter
from app.controllers import workflow
from app.models.workflow import (
    WorkflowRequestSchema,
    WorkflowStatusResponseSchema,
    WorkflowSearchSchema,
)
from app.controllers.subprocesses import utils
router = APIRouter()


@router.post(
    "",
    response_description="Workflow response retrieved",
    summary="Create a workflow",
)
async def create_workflow(data: WorkflowRequestSchema) -> WorkflowStatusResponseSchema:
    """
    Get the status of a workflow by POSTing a payload using this API endpoint.
    If it's the first time a client is POSTing a payload, this API creates a new
    entry in the DB and returns a default response.
    """
    response = await workflow.post_workflow(data)
    return response


@router.get("/search", response_description="All workflows retrieved")
async def get_workflows(
    AccessionNumber: str = "",
    PatientID: str = "",
    PatientName: str = "",
    PatientBirthDate: str = "",
    PatientAge: str = "",
    PatientSex: str = "",
    StudyDate: str = "",
    StudyDescription: str = "",
    StudyInstanceUID: str = "",
    Modality: str = "",
    ModalitiesInStudy: str = "",
    PerformedStationAETitle: str = "",
    NumberOfSeriesRelatedInstances: str = "",
    InstanceNumber: str = "",
    SeriesDate: str = "",
    SeriesDescription: str = "",
    SeriesInstanceUID: str = "",
    ProtocolName: str = "",
    AcquisitionProtocolDescription: str = "",
    AcquisitionProtocolName: str = "",
    plugin_name: str = "",
    plugin_version: str = "",
    plugin_params: str = "",
    pipeline_name: str = "",
    cube_username: str = "",
    date: str = "",
):
    """
    Fetch all workflows currently present in the database
    """
    search_params = WorkflowSearchSchema(
    AccessionNumber = AccessionNumber,
    PatientID = PatientID,
    PatientName = PatientName,
    PatientBirthDate = PatientBirthDate,
    PatientAge = PatientAge,
    PatientSex = PatientSex,
    StudyDate = StudyDate,
    StudyDescription = StudyDescription,
    StudyInstanceUID = StudyInstanceUID,
    Modality = Modality,
    ModalitiesInStudy = ModalitiesInStudy,
    PerformedStationAETitle = PerformedStationAETitle,
    NumberOfSeriesRelatedInstances = NumberOfSeriesRelatedInstances,
    InstanceNumber = InstanceNumber,
    SeriesDate = SeriesDate,
    SeriesDescription = SeriesDescription,
    SeriesInstanceUID = SeriesInstanceUID,
    ProtocolName = ProtocolName,
    AcquisitionProtocolDescription = AcquisitionProtocolDescription,
    AcquisitionProtocolName = AcquisitionProtocolName,
    plugin_name = plugin_name,
    plugin_version = plugin_version,
    plugin_params = plugin_params,
    pipeline_name = pipeline_name,
    cube_username = cube_username,
    date = date,
    )
    workflows = workflow.retrieve_workflows(search_params)
    return workflows
    
    
@router.get("", response_description="Workflow retrieved successfully")
async def get_workflow(workflow_key: str):
    """
    Fetch workflow recorded by using hash of a request.
    """
    workflow = utils.retrieve_workflow(workflow_key)
    return workflow



# @router.delete("/list", response_description="All workflows deleted")
# async def delete_workflows():
    """
    Delete all workflow records from the prod database table
    """
#    response = await workflow.delete_workflows()
#    return response

@router.delete("", response_description="Selected workflow deleted successfully")
async def delete_workflow(workflow_key: str):
    """
    Delete a single workflow record from the prod database table
    """
    response = await workflow.delete_workflow(workflow_key)
    return response
