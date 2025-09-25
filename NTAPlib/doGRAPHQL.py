import requests
import json
import userio

class doGraphQL:
    
    def __init__(self, url, query, variables=None, **kwargs):
        self.result = None
        self.reason = None
        self.stdout = []
        self.stderr = []
        self.url = "https://" + url
        self.query = query
        self.variables = variables or {}
        self.response = None
        self.debug = False
        self.access_token = None
        self.headers = {}
        self.timeout = 30
        
        self.apibase = self.__class__.__name__
        
        if 'apicaller' in kwargs.keys():
            self.apicaller = kwargs['apicaller']
        else:
            self.apicaller = ''
            
        if 'debug' in kwargs.keys():
            self.debug = kwargs['debug']
            
        if 'access_token' in kwargs.keys():
            self.access_token = kwargs['access_token']
            
        if 'headers' in kwargs.keys():
            self.headers.update(kwargs['headers'])
            
        if 'timeout' in kwargs.keys():
            self.timeout = kwargs['timeout']
            
        # Headers par défaut pour GraphQL
        self.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # Ajouter le token d'authentification si fourni
        if self.access_token:
            self.headers['Authorization'] = f'Bearer {self.access_token}'
            
        self.go()
    
    def showDebug(self):
        userio.debug(self)
        if self.debug >= 3:
            userio.message(f"GraphQL Query: {self.query}")
            userio.message(f"Variables: {json.dumps(self.variables, indent=2)}")
            userio.message(f"Headers: {json.dumps(self.headers, indent=2)}")
            if self.response:
                userio.message(f"Response: {json.dumps(self.response, indent=2)}")
    
    def go(self, **kwargs):
        """
        Exécute la requête GraphQL
        """
        if 'apicaller' in kwargs.keys():
            self.apicaller = kwargs['apicaller']
            
        localapi = '->'.join([self.apicaller, self.apibase + ".go"])
        
        # Préparer le payload GraphQL
        payload = {
            "query": self.query,
            "variables": self.variables
        }
        
        if self.debug >= 3:
            userio.message(f"GraphQL URL: {self.url}")
            userio.message(f"Payload: {json.dumps(payload, indent=2)}")
        
        try:
            # Faire la requête POST
            response = requests.post(
                self.url,
                json=payload,
                headers=self.headers,
                timeout=self.timeout,
                verify=False  
            )
            
            # Stocker le code de statut
            self.result = response.status_code
            
            if response.status_code == 200:
                # Parser la réponse JSON
                self.response = response.json()
                
                # Vérifier les erreurs GraphQL
                if "errors" in self.response:
                    self.result = 1
                    self.reason = response.reason
                    self.stderr = self.response["errors"]
                    
                    if self.debug >= 1:
                        userio.message(f"GraphQL Errors:")
                        for error in self.response["errors"]:
                            userio.message(f"  - {error.get('message', 'Unknown error')}")
                            if 'locations' in error:
                                userio.message(f"    Location: {error['locations']}")
                            if 'path' in error:
                                userio.message(f"    Path: {error['path']}")
                    
                    if self.debug & 4:
                        self.showDebug()
                    return False
                
                # Succès
                self.reason = response.reason
                
                if self.debug & 4:
                    self.showDebug()
                    
                return True
                
            else:
                # Erreur HTTP
                self.result = response.status_code
                self.reason = response.reason
                self.stderr.append(f"HTTP {response.status_code}: {response.reason}")
                
                try:
                    error_response = response.json()
                    self.response = error_response
                    if 'error' in error_response:
                        self.stderr.append(error_response['error'])
                except:
                    self.stderr.append(response.text)
                
                if self.debug >= 1:
                    userio.message(f"HTTP Error {response.status_code}: {response.reason}")
                    userio.message(f"Response: {response.text}")
                
                if self.debug & 4:
                    self.showDebug()
                    
                return False
                
        except requests.exceptions.Timeout:
            self.result = 1
            self.reason = "Request timeout"
            self.stderr.append(f"Request timed out after {self.timeout} seconds")
            
            if self.debug >= 1:
                userio.message(f"Request timeout after {self.timeout} seconds")
                
            return False
            
        except requests.exceptions.ConnectionError as e:
            self.result = 1
            self.reason = "Connection error"
            self.stderr.append(str(e))
            
            if self.debug >= 1:
                userio.message(f"Connection error: {str(e)}")
                
            return False
            
        except requests.exceptions.RequestException as e:
            self.result = 1
            self.reason = "Request error"
            self.stderr.append(str(e))
            
            if self.debug >= 1:
                userio.message(f"Request error: {str(e)}")
                
            return False
            
        except json.JSONDecodeError as e:
            self.result = 1
            self.reason = "JSON decode error"
            self.stderr.append(f"Failed to parse JSON response: {str(e)}")
            
            if self.debug >= 1:
                userio.message(f"JSON decode error: {str(e)}")
                
            return False
            
        except Exception as e:
            self.result = 1
            self.reason = "Unexpected error"
            self.stderr.append(str(e))
            
            if self.debug >= 1:
                userio.message(f"Unexpected error: {str(e)}")
                
            return False
    
    def get_data(self):
        """
        Retourne les données de la réponse GraphQL si disponibles
        """
        if self.response and "data" in self.response:
            return self.response["data"]
        return None
    
    def get_errors(self):
        """
        Retourne les erreurs GraphQL si disponibles
        """
        if self.response and "errors" in self.response:
            return self.response["errors"]
        return []
    
    def has_errors(self):
        """
        Vérifie si la réponse contient des erreurs GraphQL
        """
        return self.response and "errors" in self.response and len(self.response["errors"]) > 0