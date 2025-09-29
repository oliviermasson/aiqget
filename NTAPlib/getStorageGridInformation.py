import doGRAPHQL
import userio

class getStorageGridInformation:

    def __init__(self,url,access_token,serialnumbers,detailSG,**kwargs):
        self.result=None
        self.reason=None
        self.stdout=[]
        self.stderr=[]
        self.url=url
        self.access_Token=access_token
        self.serialnumbers=serialnumbers
        self.detailSG=detailSG
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
            userio.message("Retrieve StorageGrid Informations for S/N " + serialnumber + " and SystemID " + self.detailSG[serialnumber]['SystemID'] + "...")
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
                    productType
                    osType
                    type
                    model
                    ... on StorageGrid {
                        osVersion
                        hostName
                        hardwareModel {
                        name
                        }
                        type
                        osType
                        productType
                        platformType
                        systemShipmentDate
                        customer {
                        name
                        }
                        site {
                        name
                        }
                        storageConfiguration
                        gridName
                        gridId
                        licenseCapacity
                        installedNodeCount
                        gridSites {
                        name
                        siteCapacity {
                            configured {
                            usableKiB
                            usedKiB
                            usedDataKiB
                            usedMetadataKiB
                            reservedMetadataKiB
                            }
                        }
                        }
                        gridCapacity {
                        configured {
                            usableKiB
                            usedKiB
                            usedDataKiB
                            usedMetadataKiB
                            reservedMetadataKiB
                        }
                        }
                    }
                    }
                }
                }
            """
            
            variables = {
                "systemKey": [
                    {
                    "serialNumber": serialnumber,
                    "systemId": self.detailSG[serialnumber]['SystemID']
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
                self.aggrSGInformation[serialnumber]={'Site_Name':self.response['data']['systems']['systems'][0]['site']['name'],
                                                    'HostName':self.response['data']['systems']['systems'][0]['hostName'],
                                                    'AgeInYears':AgeInYears,
                                                    'Model':self.response['data']['systems']['systems'][0]['model'],
                                                    'Release':self.response['data']['systems']['systems'][0]['osVersion'],
                                                    'ClusterName':self.response['data']['systems']['systems'][0]['gridName'],
                                                    'UsedTB':round(int(self.response['data']['systems']['systems'][0]['gridCapacity']['configured']['usedKiB'])/1024/1024/1024,2),
                                                    'AvailTB':round(int(self.response['data']['systems']['systems'][0]['gridCapacity']['configured']['usableKiB'])/1024/1024/1024,2),
                                                    'TotalTB':round(int(self.response['data']['systems']['systems'][0]['gridCapacity']['configured']['usedKiB']+self.response['data']['systems']['systems'][0]['gridCapacity']['configured']['usableKiB'])/1024/1024/1024,2),
                                                    'Used%':round((int(self.response['data']['systems']['systems'][0]['gridCapacity']['configured']['usedKiB'])/int(self.response['data']['systems']['systems'][0]['gridCapacity']['configured']['usedKiB']+self.response['data']['systems']['systems'][0]['gridCapacity']['configured']['usableKiB']))*100,2)}
                for gridsite in self.response['data']['systems']['systems'][0]['gridSites']:
                    self.aggrSGInformation[str(serialnumber)+"_"+str(gridsite['name'])]={'Site_Name':gridsite['name'],
                                                    'UsedTB':round(int(gridsite['siteCapacity']['configured']['usedKiB'])/1024/1024/1024,2),
                                                    'AvailTB':round(int(gridsite['siteCapacity']['configured']['usableKiB'])/1024/1024/1024,2),
                                                    'TotalTB':round(int(gridsite['siteCapacity']['configured']['usedKiB']+gridsite['siteCapacity']['configured']['usableKiB'])/1024/1024/1024,2),
                                                    'Used%':round((int(gridsite['siteCapacity']['configured']['usedKiB'])/int(gridsite['siteCapacity']['configured']['usedKiB']+gridsite['siteCapacity']['configured']['usableKiB']))*100,2),
                                                    'Model':"StorageGRID"}
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
        self.aggrSGInformation={}
        
        return self.proceedSerialList(self.serialnumbers,headers)

