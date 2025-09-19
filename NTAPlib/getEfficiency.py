import doREST
import re
import userio

class getEfficiency:

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
        
        self.api='/v1/efficiency/summary/level/serial_numbers/id/'

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
        self.aggrEfficiency={}
        for serialnumber in self.serialnumbers:
            api=self.api + serialnumber
            userio.message("Retrieve Efficiency information for S/N " + serialnumber + "...")
            if self.debug >= 3:
                userio.message("with URL : " + self.url + api)
            rest=doREST.doREST(self.url,'get',api,debug=self.debug,headers=headers)
            if rest.result == 200:
                self.result=0
                self.response=rest.response
                if self.debug & 4:
                    self.showDebug()
                if len(self.response['results']['efficiency']['systems']['system']) > 0:
                    self.aggrEfficiency[self.response['results']['efficiency']['systems']['system'][0]['serial_number']]={'effRatio':str(self.response['results']['efficiency']['systems']['system'][0]['node_overall_efficiency_ratio_without_clone_snapshot'])+":1"}
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
        
