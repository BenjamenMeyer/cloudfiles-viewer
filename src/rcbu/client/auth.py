"""
RCBU Authentication API
"""
import json
import requests
import logging
import datetime

from rcbu.common.command import Command


class Authentication(Command):
    """
    Basic Username+Password Authentication for an HTTP REST API
    Presently supports the RAX v1.0 API
    """

    def __init__(self, username, apikey):
        """
        Initialize the Agent access
          sslenabled - True if using HTTPS; otherwise False
          authenticator - instance of rcbu.client.auth.Authentication to use
          apihost - server to use for API calls
          username - user for the authentication
          apikey - apikey/password for the given user
        """
        Command.__init__(self, True, 'identity.api.rackspacecloud.com', "/v2.0/tokens")
        self.log = logging.getLogger(__name__)
        self.o = {}
        self.o['auth'] = {}
        self.o['auth']['RAX-KSKEY:apiKeyCredentials'] = {}
        self.o['auth']['RAX-KSKEY:apiKeyCredentials']['username'] = username
        self.o['auth']['RAX-KSKEY:apiKeyCredentials']['apiKey'] = apikey
        self.body = json.dumps(self.o)
        self.auth_data = {}

    def GetToken(self, retry=5):
        """
        Retrieve the Authentication Tokey

        Note: This may expire quickly. Tokens are valid for 6 hours but are not instance specific
        """
        self.log.debug('host: %s', self.apihost)
        self.log.debug('body: %s', self.Body)
        self.log.debug('headers: %s', self.Headers)
        self.log.debug('uri: %s', self.Uri)
        response = requests.post(self.Uri, headers=self.Headers, data=self.Body)
        if response.status_code is 200:
            self.auth_data = response.json()
            self.log.info('auth token: %s', self.auth_data['access']['token']['id'])
            return self.auth_data['access']['token']['id']
        elif response.status is 404:
            self.log.error('server return unavailable. Trying again up to ' + str(retry) + ' times.')
            if retry is 0:
                assert False
            else:
                return self.GetToken(retry - 1)
        elif response.status_code >= 400:
            self.log.error('failed to authenticate - ' + str(response.status_code) + ': ' + response.text)
        else:
            self.log.error('failed to authenticate: ' + response.text)
            self.auth_data = {}
            return ''

    def IsExpired(self):
        """
        Checks to see if the auth token has expired by comparing its expiration time stamp to the current time in utc
        """
        #2013-12-24T14:02:26.550Z
        expirationtime = datetime.datetime.utcnow()
        try:
            expirationtime = datetime.datetime.strptime(self.AuthExpirationTime, "%Y-%m-%dT%H:%M:%S.%fZ")
        except ValueError:
            try:
                expirationtime = datetime.datetime.strptime(self.AuthExpirationTime, "%Y-%m-%dT%H:%M:%S")
            except ValueError:
                self.log.error('Unknown time format: %s', self.AuthExpirationTime)
                assert False
        nowtime = datetime.datetime.utcnow()
        if expirationtime > nowtime:
            self.log.debug('Auth Token is still valid')
            return False
        else:
            self.log.debug('Auth Token is expired')
            return True

    @property
    def AuthToken(self):
        """
        Retrieve the cached Authentication Token
        Retrieve the cached Authentication Token


        Note: See GetToken()
        """
        try:
            if self.IsExpired():
                return self.GetToken()
            else:
                return self.auth_data['access']['token']['id']
        except LookupError:
            raise UserWarning('Unable to retrieve authentication token')

    @property
    def AuthExpirationTime(self):
        """
        Retrieve the date-time for when the AuthToken expires
        """
        try:
            return self.auth_data['access']['token']['expires']
        except LookupError:
            # We want all the data except the milliseconds
            return datetime.datetime.utcnow().isoformat()[0:19]

    @property
    def AuthId(self):
        """
        Retrieve the User Account Identifier
        """
        try:
            return self.auth_data['access']['token']['tenant']['id']
        except LookupError:
            self.log.error('Unable to retrieve User Identifier. Did you authenticate?')
            return -1

    def GetCloudFilesDataCenters(self):
        """
        Retrieve the list of Data Centers for the authentication
        Returns an array of data centers
        """
        try:
            # We need the auth data so we must have an Auth Token
            token = self.AuthToken
            dclist = []
            for service in self.auth_data['access']['serviceCatalog']:
                if service['name'] == 'cloudFiles':
                    for endpoint in service['endpoints']:
                        dclist.append(endpoint['region'])
            return dclist
        except LookupError:
            self.log.error('Unable to retrieve list of DCs for the currently authenticated user')
            return []

    def GetCloudFilesUri(self, dc):
        """
        Retrieve the CloudFiles URI for the given DC

        Returns an array of dictionaries containing 'name' and 'uri' pairs
        """
        try:
            # We need the auth data so we must have an Auth Token
            token = self.AuthToken
            dcuri = []
            for service in self.auth_data['access']['serviceCatalog']:
                if service['name'] == 'cloudFiles':
                    for endpoint in service['endpoints']:
                        if endpoint['region'] == dc:
                            publicuri = {}
                            publicuri['name'] = 'public'
                            publicuri['uri'] = endpoint['publicURL']
                            dcuri.append(publicuri)
                            sneturi = {}
                            sneturi['name'] = 'snet'
                            sneturi['uri'] = endpoint['internalURL']
                            dcuri.append(sneturi)
            return dcuri
        except LookupError:
            self.log.error('Unable to retrieve DC URI for the currently authenticated user')
            return {}
