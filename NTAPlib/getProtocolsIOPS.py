import doREST
import re
import userio

class getProtocolsIOPS:

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
        
        self.api='/v1/performance-data/graphs?graphName=node_protocol_iops&startDate='+self.start+'&endDate='+self.end+'&serialNumber='

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
        self.aggrProtoIOPS={}
        for serialnumber in self.serialnumbers:
            api=self.api + serialnumber
            userio.message("Retrieve ONTAP Protocols IOPS information for S/N " + serialnumber + "...")
            if self.debug >= 3:
                userio.message("with URL : " + self.url + api)
            rest=doREST.doREST(self.url,'get',api,debug=self.debug,headers=headers)
            if rest.result == 200:
                self.result=0
                self.response=rest.response
                if self.debug & 4:
                    self.showDebug()
                firstKey=next(iter(self.response['results']['counterData']))
                protocols=self.response['results']['counterData'][firstKey].keys()
                avgProtoIOPS={}
                maxProtoIOPS={}
                for proto in protocols:
                    avgProtoIOPS[proto]=0
                    maxProtoIOPS[proto]=0
                for ProtoTime in self.response['results']['counterData'].keys():
                    for proto in protocols:
                        avgProtoIOPS[proto] += self.response['results']['counterData'][ProtoTime][proto]
                        if self.response['results']['counterData'][ProtoTime][proto] > maxProtoIOPS[proto]:
                            maxProtoIOPS[proto]=self.response['results']['counterData'][ProtoTime][proto]
                avgResults={}
                for proto in protocols:
                    avgProtoIOPS[proto] /= len(self.response['results']['counterData'])
                    avgProtoIOPS[proto] = round(avgProtoIOPS[proto], 2)
                    avg=f'avg_{proto}'
                    max=f'max_{proto}'
                    avgResults[max]=maxProtoIOPS[proto]
                    avgResults[avg]=avgProtoIOPS[proto]
                self.aggrProtoIOPS[self.response['results']['serialNumber']]=avgResults
                    
            else:
                self.result=1
                self.reason=rest.reason
                self.stdout=rest.stdout
                self.stderr=rest.stderr
                if self.debug & 4:
                    self.showDebug()
                return(False)
        return(True)

