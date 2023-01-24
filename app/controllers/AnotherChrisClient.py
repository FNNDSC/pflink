### aiochris ChRIS Client Implementation ###
import asyncio
from chris import ChrisClient

class AIOChrisClient(ABC):

    async def __int__(self,url: str, username: str, password: str):
        self.cl = await ChrisClient.from_login(
        username=username,
        password=password,
        url=url
        )
        
    async def getClient(params:dict):
        return self.cl
        
    
    async def getPluginId(searchParams:dict):
        pass
        
    
    async def getSwiftPath(searchParams:dict):
        pass
        
   
    async def createFeed(params:dict):
        pass
        
    
    async def getPipelineId(searchParams:dict):
        pass
        
    
    async def createWorkflow(params:dict):
        pass 
