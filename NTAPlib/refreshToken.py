import doREST
import re
import userio

class refreshToken:

    def __init__(self,url,refresh_Token,**kwargs):
        self.result=None
        self.reason=None
        self.stdout=[]
        self.stderr=[]
        self.url=url
        self.refresh_Token=refresh_Token
        self.access_Token=None
        self.debug=False

        self.apibase=self.__class__.__name__
        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        else:
            self.apicaller=''
        localapi='->'.join([self.apicaller,self.apibase])
        
        self.api='/v1/tokens/accessToken'

        if 'debug' in kwargs.keys():
            self.debug=kwargs['debug']

        return
    
    def showDebug(self):
        userio.debug(self)

    def go(self,**kwargs):

        headers = {'content-type': "application/json",
           'accept': "application/json",
           'User-Agent': "test",
           'Connection': "keep-alive"}
        # headers['AuthorizationToken']=self.refresh_Token

        json={'refresh_token':self.refresh_Token}
        
        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        localapi='->'.join([self.apicaller,self.apibase + ".go"])

        if self.debug & 1:
            userio.message("refresh AIQ access token with refresh token...")
        rest=doREST.doREST(self.url,'post',self.api,debug=self.debug,headers=headers,json=json)
        if rest.result == 200:
            self.access_Token=rest.response['access_token']
            self.refresh_Token=rest.response['refresh_token']
            self.result=0
            if self.debug & 4:
                self.showDebug()
            return(True)
        else:
            self.result=1
            self.reason=rest.reason
            self.stdout=rest.stdout
            self.stderr=rest.stderr
            if self.debug & 4:
                self.showDebug()
            return(False)

