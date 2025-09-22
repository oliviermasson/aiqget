import doREST
import re
import userio

class getClusterviewCapacity:

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
            userio.message("Retrieve Clusterview Capacity information for S/N " + serialnumber + "...")
            # if serialnumber == '952133001024':
            #     userio.message("Debug for S/N " + serialnumber)
            if self.debug >= 3:
                userio.message("with URL : " + self.url + api)
            rest=doREST.doREST(self.url,'get',api,debug=self.debug,headers=headers)
            if rest.result == 200:
                self.result=0
                self.response=rest.response
                if self.debug >= 3:
                    self.showDebug()
                if 'errors' in self.response:
                    if len(self.response['errors']) > 0:
                        print("Error for S/N " + serialnumber + ": " + str(self.response['errors']))
                        self.aggrCapacity[serialnumber]={'TotalTB':'n/a'}
                        continue
                if len(self.response['data']) > 1:
                    if self.debug >= 1:
                        print("More than one aggregate found for S/N " + serialnumber + ", need to exclude root aggregate and summarize all others aggregates")
                    nodeaggr={}
                    nodeaggr={'usable_capacity_tib':0,'used_capacity_tib':0,'available_capacity_tib':0}
                    for aggr in self.response['data']:
                        try:
                            if ('root' not in aggr['local_tier_name'].lower() and aggr.get('usable_capacity_tib') and float(aggr['usable_capacity_tib']) > 1):
                                if self.debug >= 1:
                                    print("  " + aggr['local_tier_name'] + " is a DATA aggr with current usage of %s%%" % (float(aggr['used_data_percent'])))
                                nodeaggr['usable_capacity_tib']+=float(aggr['usable_capacity_tib'])
                                nodeaggr['used_capacity_tib']+=float(aggr['used_capacity_tib'])
                                nodeaggr['available_capacity_tib']+=float(aggr['available_capacity_tib'])
                            else:
                                if self.debug >= 1:
                                    print("  " + aggr['local_tier_name'] + " excluded from capacity calculation")
                        except (ValueError, TypeError, KeyError):
                            if self.debug >= 1:
                                print(f"  Skipping aggregate {aggr.get('local_tier_name', 'unknown')} - invalid capacity data")
                            continue
                    if nodeaggr['usable_capacity_tib'] > 0:
                        nodeaggr['used_data_percent']=round((nodeaggr['used_capacity_tib'] / nodeaggr['usable_capacity_tib']) * 100,2)
                    else:
                        nodeaggr['used_data_percent']=0
                    if self.clusterviewmode:
                        self.aggrCapacity[serialnumber]={'UsedTB':nodeaggr['used_capacity_tib'],
                                                    'AvailTB':nodeaggr['available_capacity_tib'],
                                                    'TotalTB':nodeaggr['usable_capacity_tib'],
                                                    'Used%':nodeaggr['used_data_percent']}
                    else:
                        self.aggrCapacity[serialnumber]={'TotalTB':nodeaggr['usable_capacity_tib']}
                else:
                    print("No data found for S/N " + serialnumber)
                    self.aggrCapacity[serialnumber]={'TotalTB':'n/a'}
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
