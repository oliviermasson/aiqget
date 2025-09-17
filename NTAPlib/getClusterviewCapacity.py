import doREST
import re
import userio

class getClusterviewCapacity:

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
        
        self.api='/v1/clusterview/get-aggregate-summary/'

        if 'debug' in kwargs.keys():
            self.debug=kwargs['debug']

        return
    
    def showDebug(self):
        userio.debug(self)
    
    def proceedSerialList(self,serialnumberslist,headers):
        # work all serials one by one
        for serialnumber in serialnumberslist:
            api=self.api + serialnumber
            if self.debug & 1:
                userio.message("Retrieve Clusterview Capacity information for S/N " + serialnumber + "...")
            if self.debug >= 3:
                userio.message("with URL : " + self.url + api)
            rest=doREST.doREST(self.url,'get',api,debug=self.debug,headers=headers)
            if rest.result == 200:
                self.result=0
                self.response=rest.response
                if self.debug & 4:
                    self.showDebug()
                if len(self.response['data']) > 1:
                    if self.debug & 4:
                        print("More than one aggregate found for S/N " + serialnumber + ", need to exclude root aggregate and summarize all others aggregates")
                    nodeaggr={}
                    nodeaggr={'usable_capacity_tib':0,'used_capacity_tib':0,'available_capacity_tib':0}
                    for aggr in self.response['data']:
                        if 'root' not in aggr['local_tier_name'] and float(aggr['usable_capacity_tib']) > 1:
                            if self.debug & 4:
                                print("  " + aggr['local_tier_name'] + " is a DATA aggr with current usage of %s%%" % (float(aggr['used_data_percent'])))
                            nodeaggr['usable_capacity_tib']+=float(aggr['usable_capacity_tib'])
                            nodeaggr['used_capacity_tib']+=float(aggr['used_capacity_tib'])
                            nodeaggr['available_capacity_tib']+=float(aggr['available_capacity_tib'])
                        else:
                            if self.debug & 4:
                                print("  " + aggr['local_tier_name'] + " is a ROOT aggr, excluded from capacity calculation")
                    nodeaggr['used_data_percent']=round((nodeaggr['used_capacity_tib'] / nodeaggr['usable_capacity_tib']) * 100,2)
                    self.aggrCapacity[serialnumber]={'UsedTB':nodeaggr['used_capacity_tib'],
                                                    'AvailTB':nodeaggr['available_capacity_tib'],
                                                    'TotalTB':nodeaggr['usable_capacity_tib'],
                                                    'CapacityUsed%':nodeaggr['used_data_percent']}
                else:
                    print("No data found for S/N " + serialnumber)
            else:
                self.result=1
                self.reason=rest.reason
                self.stdout=rest.stdout
                self.stderr=rest.stderr
                if self.debug & 4:
                    self.showDebug()
                return(False)
        return(True)
            
    def go(self,**kwargs):

        headers = {'content-type': "application/json",
           'accept': "application/json"}
        headers['AuthorizationToken']=self.access_Token

        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        localapi='->'.join([self.apicaller,self.apibase + ".go"])
        self.aggrCapacity={}

        return self.proceedSerialList(self.serialnumbers,headers)
