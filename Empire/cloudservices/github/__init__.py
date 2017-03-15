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
GitHub
"""

__copyright__ = "2015 Salesforce.com, Inc"
__status__    = "Prototype"

# TODO:
# - Pagination the github way
# - Groups / Users / Org
# - Security
# - Stale branches

import sys
import os.path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from creds import CredentialManager
import requests
import urllib
import datetime
import pytz
from cloudservices.github.GithubAPI import GithubAPI

__copyright__ = "2015 Salesforce.com, Inc"
__status__    = "Prototype"

class GithubOrg(object):
    def __init__(self, server, orgname, creds):
        self.server = server
        self.name = orgname
        self.creds = creds
        self.github_api = GithubAPI(server, creds)

    def repositories(self, _type="all"):
        url = "%s/repos" % (self.github_api.baseURL(self.name))
        params = {"type":_type}
        results = self.github_api.fetch(url, params=params)
        if results is None:
            return None
        repos = []
        for result in results:
            if result.get("name") is None:
                continue
            repo = GithubRepo(self, result.get("name"), repo_json=result)
            repos.append(repo)
        return repos

    def repository(self, repository_name):
        url = "%s" % (self.github_api.baseURL(self.name), repository_name)
        result = self.github_api.fetch(url)
        if result is None:
            return None
        repo = GithubRepo(self, result.get("name"), repo_json=result)        

    def members(self, _filter="all"):
        url = "%s/members" % (self.github_api.baseURL(self.name))
        params = {"filter":_filter, "per_page":200}
        results = self.github_api.fetch(url, params=params)
        if results is None:
            return None
        members = []
        for result in results:
            if result.get("id") is None:
                continue
            member = GithubMember(self, result.get("id"), member_json=result)
            members.append(member)
        return members

class GithubRepo(object):
    def __init__(self, github_org, name, repo_json=None):
        self.github_org = github_org
        self.name = name
        self.json = repo_json

    def issues(self, params=None):
        url = "%s/issues" % (self.github_org.github_api.baseURL(self.github_org.name, self.name))
        results = self.github_org.github_api.fetch(url, params=params)
        if results is None:
            return None
        issues = []
        for result in results:
            if result.get("number") is None:
                continue
            issue = GithubIssue(self.github_org, result.get("number"), github_repo=self, issue_json=result)
            issues.append(issue)
        return issues

    def issue(self, issue_number):
        url = "%s/issues/%s" % (self.github_org.github_api.baseURL(self.github_org.name, self.name), issue_number)
        result = self.github_org.github_api.fetch(url)
        if result is None:
            return None
        issue = GithubIssue(self.github_org, result.get("number"), github_repo=self, issue_json=result)
        return issue

    def commits(self, commits_since_datetime, path=None):
        commits_since_datetime_utc = commits_since_datetime.astimezone(pytz.utc)
        since_iso_string = commits_since_datetime_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        until_iso_string = datetime.datetime.utcnow().isoformat('T') + "Z"

        url = "%s/commits" % (self.github_org.github_api.baseURL(self.github_org.name, self.name))
        params = {"since":since_iso_string}
        if path:
            params["path"] = path
        results = self.github_org.github_api.fetch(url, params=params)
        if results is None:
            return None
        commits = []
        for result in results:
            if result.get("sha") is None:
                continue
            commit = GithubCommit(self, result.get("sha"), commit_json=result)
            commits.append(commit)
        return commits

    def commit(self, commit_sha):
        url = "%s/commits/%s" % (self.github_org.github_api.baseURL(self.github_org.name, self.name), commit_sha)
        result = self.github_org.github_api.fetch(url)
        if result is None:
            return None
        commit = GithubCommit(self, result.get("sha"), commit_json=result)
        return commit

    def get_raw_file(self, file_path, commit_sha=None):
        url = "%s/contents/%s" % (self.github_org.github_api.baseURL(self.github_org.name, self.name), file_path)
        file_content = self.github_org.github_api.fetch_raw(url)
        return file_content

class GithubIssue(object):
    def __init__(self, github_org, number, github_repo=None, issue_json=None):
        self.github_org = github_org
        self.github_repo = github_repo
        self.number = number
        self.json = issue_json

class GithubCommit(object):
    def __init__(self, github_repo, sha, commit_json=None):
        self.github_repo = github_repo
        self.sha = sha
        self.json = commit_json
        self.url = None
        self.html_url = None
        self.message = None
        self.date = None
        self.committer_name = None
        self.committer_email = None
        self.committer_login = None
        self.committer_type = None
        self.files = None
        if self.json is not None:
            self.parseJSON(self.json)

    def parseJSON(self, commits_json):
        self.url = commits_json.get('url')
        self.sha = commits_json.get('sha')
        self.html_url = commits_json.get('html_url')

        commit = commits_json.get('commit')
        if commit is None:
            commit = {}
        self.message = commit.get("message")
        commit_committer = commit.get('committer')
        if commit_committer is None:
            commit_committer = {}
        self.date = commit_committer.get('date')
        self.committer_email = commit_committer.get('email')

        committer = commits_json.get('committer')
        if committer is None:
            committer = {}
        self.committer_login = committer.get('login')
        self.committer_name = committer.get('name')
        self.committer_type = committer.get('type')
        self.files = commits_json.get('files')

class GithubMember(object):
    def __init__(self, github_org, _id, member_json=None):
        self.github_org = github_org
        self.id = _id
        self.json = member_json

if __name__ == "__main__":

    credentials_file = "credentials.json"
    credential_key = os.environ.get('CREDENTIAL_KEY')
    if credential_key is None:
        credential_key = getpass.getpass('Credential Key:')
    credential_manager = CredentialManager(credentials_file, credential_key)
    creds = credential_manager.get_or_create_credentials_for("github-pardot-orgowner","password")

    git = GithubOrg('api.github.com', 'Pardot', creds)
    members = git.members("2fa_disabled")
    for member in members:
        print member.json["login"]

    bugs = git.issues(params={"labels":"bug,security","state":"all","since":"2015-02-01T00:00:00Z"})
    import json
    print json.dumps(bugs, indent=2)
    if bugs:
        for bug in bugs:
            print bug["title"], bug["state"]
