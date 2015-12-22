'''
Copyright (c) 2015, Salesforce.com, Inc.
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

* Neither the name of Salesforce.com nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

import re
import cgi
import jinja2
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from alerts import Alert
from alerts.email_alert import EmailAlert

import config
import logging
logger = logging.getLogger(__name__)

class RegexRuleEngine(object):
    def __init__(self, config=None, test_mode=False):
        self.alert_queue = []
        if config is None:
            config={}
        self._alert_configs = None
        self._log_configs = None
        self._regexes = None
        self._rules = None
        self._tests = None
        self._name = None
        self._version = None

        self.load_config(config)
        self.test_mode = test_mode

    def load_config(self, config):
        if self._alert_configs is None:
            self._alert_configs = {}
        if self._log_configs is None:
            self._log_configs = []
        if self._rules is None:
            self._rules = []
        if self._regexes is None:
            self._regexes = {}
        if self._tests is None:
            self._tests = {}

        self._name = config.get("name",self._name)
        self._version = config.get("version",self._version)

        self._alert_configs.update(config.get("alert configs",[]))
        self._log_configs.extend(config.get("log configs",[]))

        self._regexes.update(config.get("regexes",{}))
        self._rules.extend(config.get("regex_rules",[]))

        self._tests.update(config.get("tests",{}))

    def _if_rule(self, data, rule, alert_callback):
        if_conditions = rule.get("if")
        then_rules = rule.get("then")
        else_rules = rule.get("else")

        if data is None or if_conditions is None:
            return

        if_condition_met = True
        for if_condition in if_conditions:
            if_condition = self._regexes.get(if_condition, if_condition)
            ignorecase = re.compile(if_condition, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if ignorecase.search(data) is None:
                if_condition_met = False
                break

        if if_condition_met:
            if then_rules is not None:
                for then_rule in then_rules:
                    self._process(data, then_rule, alert_callback)
        else:
            if else_rules is not None:
                for else_rule in else_rules:
                    self._process(data, else_rule, alert_callback)

    def _alert_rule(self, data, rule, alert_callback):
        alert_actions = rule.get("alert")
        for alert_action in alert_actions:
            if alert_callback:
                alert_callback(alert_action)

    def _process(self, data, rule, alert_callback): 
        if rule.get("if") is not None:
            self._if_rule(data, rule, alert_callback)
        if rule.get("alert"):
            self._alert_rule(data, rule, alert_callback)

    def process(self, data, alert_callback=None):
        for rule in self._rules:
            self._process(data, rule, alert_callback)

class RepoPatchRegexRuleEngine(RegexRuleEngine):
    def create_alert_email(self, subject, alert_message, repo_commit):
        alert_message = alert_message.decode("utf8")
        templateVars = { "title" : subject,
                         "description" : "Description",
                         "rule" : "Rule",
                         "github_link" : repo_commit.url,
                         "code" : alert_message }

        templateEnv = jinja2.Environment(autoescape=True,
            loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))

        #templateLoader = jinja2.FileSystemLoader( os.path.join(os.path.dirname(__file__)) )
        #templateEnv = jinja2.Environment( loader=templateLoader )

        html_template_file = os.path.join("ruleengine_github.html")
        text_template_file = os.path.join("ruleengine_github.txt")

        html_template = templateEnv.get_template( html_template_file )
        text_template = templateEnv.get_template( text_template_file )

        html = html_template.render( templateVars )
        text = text_template.render( templateVars )
        return (text, html)

    def process(self, repo_patch, alert_callback=None):
        data = u'\n'.join(repo_patch.diff.additions).encode('utf-8').strip()
        def _alert_callback(alert_action):
            alert_config_key = alert_action.get("alert config")
            alert_config = self._alert_configs.get(alert_config_key)
            if alert_config is None:
                logger.error("Alert config for [%s] is None", alert_config_key);
                return
            if alert_config.get("email"):
                default_email = config.Configuration('config.json').get(('email', 'to'))
                to_email = alert_config.get("email", default_email)
                patch_lines = u'\n'.join(repo_patch.diff.additions).encode('utf-8').strip()
                subject = alert_action.get("subject","Unknown Subject")
                (text, html) = self.create_alert_email(subject, data, repo_patch.repo_commit)
                ea = EmailAlert(Alert(subject=subject, 
                                      message=text.encode('utf-8'), 
                                      message_html=html.encode('utf-8')), 
                                to_email=to_email)
                if (self.test_mode == True):
                    print ea
                else:
                    ea.send()
            else:
                logger.warn("Alert type unknown %s" % (alert_config))

        if alert_callback is None:
            alert_callback = _alert_callback
        #data = repo_patch
        for rule in self._rules:
            self._process(data, rule, alert_callback)

