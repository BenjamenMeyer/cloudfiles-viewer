"""
Rackspace Cloud Files
"""
import logging
import requests
import hashlib

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

    def DownloadObject(self, uri, container, object_data,  localpath):
        """
        Download the object
        """
        self.apihost = uri
        try:
            self.ReInit(self.sslenabled, '/' + container + '/' + object_data['name'])
            self.headers['X-Auth-Token'] = self.authenticator.AuthToken
            self.log.debug('uri: %s', self.Uri)
            self.log.debug('headers: %s', self.Headers)
            try:
                res = requests.get(self.Uri, headers=self.Headers)
            except request.exceptions.SSLError as ex:
                self.log.error('Request SSLError: {0}'.format(str(ex)))
                res = requests.get(self.Uri, headers=self.Headers, verify=False)

            if res.status_code == 404:
                raise UserWarning('Cloud Files did not find the object')

            elif res.status_code >= 300:
                raise UserWarning('Cloud Files responded unexpecteduing during download initiation (Code: ' + str(res.status_code) + ' )')
            else: 
                meter = {}
                meter['bytes-remaining'] = int(res.headers['Content-Length'])
                meter['bar-count'] = 50
                meter['bytes-per-bar'] = meter['bytes-remaining'] // meter['bar-count']
                meter['block-size'] = min(2 ** 12, meter['bytes-per-bar'])
                meter['chunks-per-bar'] = meter['bytes-per-bar'] // meter['block-size']
                meter['chunks'] = 0
                meter['bars-remaining'] = meter['bar-count']
                meter['bars-completed'] = 0
                self.log.info('Downloading object: {0} bytes...'.format(meter['bytes-remaining']))
                self.log.info('[' + ' ' * meter['bar-count'] + ']')
                md5_hash = hashlib.md5()
                sha1_hash = hashlib.sha1()
                with open(localpath, 'wb') as target_file:
                    for object_chunk in res.iter_content(chunk_size=meter['block-size']):
                        target_file.write(object_chunk)
                        md5_hash.update(object_chunk)
                        sha1_hash.update(object_chunk)
                        meter['chunks'] += 1
                        if meter['chunks'] == meter['chunks-per-bar']:
                            meter['chunks'] = 0
                            meter['bars-completed'] += 1
                            meter['bars-remaining'] -= 1
                            self.log.info('[' + '-' * meter['bars-completed'] + ' ' * meter['bars-remaining'] + ']')
                object_data['md5'] = md5_hash.hexdigest().upper()
                object_data['sha1'] = sha1_hash.hexdigest().upper()
                self.log.info('VaultDB (' + object_data['name'] + ') was successfully downloaded to ' + localpath)
                return True
        except LookupError:
            raise UserWarning('Invalid Object Data provided.')
