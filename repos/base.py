'''
Copyright (c) 2015, Salesforce.com, Inc.
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

* Neither the name of Salesforce.com nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from alerts import Alert
from alerts.email_alert import EmailAlert

import cgi

class RepoSource(object):
    def __init__(self):
        pass

    def processSinceIdentifier(self, identifier, commit_callback, patch_callack):
        raise NotImplementedError("processSinceIdentifier was not defined")

    def processSinceDate(self, since_datetime, patch_callack):
        pass

    def processCommits(self, commits_json, commit_callback, patch_callack):
        pass

    def check_for_match(self, lines, search_re, ignore_case=True):
        all_lines = [u' '.join(lines).encode('utf-8').strip()] + lines
        ignorecase = re.compile(search_re, re.IGNORECASE | re.MULTILINE | re.DOTALL)
        for line in all_lines:
            if ignorecase.search(line):
                return True
        return False
    
    def retrieve_file(self, file_path):
        return ''

    def send_alert_email(self, from_email, to_email, subject, alert_message, repo_commit):
        # me == my email address
        # you == recipient's email address
        # Create the body of the message (a plain-text and an HTML version).
        url_html = ""
        if repo_commit and repo_commit.sha: #XXX: modify below to use config vars,
                                            #XXX: github.com/%s/%s/commit % (config.get('repos','github','owner'),...)
            url_html = "<A HREF='https://github.com/Pardot/pardot/commit/" + repo_commit.sha + "'>" + repo_commit.sha + "</A><br>"
        html = """
        <html>
          <head></head>
          <body>
            """ + url_html + """
            <pre><code>""" + cgi.escape(alert_message) + """
            </pre></code>
          </body>
        </html>
        """
        EmailAlert().send(Alert(subject=subject, message=body, message_html=html), to_email=to_email)

class RepoCommit(object):
    def __init__(self,
                 sha=None,
                 committer_email=None,
                 committer_name=None,
                 message=None,
                 url=None,
                 is_admin=None,
                 role=None,
                 repo_source=None,
                 patches=[]):
        self.identifier = None
        self.sha = sha
        self.committer_name = committer_name
        self.committer_email = committer_email
        self.message = message
        self.url = url
        self.is_admin = is_admin
        self.role = role
        self.repo_source = repo_source
        self.patches = patches

class RepoPatch:
    def __init__(self, 
                 repo_commit=None,
                 filename=None,
                 url=None,
                 diff=None,
                 lines_removed=None,
                 lines_added=None):
        self.repo_commit = repo_commit
        self.filename = filename
        self.url = url
        self.lines_added = lines_added
        self.lines_removed =lines_removed
        self.diff = diff
