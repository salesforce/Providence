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
import json
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from detection.pattern.regexruleengine import RegexRuleEngine
from Empire.creds.credentials import Credentials
from plugins import base, RepoWatcher
import logging
import config
import re
from alerts.email_alert import EmailAlert
from alerts import Alert
from Empire.creds import CredentialManager
import settings

logger = logging.getLogger(__name__)
class Plugin(base.Plugin):
# Example of a watcher plugin. Implements the four required methods as described in readme

    # basic configurations
    configuration = config.Configuration('config.json')
    EMAIL_ALERT_RECIPIENTS = configuration.get(('email', 'to'))

    # some regex filename constants
    JAVA_SOURCE_FILE_PATTERN = "\.java$"
    JS_SOURCE_FILE_PATTERN = "\.js$"

    # anchor for last repo commit
    last_alert = None

    def register_watcher(self):
    # hooks each repository listed in config.json to the main process in providence.py
        repo_watchers = []
        for repo in self.configuration.get('repos'):

            repo_type = repo.get('type')

            if repo_type == 'perforce':
                repo_type = RepoWatcher.PERFORCE
            elif repo_type == 'github':
                repo_type = RepoWatcher.GITHUB
            else:
                logger.warning('Repo Type \'%s\' not supported yet', repo_type)
                repo_type = RepoWatcher.ALL

            repo_watchers.append(RepoWatcher(self, repo_type, repo.get('name')))

        return repo_watchers

    def commit_started(self, repository_name, repo_commit):
    # method called when Providence begins the commit processing
        logger.debug("processing repo %s on commit %s", repository_name, repo_commit.identifier)

    def patch(self, repository_name, repo_patch):
    # method called during the commit processing. Defines when an alert should be sent
        if re.search(self.JAVA_SOURCE_FILE_PATTERN, repo_patch.filename):
            regex_file_path = os.path.join(os.path.dirname(__file__),"java.json")
        else:
            regex_file_path = os.path.join(os.path.dirname(__file__),"js.json")
        logger.debug("filename %s processed", (repo_patch.filename))
        all_lines = []
        all_lines.extend(repo_patch.diff.additions)
        rule_engine = RegexRuleEngine(json.load(open(regex_file_path)))

        def custom_match_callback(alert_config, alert_action, repo_patch, all_lines, offending_line):
        # method called when the commit matches a regex rule. The actual sending of alerts (via email or bug tracking system) goes here
            self.send_alert(repo_patch, repo_patch.repo_commit, alert_action.get("subject"), offending_line)

        # Each line in the commit goes through the rule engine. If the line matches a regex rule, custom_match_callback() is called
        rule_engine.match(all_lines, repo_patch, custom_match_callback=custom_match_callback)
        return

    def commit_finished(self, repository_name, repo_commit):
        # method called when Providence finishes the commit processing
        pass

    def simple_html_encode(self, string):
        return string.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')

    def send_alert(self, repo_patch, repo_commit, subject, offending_line):
        # Example method for sending alert whenever a rule is matched. 
        url = repo_commit.url;
        filename = 'NOFILE'
        if repo_patch != None:
            filename = repo_patch.filename
        subject = "[Providence Email Alert] - " + subject + ' in ' + repo_commit.identifier

        # skip if the alert is duplicate
        if url + filename + subject + offending_line == Plugin.last_alert:
            return

        # remember the current alert
        Plugin.last_alert = url + filename + subject + offending_line

        message = '<a href="' + url + '">' + url + '</a>'+\
        '<br/><br/>OFFENDING LINE<br/>' + self.simple_html_encode(offending_line) +\
        '<br/><br/>FILE NAME<br/>' + filename

        # email alert
        alert = Alert(message='', message_html=message, subject=subject, level=Alert.HIGH)
        email_recipients = [self.EMAIL_ALERT_RECIPIENTS]
        EmailAlert().send(alert, to_email=email_recipients)


    def test(self, verbose=True):
        # Don't test non-regex based plugins
        if self.regex_file_path == "":
            return
        rule_engine = RegexRuleEngine()
        rule_engine.load_config(json.load(open(self.regex_file_path)))
        (success, results) = rule_engine.test()
        if verbose == True:
            logger.debug( results )
        if success == False:
            raise base.PluginTestError(results)

if __name__ == "__main__":
    test();
