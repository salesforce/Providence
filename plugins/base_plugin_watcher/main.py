'''
Copyright (c) 2015, Salesforce.com, Inc.
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

* Neither the name of Salesforce.com nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

import sys
import os.path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from repos.perforce import PerforceSource
from repos.github import GithubSource
from detection.pattern.regexruleengine import RegexRuleEngine
from Empire.creds.credentials import Credentials
from plugins import base, RepoWatcher
import logging
import config

logger = logging.getLogger(__name__)

class Plugin(base.Plugin):

    def register_repositories(self):
        logger.debug("registering repository")

        configuration = config.Configuration('config.json')
        
        repos = {}
        for repo in configuration.get('repos'):
            repo_type = repo.get('type')
            if repo_type == 'perforce':
                repo_name = repo.get('name')
                creds = config.credential_manager.get_or_create_credentials_for(repo_name, "password")
                if creds is None:
                    logger.error("Failed to load credentials")
                    return {}
                repo_source = PerforceSource(creds=creds, port=repo.get('server'), directory=repo.get('directory'))
                repos[repo_name] = {"source":repo_source, "check-every-x-minutes":10}
            elif repo_type == 'github':
                repo_name = repo.get('name')
                creds = config.credential_manager.get_or_create_credentials_for(repo_name, "password")
                if creds is None:
                    logger.error("Failed to load credentials")
                    return {}
                repo_source = GithubSource(creds=creds, host=repo.get('server'), owner=repo.get('owner'), repo=repo.get('directory'))
                repos[repo_name] = {"source":repo_source, "check-every-x-minutes":10}
            else:
                print "Repo Type not supported yet: " + repo_type

        return repos

    def test(self):
        logger.warn("No tests")

if __name__ == "__main__":
    test();
