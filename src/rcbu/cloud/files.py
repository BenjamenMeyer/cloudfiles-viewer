"""
Rackspace Cloud Files
"""
import logging
import requests

from rcbu.common.command import Command


class CloudFiles(Command):
    """
    Primary Cloud Files API Class
    """

    def __init__(self, sslenabled, authenticator):
        """
        Setup the CloudFiles API Class in the same manner as rcbu.common.Command
        """
        Command.__init__(self, sslenabled, 'localhost', '/')
        # save the ssl status for the various reinits done for each API call supported
        self.sslenabled = sslenabled
        self.authenticator = authenticator
        self.auth = authenticator
        self.log = logging.getLogger(__name__)

    def GetContainers(self, uri, limit=-1, marker=''):
        """
        List all containers for the current account
        """
        self.apihost = uri
        urioptions = '?format=json'
        if not limit is -1:
            urioptions += '&limit=%d' % limit
        if len(marker):
            urioptions += '&marker=%s' % marker
        self.ReInit(self.sslenabled, urioptions)
        self.headers['X-Auth-Token'] = self.authenticator.AuthToken
        self.headers['Content-Type'] = 'text/plain; charset=UTF-8'
        self.log.debug('uri: %s', self.Uri)
        self.log.debug('headers: %s', self.Headers)
        res = requests.get(self.Uri, headers=self.Headers)
        if res.status_code == 200:
            # We have a list in JSON format
            return res.json()
        elif res.status_code == 204:
            # Nothing left to retrieve
            return {}
        else:
            # Error
            self.log.error('Error retrieving list of containers: (code=' + str(res.status_code) + ', text=\"' + res.text + '\")')
            return {}

    def GetContainerObjects(self, uri, container, limit=-1, marker=''):
        """
        List the objects in a container under the current account
        """
        self.apihost = uri
        urioptions = '/' + container + '?format=json'
        if not limit is -1:
            urioptions += '&limit=%d' % limit
        if len(marker):
            urioptions += '&marker=%s' % marker
        self.ReInit(self.sslenabled, urioptions)
        self.headers['X-Auth-Token'] = self.authenticator.AuthToken
        self.headers['Content-Type'] = 'text/plain; charset=UTF-8'
        self.log.debug('uri: %s', self.Uri)
        self.log.debug('headers: %s', self.Headers)
        res = requests.get(self.Uri, headers=self.Headers)
        if res.status_code == 200:
            # We have a list in JSON format
            return res.json()
        elif res.status_code == 204:
            # Nothing left to retrieve
            return {}
        else:
            # Error
            self.log.error('Error retrieving list of containers: (code=' + str(res.status_code) + ', text=\"' + res.text + '\")')
            return {}
