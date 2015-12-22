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
Jira Bug Tracking System Interface
"""

__copyright__ = "2015 Salesforce.com, Inc"
__status__    = "Prototype"

import sys
import os.path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
import requests
import json

from bugsystems.jira.JiraAPI import JiraAPI
from bugsystems.base import Bug, BugSystem

from dateutil import parser
from dateutil import relativedelta
from datetime import datetime
from datetime import timedelta

__copyright__ = "2015 Salesforce.com, Inc"
__status__    = "Prototype"

class JiraBugSystem(BugSystem):
    def __init__(self, creds, server):
        super(JiraBugSystem, self).__init__(creds)
        self.creds = creds
        self.jira = JiraAPI(server, self.creds)

    def from_search_json(self, issue):
        pass

    def query_bugs(self, query):
        bugs = []
        def __api_call(offset=None):
            query_results = self.jira.jql(query, offset)
            if query_results:
                issues = query_results["issues"]
                for issue in issues:
                    bug = self.from_search_json(issue)
                    bugs.append(bug)
            try:
                starts_at = query_results.get("startAt")
                max_results = query_results.get("maxResults")
                total = query_results.get("total")
                ends_at = int(starts_at) + int(max_results)
                if ends_at < int(total):
                    __api_call(offset=ends_at)
            except TypeError:
                pass

        __api_call();
        return bugs
