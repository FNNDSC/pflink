### Python Chris Client Implementation ###

from chrisclient import client
from controllers.client.ChrisClient import ChrisClient

class PythonChrisClient(ChrisClient):

    def __init__(self,url: str, username: str, password: str):
        self.cl = client.Client(url,username,password)


    def getClient(self, params:dict):
        return self.cl
        

    def getPluginId(self, searchParams:dict):
        plugin_id = self.cl.get_plugins(searchParams)['data'][0]['id']
        return plugin_id
        

    def getSwiftPath(self, searchParams:dict):
        files = self.cl.get_pacs_files(searchParams)
        filePath = files['data'][0]['fname']
        fileName = filePath.split('/')[-1]
        dirPath = filePath.replace(fileName,'')
        return dirPath
        

    def createFeed(self, plugin_id: str,params: dict):
        response = self.cl.create_plugin_instance(plugin_id,params)
        return response
        

    def getPipelineId(self, searchParams:dict) -> int:
        pipeline_res = self.cl.get_pipelines(searchParams)['data']
        if pipeline_res:
            return pipeline_res[0]['id']
        return -1        

    def createWorkflow(self, pipeline_id: str,params: dict):
        response = self.cl.create_workflow(pipeline_id,params)
        return response
        
    def getFeed(self, searchParams: dict):
        response = self.cl.get_feeds(searchParams)
        return response
        
    def getWorkflow(self, searchParams: dict):
        response = self.cl.get_workflows(searchParams)
        return response
        
    def getWorkflowDetails(self, workflow_id : str):
        response = self.cl.get_workflow_plugin_instances(workflow_id)
        return response
        
    def getPluginInstances(self, searchParams : dict):
        response = self.cl.get_plugin_instances(searchParams)
        return response

