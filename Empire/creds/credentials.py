'''
Copyright (c) 2015, Salesforce.com, Inc.
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

* Neither the name of Salesforce.com nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

"""
Credential Method Specific Classes

Credentials                               - Base class to be inherited
OAuthCredential(Credentials)              - OAuth Methods 
"""
import json
import base64
import requests
import copy
import getpass
import urllib

import httplib2
import csv

from rauth import OAuth2Service

#from apiclient.discovery import build
#from oauth2client.file import Storage
#from oauth2client.client import OAuth2WebServerFlow
#from oauth2client.tools import run
#from oauth2client.client import OAuth2Credentials
#from oauth2client.client import FlowExchangeError
#import argparse
#from oauth2client import tools

__copyright__ = "2015 Salesforce.com, Inc"
__status__    = "Prototype"

class CredentialsInvalidError(Exception):
    pass

class Credentials(object):
    def __init__(self, identifier):
        self.type = "password"
        self.identifier = identifier
        self.server_data = {}
        self.username = None
        self.password = None

    def read(self, user_creds):
        self.username = user_creds.get("username")
        self.password = user_creds.get("password")
        if self.password:
            self.password = self.decrypt(self.password)

    def _populate_user_creds(self, user_creds):
        user_creds = {}
        user_creds["type"] = self.type
        if self.username is not None:
            user_creds["username"] = self.username
        if self.password is not None:
            user_creds["password"] = self.encrypt(self.password)
        return user_creds

    def new_credentials(self):
        print "Need credentials for [", self.identifier, "]"
        username = raw_input('Enter your username: ')
        password = getpass.getpass('Enter your password: ')
        self.username = username
        self.password = password

    def authorizationHeaderValue(self):
        b64creds = base64.b64encode("%s:%s" % (self.username, self.password))
        return "Basic %s" % (b64creds)

    def write(self):
        self.credential_manager.write_back_credentials(self)

    def valid(self):
        return True

class OAuthCredentials(Credentials):
    def __init__(self, identifier):
        super(OAuthCredentials, self).__init__(identifier)
        self.type = "oauth"
        self.token_data = {}

    def read(self, user_creds):
        super(OAuthCredentials, self).read(user_creds)
        self.token_data = user_creds.get("token_data",{})
        if self.token_data.get("access_token") is not None:
            self.token_data["access_token"] = self.decrypt(self.token_data["access_token"])
        self.server_data = user_creds.get("server_data",{})
        if self.server_data is not None:
            self.server_data = user_creds.get("server_data",{})
            if self.server_data.get("client_secret") is not None:
                self.server_data["client_secret"] = self.decrypt(self.server_data["client_secret"])

    def _populate_user_creds(self, user_creds):
        user_creds = super(OAuthCredentials, self)._populate_user_creds(user_creds)
        if self.token_data and self.token_data.get("access_token") is not None:
            user_creds["token_data"] = copy.deepcopy(self.token_data)
            user_creds["token_data"]["access_token"] = self.encrypt(self.token_data["access_token"])
        if self.server_data is not None:
            user_creds["server_data"] = copy.deepcopy(self.server_data)
            if self.server_data.get("client_secret") is not None:
                user_creds["server_data"]["client_secret"] = self.encrypt(self.server_data["client_secret"])
        return user_creds

    def authorizationHeaderValue(self):
        if self.token_data is None or self.token_data.get("access_token") is None:
            self.refreshToken()
        return "Bearer %s" % (self.token_data.get("access_token"))

    def refreshToken(self):
        raise NotImplementedError
