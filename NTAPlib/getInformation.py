import doREST
import re
import userio

class getInformation:

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
        
        self.api='/v2/system/details/level/serial_numbers/id/'

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
        self.aggrInformation={}

        #* work all serials at once
        serials = ','.join(self.serialnumbers)
        api=self.api + serials
        if self.debug & 1:
            userio.message("Retrieve Information for S/N " + serials + "...")
        if self.debug >= 3:
            userio.message("with URL : " + self.url + api)
        rest=doREST.doREST(self.url,'get',api,debug=self.debug,headers=headers)
        if rest.result == 200:
            self.result=0
            self.response=rest.response
            if self.debug & 4:
                self.showDebug()
            for serialIndex in range(len(self.response['results'])):
                self.aggrInformation[self.response['results'][serialIndex]['serial_number']]={'site_name':self.response['results'][serialIndex]['site_name'],
                                                                                       'model':self.response['results'][serialIndex]['model']}
            return(True)
        else:
            self.result=1
            self.reason=rest.reason
            self.stdout=rest.stdout
            self.stderr=rest.stderr
            if self.debug & 4:
                self.showDebug()
            return(False)
        
