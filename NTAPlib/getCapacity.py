import doREST
import re
import userio

class getCapacity:

    def __init__(self,url,access_token,serialnumbers,**kwargs):
        self.result=None
        self.reason=None
        self.stdout=[]
        self.stderr=[]
        self.url=url
        self.access_Token=access_token
        self.serialnumbers=serialnumbers
        self.debug=False

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

    def go(self,**kwargs):

        headers = {'content-type': "application/json",
           'accept': "application/json"}
        headers['AuthorizationToken']=self.access_Token

        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        localapi='->'.join([self.apicaller,self.apibase + ".go"])
        self.aggrCapacity={}

        #* work all serials at once
        serials = ','.join(self.serialnumbers)
        api=self.api + serials
        if self.debug & 1:
            userio.message("Retrieve Capacity information for S/N " + serials + "...")
        if self.debug >= 3:
            userio.message("with URL : " + self.url + api)
        rest=doREST.doREST(self.url,'get',api,debug=self.debug,headers=headers)
        if rest.result == 200:
            self.result=0
            self.response=rest.response
            if self.debug & 4:
                self.showDebug()
            for serialIndex in range(len(self.response['results']['systems'])):
                self.aggrCapacity[self.response['results']['systems'][serialIndex]['serialNumber']]={'Release':self.response['results']['systems'][serialIndex]['osVersion'],
                                                                                                    'HostName':self.response['results']['systems'][serialIndex]['hostName'],
                                                                                                    'ClusterName':self.response['results']['systems'][serialIndex]['clusterName'],
                                                                                                    'CapacityUsed%':self.response['results']['systems'][serialIndex]['currentSystemCapacityUtilization'],
                                                                                                    'UsedTB':self.response['results']['systems'][serialIndex]['systemUsedCapacity'],
                                                                                                    'AvailTB':self.response['results']['systems'][serialIndex]['systemUnusedCapacity']}
            return(True)
        else:
            self.result=1
            self.reason=rest.reason
            self.stdout=rest.stdout
            self.stderr=rest.stderr
            if self.debug & 4:
                self.showDebug()
            return(False)
        

        #* work one serial at a time
        """ for serialnumber in self.serialnumbers:
            api=self.api + serialnumber
            if self.debug & 1:
                userio.message("Retrieve Capacity information for S/N " + serialnumber + "...")
            if self.debug >= 3:
                userio.message("with URL : " + self.url + api)
            rest=doREST.doREST(self.url,'get',api,debug=self.debug,headers=headers)
            if rest.result == 200:
                self.result=0
                self.response=rest.response
                if self.debug & 4:
                    self.showDebug()
                self.aggrCapacity[self.response['results']['systems'][0]['serialNumber']]={'release':self.response['results']['systems'][0]['osVersion'],
                                                                                                     'hostName':self.response['results']['systems'][0]['hostName'],
                                                                                                     'clusterName':self.response['results']['systems'][0]['clusterName'],
                                                                                                     'CapacityUsed%':str(self.response['results']['systems'][0]['currentSystemCapacityUtilization'])+"%",
                                                                                                     'availTB':self.response['results']['systems'][0]['systemUnusedCapacity']}
            else:
                self.result=1
                self.reason=rest.reason
                self.stdout=rest.stdout
                self.stderr=rest.stderr
                if self.debug & 4:
                    self.showDebug()
                return(False)
        return(True) """
        
