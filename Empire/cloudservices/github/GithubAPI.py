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
GitHubCommit  - Convert JSON message from GH into an object representative of the commit
GitHubRepo    - Represent the basic information needed to interact with a GH repo
GitHubAPI     - Send and receive data from the REST API
"""

# TODO:
# - Pagination the github way
# - Groups / Users / Org
# - Security
# - Stale branches

import sys
import os.path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from creds.credentials import Credentials
import requests
import urllib
import datetime
import pytz
import json
import logging
logger = logging.getLogger('GithubAPI')

__copyright__ = "2015 Salesforce.com, Inc"
__status__    = "Prototype"

class GithubAPI(object):
    def __init__(self, server, credentials):
        self.server = server
        self.credentials = credentials
        self._no_more_requests_until = None

    def fetch(self, url, params=None, post_data=None):
        if self._no_more_requests_until:
            if self._no_more_requests_until < datetime.datetime.utcnow():
                return None
            self._no_more_requests_until = None
        r = None
        if post_data:
            raise NotImplementedError("GithubAPI Post unimplemented")
            return
        else:
            if self.credentials:
                r = requests.get(url, params=params, headers={ "Authorization":self.credentials.authorizationHeaderValue() })
            else:
                r = requests.get(url, params=params)
        if r.headers.get('x-ratelimit-remaining'):
            remaining_requests = int(r.headers['x-ratelimit-remaining'])
            if (remaining_requests == 0):
                logger.warning("Github API hit the rate limiter")
                self._no_more_requests_until = datetime.datetime.fromtimestamp(float(r.headers.get('x-ratelimit-reset')));
                return None
        if(r.ok):
            results = r.json()
            return results
        logger.warning("Github fetch of %s failed\n%s\n",r.url,r.text)
        return None

    def fetch_raw(self, url):
        if self._no_more_requests_until:
            if self._no_more_requests_until < datetime.datetime.utcnow():
                return None
            self._no_more_requests_until = None
        r = None
        if self.credentials:
            r = requests.get(url, headers={ "Authorization":self.credentials.authorizationHeaderValue(),"Accept":"application/vnd.github.v3.raw" })
        else:
            r = requests.get(url)
        if r.headers.get('x-ratelimit-remaining'):
            remaining_requests = int(r.headers['x-ratelimit-remaining'])
            if (remaining_requests == 0):
                logger.warning("Github API hit the rate limiter")
                self._no_more_requests_until = datetime.datetime.fromtimestamp(float(r.headers.get('x-ratelimit-reset')));
                return None
        if(r.ok):
            results = r.text
            return results
        logger.warning("Github fetch of %s failed\n%s\n",r.url,r.text)
        return None

    def baseURL(self, org_name=None, repo_name=None):
        baseurl = 'https://%s' % (self.server)
        if repo_name is not None:
            baseurl += "/repos/%s/%s" % (org_name, repo_name)
        elif org_name is not None:
            baseurl += "/orgs/%s" % (org_name)
        return baseurl

if __name__ == "__main__":
    creds = Credentials("github")
    git = GithubAPI(GithubRepo('api.github.com', 'salesforce','providence'), creds)
    bugs = git.issues(params={"labels":"bug,security","state":"all","since":"2015-02-01T00:00:00Z"})
    import json
    print json.dumps(bugs, indent=2)
    if bugs:
        for bug in bugs:
            print bug["title"], bug["state"]
