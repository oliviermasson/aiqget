import doREST
import re
import userio

class getHeadroom:

    def __init__(self,url,access_token,serialnumbers,start,end,**kwargs):
        self.result=None
        self.reason=None
        self.stdout=[]
        self.stderr=[]
        self.url=url
        self.access_Token=access_token
        self.serialnumbers=serialnumbers
        self.start=start
        self.end=end
        self.debug=False

        self.apibase=self.__class__.__name__
        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        else:
            self.apicaller=''
        localapi='->'.join([self.apicaller,self.apibase])
        
        self.api='/v1/performance-data/graphs?graphName=node_headroom_cpu_utilization&startDate='+self.start+'&endDate='+self.end+'&serialNumber='

        if 'debug' in kwargs.keys():
            self.debug=kwargs['debug']

        if self.debug >= 3:
            userio.message('',service=localapi + ":INIT")

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
        self.aggrHeadroom={}
        for serialnumber in self.serialnumbers:
            api=self.api + serialnumber
            if self.debug & 1:
                userio.message("Retrieve Headroom information for S/N " + serialnumber + "...")
            if self.debug >= 3:
                userio.message("with URL : " + self.url + api)
            rest=doREST.doREST(self.url,'get',api,debug=self.debug,headers=headers)
            if rest.result == 200:
                self.result=0
                self.response=rest.response
                if self.debug & 4:
                    self.showDebug()
                avgCPUheadroom=0
                for CPUTime in self.response['results']['counterData'].keys():
                    avgCPUheadroom += self.response['results']['counterData'][CPUTime]['current_utilization']
                if len(self.response['results']['counterData']) > 0:
                    avgCPUheadroom /= len(self.response['results']['counterData'])
                    avgCPUheadroom = round(avgCPUheadroom, 2)
                else:
                    avgCPUheadroom = 0.0
                self.aggrHeadroom[self.response['results']['serialNumber']]={'avgCPUheadroom%':avgCPUheadroom}
            else:
                self.result=1
                self.reason=rest.reason
                self.stdout=rest.stdout
                self.stderr=rest.stderr
                if self.debug & 4:
                    self.showDebug()
                return(False)
        return(True)

