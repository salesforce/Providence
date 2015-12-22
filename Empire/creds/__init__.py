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
Credential Manager Base Classes

CredentialManager - Manage the location, collection and encryption/decryption of credentials
"""

import sys
import os.path
import json
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
from creds.credentials import Credentials 
from creds.credentials import CredentialsInvalidError, OAuthCredentials
import helpers

CRYPTO_FERNET=True
try:
    from cryptography.fernet import Fernet
except:
    CRYPTO_FERNET=False
    import fernet
    fernet.Configuration.enforce_ttl = False

__copyright__ = "2015 Salesforce.com, Inc"
__status__    = "Prototype"

class CredentialManager(object):
    def __init__(self, filename, key=None):
        def decrypt(ciphertext):
            if key is None:
                return ciphertext
            try:
                value = ciphertext
                if CRYPTO_FERNET == True:
                    f = Fernet(key)
                    value = f.decrypt(ciphertext)
                else:
                    verifier = fernet.verifier(key, ciphertext)
                    if verifier.valid() == True:
                        value = verifier.message
                return value
            except Exception as e:
                pass
            return ciphertext

        def encrypt(value):
            if key is None:
                return value
            if CRYPTO_FERNET == True:
                f = Fernet(key)
                token = f.encrypt(bytes(value))
            else:
                token = fernet.generate(key, value)
            return token

        self.filename = filename
        self.encrypt = encrypt
        self.decrypt = decrypt

    def credential_object_for_type(self, identifier, type):
        if (type == "password"):
            return Credentials(identifier)
        raise NotImplementedError("Credential type '%s' is not supported" % (type))

    def get_credentials_for(self, identifier, check_valid=True):
        file_creds = {}
        try:
            with open(self.filename) as fp:
              file_creds = json.load(fp,object_hook=helpers.convert)
        except IOError as ioe:
            raise NameError("Credential file not found. " + str(ioe))

        user_creds = file_creds.get(identifier)
        if user_creds is None:
            raise NameError(identifier)
            return

        #XXX: Why bother type checking here if we're specifying that in the function
        #XXX: call in providence.py? 
        type = user_creds.get("type")
        credentials = self.credential_object_for_type(identifier, type)
        credentials.credential_manager = self
        credentials.encrypt = self.encrypt
        credentials.decrypt = self.decrypt
        credentials.read(user_creds)

        if check_valid == True and credentials.valid() == False:
            if isinstance(creds, OAuthCredentials):
                try:
                    credentials.refreshToken()
                    if credentials.valid():
                        if write == True:
                            credentials.write()
                        return credentials
                except NotImplementedError, nie:
                    pass
            raise CredentialsInvalidError("Invalid Credentials for %s" % identifier)
        return credentials

    def get_or_create_credentials_for(self, identifier, type, write=True, check_valid=True):
        try:
            creds = self.get_credentials_for(identifier, check_valid=False)
        except NameError, ne:
            creds = self.new_credentials_for(identifier, type)
            if write == True:
                creds.write()
        if check_valid == True and creds.valid() == False:
            # If it's an Oauth token maybe it needs refreshed?
            if isinstance(creds, OAuthCredentials):
                try:
                    creds.refreshToken()
                    if creds.valid():
                        if write == True:
                            creds.write()
                        return creds
                except NotImplementedError, nie:
                    pass
            # Lets give them 3 attempts to login
            for attempt_numer in range(3):
                creds.new_credentials()
                if creds.valid():
                    if write == True:
                        creds.write()
                    return creds
            # All attempts failed, return creds are bad
            raise CredentialsInvalidError("Invalid Credentials for %s" % identifier)
        return creds

    def new_credentials_for(self, identifier, type, server_data=None):
        credentials = self.credential_object_for_type(identifier, type)
        credentials.credential_manager = self
        credentials.encrypt = self.encrypt
        credentials.decrypt = self.decrypt
        if (server_data is not None):
            credentials.server_data = server_data
        credentials.new_credentials()

        return credentials

    def write_back_credentials(self, credentials):
        file_creds = {}
        try:
            file_data = open(self.filename)
            file_creds = json.load(file_data)
        except IOError as ioe:
            print "Credential file not found, will create..."

        user_creds = file_creds.get(credentials.identifier)
        if user_creds is None:
            user_creds = {}
        user_creds = credentials._populate_user_creds(user_creds)
        file_creds[credentials.identifier] = user_creds

        with open(self.filename, 'w') as outfile:
          json.dump(file_creds, outfile, indent=2, separators=(',', ': '))


if __name__ == '__main__':
    import os
    credential_key = os.environ.get('CREDENTIAL_KEY')
    credentials_file = "credentials2.json"
    credential_manager = CredentialManager(credentials_file, credential_key)
