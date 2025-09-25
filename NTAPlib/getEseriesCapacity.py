import doGRAPHQL
import userio

class getEseriesCapacity:

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

        if 'debug' in kwargs.keys():
            self.debug=kwargs['debug']

        return
    
    def showDebug(self):
        userio.debug(self)
    
    def proceedSerialList(self,serialnumberslist,headers):
    #* work all serials at once
        for serialnumber in serialnumberslist:
            userio.message("Retrieve E-Series Capacity information for S/N " + serialnumber + "...")
            if self.debug >= 3:
                userio.message("with URL : " + self.url )
            query="""
            query Summary($systemKey: [SystemKey!]) {
                SANtricitySystemCapacity(systemKey: $systemKey) {
                    totalKiB
                    unconfiguredKiB
                    configured {
                    allocatedKiB
                    freeKiB
                    }
                }
            }
            """
            
            variables = {
                "systemKey": [
                    {
                    "serialNumber": serialnumber,
                    "systemId": serialnumber
                    }
                ]
            }
            
            rest=doGRAPHQL.doGraphQL(self.url,query=query,variables=variables,debug=self.debug,headers=headers)
            if rest.result == 200:
                self.result=0
                self.response=rest.response
                if self.debug & 4:
                    self.showDebug()
                self.aggrECapacity[serialnumber]={'TotalTB':round(int(self.response['data']['SANtricitySystemCapacity']['totalKiB'])/1024/1024/1024,2),
                                                        'UsedTB':round(int(self.response['data']['SANtricitySystemCapacity']['configured']['allocatedKiB'])/1024/1024/1024,2),
                                                        'AvailTB':round(int(self.response['data']['SANtricitySystemCapacity']['configured']['freeKiB'])/1024/1024/1024,2),
                                                        'Used%':round(int(self.response['data']['SANtricitySystemCapacity']['configured']['allocatedKiB'])/int(self.response['data']['SANtricitySystemCapacity']['totalKiB'])*100,2)}
                
            else:
                self.result=1
                self.reason=rest.reason
                self.stdout=rest.stdout
                self.stderr=rest.stderr
                if self.debug & 4:
                    self.showDebug()
                return(False)
            
        if self.result>0:
            return(False)
        else:
            return(True)
        
    def go(self,**kwargs):
        headers = {'content-type': "application/json",
           'accept': "application/json"}
        headers['AuthorizationToken']=self.access_Token

        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        localapi='->'.join([self.apicaller,self.apibase + ".go"])
        self.aggrECapacity={}
        
        return self.proceedSerialList(self.serialnumbers,headers)

