import requests
import urllib3
import os
import json
import userio
import time
urllib3.disable_warnings()

class doREST():

    def __init__(self,svm,reqtype,api,**kwargs):

        self.mgmtaddr=svm
        self.reqtype=reqtype
        self.api=api
        self.restargs=None
        self.json=None
        self.url=None
        self.result=None
        self.reason=None
        self.response=None
        self.stdout=[]
        self.stderr=[]
        self.debug=0
        self.synchronous=False
        self.sleeptime=1
        self.access_token=None
        self.headers=None

        self.apibase=self.__class__.__name__

        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        else:
            self.apicaller=''

        if 'debug' in kwargs.keys():
            self.debug=kwargs['debug']

        if 'synchronous' in kwargs.keys():
            self.synchronous=kwargs['synchronous']

        if 'headers' in kwargs.keys():
            self.headers=kwargs['headers']

        if 'sleeptime' in kwargs.keys():
            self.sleeptime=kwargs['sleeptime']
 
        if 'restargs' in kwargs.keys():
            if type(kwargs['restargs']) is list:
                self.restargs=kwargs['restargs']
            elif type(kwargs['restargs']) is str:
                self.restargs=[kwargs['restargs']]
            elif type(kwargs['restargs']) is tuple:
                self.restargs=[str(''.join(kwargs['restargs']))]

        if 'json' in kwargs.keys():
            self.json=kwargs['json']

        self.go()

    def showDebug(self):
        userio.debug(self)

    def go(self,**kwargs):
        self.url="https://" + self.mgmtaddr + self.api
        if self.restargs is not None:
            self.url=self.url + "?" + "&".join(self.restargs)
        self.call=self.reqtype.upper() + " " + self.url
        self.jsonin=str(self.json)

        try:
            if self.reqtype=="get":
                response=requests.get(self.url,verify=False,headers=self.headers, timeout=30)
            elif self.reqtype=="post":
                response=requests.post(self.url,json=self.json,verify=False,headers=self.headers, timeout=30)
            elif self.reqtype=="patch":
                response=requests.patch(self.url,json=self.json,verify=False,headers=self.headers, timeout=30)
            elif self.reqtype=="delete":
                response=requests.delete(self.url,verify=False,headers=self.headers, timeout=30)
            else:
                self.result=1
                self.reason="Unsupported request type"
                return(False)
        
        except Exception as e:
            self.result=1
            self.reason=str(e)
            return(False)
        except requests.exceptions.Timeout:
            self.result=1
            self.reason="Request timed out"
            return(False)
        except:
            self.result=1
            self.reason="Unknown error"
            return(False)
        
        self.jsonout=json.dumps(response.json(),indent=1).splitlines()
        self.result=response.status_code
        self.reason=response.reason
        self.response=response.text

        if self.debug & 2:
            self.showDebug()

        if not response.ok:
            try:
                convert2dict=response.json()
                self.response=convert2dict
                return(True)
            except Exception as e:
                self.result=1
                self.reason=e
            return(False)
        elif not self.synchronous and self.result == 202:
            try:
                convert2dict=response.json()
                self.response=convert2dict
                return(True)
            except Exception as e:
                self.result=1
                self.reason=e
                return(False)
        elif self.synchronous and self.result == 202:
            tmpurl=self.url
            tmpjsonin=self.jsonin
            tmpapi=self.api
            tmprestargs=self.restargs
            tmpreqtype=self.reqtype
            tmpresponse=self.response
            self.jsonin=None
            try:
                convert2dict=response.json()
                jobuuid=convert2dict['job']['uuid']
            except:
                self.reason="Unable to retrieve uuid for asynchronous operation"
                if self.debug & 2:
                    self.showDebug()
                return(False)
            
            running=True
            while running:
                time.sleep(self.sleeptime)
                self.api="/cluster/jobs/" + jobuuid
                self.url="https://" + self.mgmtaddr + "/api" + self.api
                self.restargs=["fields=state,message"]
                self.url=self.url + "?" + "&".join(self.restargs)
                self.call="GET " + self.url
        
                try:
                    jobrest=requests.get(self.url,auth=(username,password),verify=False)
                
                except Exception as e:
                    self.reason=str(e)
                    return(False)

                convert2dict=jobrest.json()
                self.jsonout=json.dumps(jobrest.json(),indent=1).splitlines()
                self.response=convert2dict
                self.result=jobrest.status_code
                self.reason=jobrest.reason
    
                if self.debug & 2:
                    self.showDebug()
                
                if not self.result == 202 and not self.response['state'] == 'running':
                    running=False
                
            if not self.result == 200:
                self.reason="Job " + jobuuid + " failed"
                return(False)
            elif not self.response['state'] == 'success':
                self.result=1
                return(True)
            else:
                self.url=tmpurl
                self.jsonin=tmpjsonin
                self.api=tmpapi
                self.restargs=tmprestargs
                self.reqtype=tmpreqtype
                self.response=tmpresponse
                return(True)
                
        else:
            self.result=response.status_code
            self.reason=response.reason
            self.response=response.text
            try:
                convert2dict=response.json()
                self.response=convert2dict
            except:
                pass
            return(True)
    
