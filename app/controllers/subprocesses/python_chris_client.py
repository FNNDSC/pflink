### Python Chris Client Implementation ###

from chrisclient import client


class PythonChrisClient():

    def __init__(self,url: str, username: str, password: str):
        self.cl = client.Client(url,username,password)

    def getClient(self, params:dict):
        return self.cl

    def getPluginId(self, searchParams:dict):
        response = self.cl.get_plugins(searchParams)
        if response['total'] > 0:
            return response['data'][0]['id']
        raise Exception(f"No plugin found with matching search criteria {searchParams}")

    def getSwiftPath(self, searchParams:dict):
        searchParams["limit"] = 100000
        files = self.cl.get_pacs_files(searchParams)
        l_dir_path = set()
        for file in files['data']:
            filePath = file['fname']
            fileName = filePath.split('/')[-1]
            dirPath = filePath.replace(fileName,'')
            l_dir_path.add(dirPath)
        return ','.join(l_dir_path)
        
    def getPACSdetails(self,searchParams:dict):
        response = self.cl.get_pacs_files(searchParams)
        if response['data']:
            return response['data'][0]
        raise Exception(f"No PACS details with matching search criteria {searchParams}")

    def getPACSfilesCount(self,searchParams:dict):
        response = self.cl.get_pacs_files(searchParams)
        if response:
            return response['total']
        raise Exception(f"No PACS details with matching search criteria {searchParams}")


    def createFeed(self, plugin_id: str,params: dict):
        response = self.cl.create_plugin_instance(plugin_id,params)
        return response

    def getPipelineId(self, searchParams:dict) -> int:
        pipeline_res = self.cl.get_pipelines(searchParams)['data']
        if pipeline_res:
            return pipeline_res[0]['id']
        raise Exception(f"No pipeline found with matching search criteria {searchParams}")

    def createWorkflow(self, pipeline_id: str,params: dict):
        response = self.cl.create_workflow(pipeline_id,params)
        return response
        
    def getFeed(self, searchParams: dict):
        response = self.cl.get_feeds(searchParams)
        if response['total'] > 0:
            return response['data'][0]
        else:
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

    def getPlugins(self):
        response = self.cl.get_plugins()
        return response

    def getPipelines(self):
        response = self.cl.get_pipelines()
        return response

    def getPluginParams(self,pluginId: str):
        response = self.cl.get_plugin_parameters(pluginId)
        return response


