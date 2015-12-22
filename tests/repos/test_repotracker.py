'''
Copyright (c) 2015, Salesforce.com, Inc.
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

* Neither the name of Salesforce.com nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

import unittest
import os

import json
import string
import random
import getpass

from datetime import datetime

from Empire.creds import CredentialManager
import config
configuration = config.Configuration()
credentials_file = configuration.get('credentials_file')
credential_key = os.environ.get('CREDENTIAL_KEY')
if credential_key is None:
    credential_key = getpass.getpass('Credential Key:')
credential_manager = CredentialManager(credentials_file, credential_key)

config.credential_manager = credential_manager
from repos.repotracker import RepoTracker

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

class RepoTrackerTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_last_identifier(self):
        repo = RepoTracker()

        temp_identifier = id_generator()
        repo.update_identifier("test-identifier", temp_identifier)
        fetched_identifier = repo.last_identifier("test-identifier")
        self.assertEqual(temp_identifier, fetched_identifier)

    def test_last_run_completed(self):        
        repo = RepoTracker()

        temp_last_run = datetime.utcnow()
        repo.update_last_run_completed("test-last-run",temp_last_run)
        fetched_last_run = repo.last_run_completed("test-last-run")
        self.assertEqual(temp_last_run, fetched_last_run)
