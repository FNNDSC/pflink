### An Abstract Base Class to implement in multiple Chris Clients ###
from abc import ABC, abstractmethod

class ChrisClient(ABC):

    @abstractmethod
    def getClient(params:dict):
        pass
        
    @abstractmethod
    def getPluginId(searchParams:dict):
        pass
        
    @abstractmethod
    def getSwiftPath(searchParams:dict):
        pass
        
    @abstractmethod
    def createFeed(params:dict):
        pass
        
    @abstractmethod
    def getPipelineId(searchParams:dict):
        pass
        
    @abstractmethod
    def createWorkflow(params:dict):
        pass 
