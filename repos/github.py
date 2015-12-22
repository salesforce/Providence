'''
Copyright (c) 2015, Salesforce.com, Inc.
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

* Neither the name of Salesforce.com nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

import requests
import json
import datetime
import dateutil.parser
import urllib
import os
import pytz

from Empire.cloudservices.github import GithubOrg, GithubRepo, GithubCommit
from repos.base import RepoSource, RepoCommit, RepoPatch
from repos.diffparser import DiffParser
import logging
logger = logging.getLogger('repos_github')

owner = 'jacquev6'
repo = 'PyGithub'

class GithubSource(RepoSource):
    def __init__(self, creds=None, host='api.github.com', owner='Pardot', repo='pardot'):
        self._last_date = None
        self._last_identifier = None
        self._no_more_requests_until = None
        github_org = GithubOrg(host, owner, creds)
        self._github_repo = GithubRepo(github_org, repo)

    def processSinceIdentifier(self, identifier, commit_started_callback, patch_callback, commit_finished_callback, path=None):
        since_datetime = datetime.datetime.utcnow()
        since_datetime = since_datetime.replace(tzinfo=pytz.UTC, hour=0, minute=0, second=0)
        if identifier:
            try:
                since_datetime = dateutil.parser.parse(identifier)
            except Exception as e:
                logger.error("Error parsing datetime from %s", identifier)
        commits = self._github_repo.commits(since_datetime, path=path)
        self.processCommits(commits, 
                            commit_started_callback=commit_started_callback,
                            patch_callback=patch_callback,
                            commit_finished_callback=commit_finished_callback);
        if self._last_date:
            return self._last_date.isoformat()
        if since_datetime:
            return since_datetime.isoformat()
        return None

    def processCommits(self, commits, commit_started_callback, patch_callback, commit_finished_callback):
        if commits is None:
            return None

        # Process oldest first
        commits = commits[::-1]
        logger.debug("process %d commits", len(commits))
        for github_commit in commits:
            logger.debug("sha: %s", github_commit.sha)
            if github_commit.sha:
                github_commit = self._github_repo.commit(github_commit.sha)

                repo_commit = RepoCommit();
                repo_commit.url = github_commit.html_url
                repo_commit.repo_source = self

                if github_commit.date is not None:
                    self._last_date = dateutil.parser.parse(github_commit.date)

                    repo_commit.date = self._last_date
                    self._last_date += datetime.timedelta(seconds=1)
                    repo_commit.identifier = self._last_date.isoformat()

                    repo_commit.committer_email = github_commit.committer_email
                    repo_commit.committer_name = github_commit.committer_name
                    repo_commit.username = github_commit.committer_login
                    repo_commit.message = github_commit.message
                    
                    repo_commit.sha = github_commit.sha
                    commit_started_callback(repo_commit)

                    if github_commit.files:
                        for file_info in github_commit.files:
                            if file_info.get('patch'):
                                filename = committer_username = None
                                diff = DiffParser(file_info['patch'])
                                repo_patch = RepoPatch(repo_commit=repo_commit)
                                repo_patch.diff = diff
                                repo_patch.filename = file_info.get("filename")
                                patch_callback(repo_patch)

                    commit_finished_callback(repo_commit)
                    logger.debug("batch fof files processed")
        logger.debug("done")


if __name__ == "__main__":
    from Empire.creds import CredentialManager
    credentials_file = "credentials.json"
    credential_key = os.environ.get('CREDENTIAL_KEY')
    if credential_key is None:
        credential_key = getpass.getpass('Credential Key:')
    credential_manager = CredentialManager(credentials_file, credential_key)
    creds = credential_manager.get_or_create_credentials_for("github-mfeldmansf","password")

    test = GithubSource(creds);
    def cstart(commit):
        print commit
    def pstart(patch):
        print "touched ", patch.filename
    def cend(commit):
        pass
    test.processSinceIdentifier("2014-11-12T00:00:00Z", cstart, pstart, cend);
