import doREST
import re
import userio

class getClientIDSerialnumbers:

    def __init__(self,url,access_token,clientID,**kwargs):
        self.result=None
        self.reason=None
        self.stdout=[]
        self.stderr=[]
        self.url=url
        self.access_Token=access_token
        self.clientID=clientID
        self.debug=False

        self.apibase=self.__class__.__name__
        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        else:
            self.apicaller=''
        localapi='->'.join([self.apicaller,self.apibase])
        
        self.api='/v1/systemList/aggregate/level/customer/id/' + self.clientID

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
        api=self.api
        userio.message("Retrieve ONTAP serialnumbers for clientID [" + self.clientID + "]...")
        if self.debug >= 3:
            userio.message("with URL : " + self.url + api)
        rest=doREST.doREST(self.url,'get',api,debug=self.debug,headers=headers)
        if rest.result == 200:
            self.result=0
            self.response=rest.response
            self.list=[]
            if self.debug & 4:
                self.showDebug()
            if(len(self.response['results']) == 0):
                userio.message("No results found for clientID [" + self.clientID + "]")
                return(False)
            if(len(self.response['results']) > 1):
                for equipment in self.response['results']:
                    if equipment['platform_type'] in ['ONTAP','ONTAP-SELECT'] and equipment['hostname']:
                        self.list.append(equipment['serial_number'])
                        userio.message("Add serialnumber: [" + equipment['serial_number'] + "] with name: [" + equipment['hostname'] + "] model: [" + equipment['model'] + "] version: [" + equipment['version'] + "]")
                    else:
                        userio.message("Find serialnumber: [" + equipment['serial_number'] + "] with name: [" + equipment['hostname'] + "] plateforme: [" + equipment['platform_type'] + "] model: [" + equipment['model'] + "] version: [" + equipment['version'] + "]")    
                if len(self.list) == 0:
                    userio.message("No ONTAP serialnumbers found for clientID [" + self.clientID + "]")
                    return(False)
            userio.message("\n")
            return(True)
        else:
            self.result=1
            self.reason=rest.reason
            self.stdout=rest.stdout
            self.stderr=rest.stderr
            if self.debug & 4:
                self.showDebug()
            return(False)
        
