### Python Chris Client Implementation ###

from chrisclient import client
from controllers.ChrisClient import ChrisClient

cl = client.Client('http://localhost:8000/api/v1/', 'chris', 'chris1234')

class PythonChrisClient(ChrisClient):


    def getClient(self, params:dict):
        return cl
        

    def getPluginId(self, searchParams:dict):
        plugin_id = cl.get_plugins(searchParams)['data'][0]['id']
        return plugin_id
        

    def getSwiftPath(self, searchParams:dict):
        files = cl.get_pacs_files(searchParams)
        path = files['data'][0]['fname']
        return path
        

    def createFeed(self, plugin_id: str,params: dict):
        response = cl.create_plugin_instance(plugin_id,params)
        return response
        

    def getPipelineId(self, searchParams:dict):
        pipeline_id = cl.get_pipelines(searchParams)['data'][0]['id']
        return pipeline_id
        

    def createWorkflow(self, pipeline_id: str,params: dict):
        response = cl.create_workflow(pipeline_id,params)
        return response
