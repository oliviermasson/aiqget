import doGRAPHQL
import userio

class getEseriesInformation:

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
            userio.message("Retrieve E-Series Informations for S/N " + serialnumber + "...")
            if self.debug >= 3:
                userio.message("with URL : " + self.url )
            query="""
            query Systems($systemKey: [SystemKey!]) {
                systems(systemKey: $systemKey) {
                    totalCount
                    cursor
                    systems {
                    hostName
                    serialNumber
                    osVersion
                    hardwareModel {
                        name
                        endOfAvailability
                        endOfSupport
                    }
                    platformType
                    site {
                        name
                    }
                    systemShipmentDate
                    contract {
                        expiryDate
                    }
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
                systemShipmentDate=self.response['data']['systems']['systems'][0]['systemShipmentDate']
                if systemShipmentDate:
                    from datetime import datetime
                    from dateutil import relativedelta
                    d1 = datetime.strptime(systemShipmentDate, "%Y-%m-%dT%H:%M:%S.%fZ")
                    d2 = datetime.now()
                    delta = relativedelta.relativedelta(d2, d1)
                    AgeInYears=delta.years
                else:
                    AgeInYears='n/a'
                self.aggrEInformation[serialnumber]={'Site_Name':self.response['data']['systems']['systems'][0]['site']['name'],
                                                    'AgeInYears':AgeInYears}                
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
        self.aggrEInformation={}
        
        return self.proceedSerialList(self.serialnumbers,headers)

