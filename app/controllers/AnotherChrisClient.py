### aiochris ChRIS Client Implementation ###
import asyncio
from chris import ChrisClient as cClient
from controllers.ChrisClient import ChrisClient

class AIOChrisClient(ChrisClient):

    async def __init__(self,url: str, username: str, password: str):
        self.cl = await cClient.from_login(
                  username=username,
                  password=password,
                  url=url
        )
        
    async def getClient(params:dict):
        return self.cl
        
    
    async def getPluginId(searchParams:dict):
        plugin_id = await self.cl.search_plugins(searchParams)['data'][0]['id']
        return plugin_id
        
    
    async def getSwiftPath(searchParams:dict):
        pass
        
   
    async def createFeed(params:dict):
        pass
        
    
    async def getPipelineId(searchParams:dict):
        pass
        
    
    async def createWorkflow(params:dict):
        pass 
    
    async def getFeed(self, searchParams: dict):
        response = self.cl.get_feeds(searchParams)
        return response
