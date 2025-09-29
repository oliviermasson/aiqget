import doREST
import re
import userio
from getClientIDSerialnumbers import getClientIDSerialnumbers


class getClientID:

    def __init__(self,url,access_token,customer_name,**kwargs):
        self.result=None
        self.reason=None
        self.stdout=[]
        self.stderr=[]
        self.url=url
        self.access_Token=access_token
        self.customer_name=customer_name
        self.debug=False

        self.apibase=self.__class__.__name__
        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        else:
            self.apicaller=''
        localapi='->'.join([self.apicaller,self.apibase])
        
        self.api='/v3/search/aggregate?customer=' + self.customer_name

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
        if self.debug & 1:
            userio.message("Retrieve Customer ID for customer [" + self.customer_name + "]...")
        if self.debug >= 3:
            userio.message("with URL : " + self.url + api)
        rest=doREST.doREST(self.url,'get',api,debug=self.debug,headers=headers)
        if rest.result == 200:
            self.result=0
            self.response=rest.response
            if self.debug & 4:
                self.showDebug()
            if len(self.response['results']) == 0:
                userio.message("No results found for customer [" + self.customer_name + "]")
                return(False)
            if len(self.response['results']) > 1:
                userio.message("More than one ClientID for [" + self.customer_name + "]")
                userio.message("Please refine your search customer name to get a correct single ClientID.")
                listclientID=[]
                userio.message("\nList of ClientIDs found for customer [" + self.customer_name + "]")
                userio.message("-------------------------------------------------")
                for client in self.response['results']:
                    userio.message("ClientID: [" + client['name'] + "] with ID: [" + client['id'] + "] and number of equipment: [" + str(client['count']) + "]")
                    listclientID.append(client['id'])
                userio.message("-------------------------------------------------\n")
                mergeall = input("Do you want to merge all these ClientIDs? [y/N] ")
                if re.match('n', mergeall, re.IGNORECASE):
                    return(False) 
                    
            else:
                listclientID=[]
                listclientID.append(self.response['results'][0]['id'])
            listSerialnumbers=[]
            listSerialnumbersEseries=[]
            listSerialnumbersStorageGrid=[]
            self.DetailsStorageGrid=[]
            for clientID in listclientID:
                #userio.message("\nGet serialnumbers for ClientID: [" + clientID + "]")
                self.serialnumbers=getClientIDSerialnumbers("api.activeiq.netapp.com",access_token=self.access_Token,clientID=clientID,debug=self.debug)
                if not self.serialnumbers.go():
                    self.serialnumbers.showDebug()
                    if self.debug & 1:
                        userio.message("This ClientID: [" + clientID + "] does not contain any ONTAP serialnumbers.")
                if len(self.serialnumbers.listOntap) > 0:
                    listSerialnumbers.extend(self.serialnumbers.listOntap)
                if len(self.serialnumbers.listEseries) > 0:
                    listSerialnumbersEseries.extend(self.serialnumbers.listEseries)
                if len(self.serialnumbers.listStorageGrid) > 0:
                    listSerialnumbersStorageGrid.extend(self.serialnumbers.listStorageGrid)
                if len(self.DetailsStorageGrid) == 0:
                    self.DetailsStorageGrid=self.serialnumbers.DetailsStorageGrid.copy()
                else:
                    self.DetailsStorageGrid.update(self.serialnumbers.DetailsStorageGrid)
            self.listSerialNumbers=[]
            self.listSerialNumbers=list(set(listSerialnumbers))  # Remove duplicates
            self.listSerialNumbersEseries=[]
            self.listSerialNumbersEseries=list(set(listSerialnumbersEseries))  # Remove duplicates
            self.listSerialNumbersStorageGrid=[]
            self.listSerialNumbersStorageGrid=list(set(listSerialnumbersStorageGrid))  # Remove duplicates
            
            return(True)
        else:
            self.result=1
            self.reason=rest.reason
            self.stdout=rest.stdout
            self.stderr=rest.stderr
            if self.debug & 4:
                self.showDebug()
            return(False)
        
