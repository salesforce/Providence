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
JiraAPI - Sends JQL (Jira Query Language) requests to a Jira instance and returns the results
"""
import ssl

import requests
import json
import urllib
import os

__copyright__ = "2015 Salesforce.com, Inc"
__status__    = "Prototype"


class JiraAPI(object):
    def __init__(self, server, credentials):
        super(JiraAPI, self).__init__()
        self.server = server
        self.credentials = credentials
        self.verify = None
        __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        if (self.server == "jira.exacttarget.com:8443"):
            self.verify = os.path.join(__location__, 'et-jira-certs.pem')

    def fetchCommitDetails(self, url):
        r = requests.get(url, auth=self.auth(), verify=self.verify);
        if r.headers['x-ratelimit-remaining']:
            remaining_requests = int(r.headers['x-ratelimit-remaining'])
            if (remaining_requests == 0):
                self._no_more_requests_until = datetime.datetime.fromtimestamp(float(r.headers['x-ratelimit-reset']));
                #reset_time = long(r.headers['x-ratelimit-reset'])
                return None
        if(r.ok):
            return r.json()
        return None

    def jql(self, query, offset=None):
        verbose = False
        resource_name = "search"
        url = "https://%s/rest/api/latest/%s" % (self.server, urllib.quote(resource_name))
        params = {"jql":query}
        if offset is not None:
            params["startAt"] = offset
        r = requests.get(url, params=params, headers={ "Authorization":self.credentials.authorizationHeaderValue() }, verify=self.verify)
        if(r.ok):
            results = r.json()
            return results
        else:
            print "Request failed: ", r.status_code
            print r.text
        return None

if __name__ == '__main__':
    usercredentials_jsonfile = "bugsystems-Jira-usercreds.json"
    user_creds_data = open(usercredentials_jsonfile)
    user_creds = json.load(user_creds_data)
    user = user_creds["user"]
    password = user_creds["token"]
    server_url = 'https://pardot.atlassian.net'
    jira = JiraAPI(server_url, user, password)
    results = jira.jql('issuetype = Bug AND labels = trust AND status in (Accepted, "In Progress", Reopened, QA, "Needs Documentation", "On Hold", "QA Confirmed", Backlog, "Under Consideration", Investigation, "Define User Requirements", "Interaction Design", "Ready for Engineering", "UX Review", Done, "In Review", Blocked)')
