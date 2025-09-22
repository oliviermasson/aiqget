import doREST
import re
import userio

class getCapacity:

    def __init__(self,url,access_token,serialnumbers,clusterviewmode,**kwargs):
        self.result=None
        self.reason=None
        self.stdout=[]
        self.stderr=[]
        self.url=url
        self.access_Token=access_token
        self.serialnumbers=serialnumbers
        self.debug=False
        self.clusterviewmode=clusterviewmode

        self.apibase=self.__class__.__name__
        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        else:
            self.apicaller=''
        localapi='->'.join([self.apicaller,self.apibase])
        
        self.api='/v1/capacity2/detail?level=system&serialNumbers='

        if 'debug' in kwargs.keys():
            self.debug=kwargs['debug']

        return
    
    def showDebug(self):
        userio.debug(self)
    
    def proceedSerialList(self,serialnumberslist,headers):
    #* work all serials at once
        serials = ','.join(serialnumberslist)
        api=self.api + serials
        userio.message("Retrieve Node information for S/N " + serials + "...")
        if self.debug >= 3:
            userio.message("with URL : " + self.url + api)
        rest=doREST.doREST(self.url,'get',api,debug=self.debug,headers=headers)
        if rest.result == 200:
            self.result=0
            self.response=rest.response
            if self.debug & 4:
                self.showDebug()
            for serialIndex in range(len(self.response['results']['systems'])):
                if self.clusterviewmode:
                    self.aggrNode[self.response['results']['systems'][serialIndex]['serialNumber']]={'Release':self.response['results']['systems'][serialIndex]['osVersion'],
                                                                                                'HostName':self.response['results']['systems'][serialIndex]['hostName'],
                                                                                                'ClusterName':self.response['results']['systems'][serialIndex]['clusterName'],
                                                                                                'AgeInYears':self.response['results']['systems'][serialIndex]['systemAgeInYears']}
                else:
                    self.aggrNode[self.response['results']['systems'][serialIndex]['serialNumber']]={'Release':self.response['results']['systems'][serialIndex]['osVersion'],
                                                                                                'HostName':self.response['results']['systems'][serialIndex]['hostName'],
                                                                                                'ClusterName':self.response['results']['systems'][serialIndex]['clusterName'],
                                                                                                'UsedTB':self.response['results']['systems'][serialIndex]['systemUsedCapacity'],
                                                                                                'AvailTB':self.response['results']['systems'][serialIndex]['systemUnusedCapacity'],
                                                                                                'Used%':self.response['results']['systems'][serialIndex]['currentSystemCapacityUtilization'],
                                                                                                'AgeInYears':self.response['results']['systems'][serialIndex]['systemAgeInYears']}
            return(True)
        else:
            self.result=1
            self.reason=rest.reason
            self.stdout=rest.stdout
            self.stderr=rest.stderr
            if self.debug & 4:
                self.showDebug()
            return(False)
            
    def go(self,**kwargs):

        headers = {'content-type': "application/json",
           'accept': "application/json"}
        headers['AuthorizationToken']=self.access_Token

        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        localapi='->'.join([self.apicaller,self.apibase + ".go"])
        self.aggrNode={}

        if len(self.serialnumbers) <= 50:
            #* work all serials at once
            return self.proceedSerialList(self.serialnumbers,headers)
        else:    
            #* too many serials, split them up
            chunk_size = 50
            for i in range(0, len(self.serialnumbers), chunk_size):
                chunk = self.serialnumbers[i:i + chunk_size]
                if not self.proceedSerialList(chunk, headers):
                    return False  # Arrêter en cas d'échec
            
            return True
        
