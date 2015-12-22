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

class RegexRuleEngine(object):
    def __init__(self, config=None):
        if config is None:
            config={}
        self._alert_configs = config.get("alert configs",[]);
        self._log_configs = config.get("log configs",[]);
        self._rules = config.get("regex_rules",[])
        self._tests = config.get("tests",{})
        self._name = config.get("name","unknown")
        self._version = config.get("version",0)

    def load_config(self, config):
        if self._alert_configs is None:
            self._alert_configs = []
        if self._log_configs is None:
            self._log_configs = []
        if self._rules is None:
            self._rules = []
        if self._tests is None:
            self._tests = {}

        self._alert_configs += config.get("alert configs",[])
        self._log_configs += config.get("log configs",[])
        self._rules += config.get("regex_rules",[]) 
        self._tests.update(config.get("tests",{}))
        self._name = config.get("name",self._name)
        self._version = config.get("version",self._version)


    def send_alert_email(self, from_email, to_email, subject, alert_message, repo_commit):
        alert_message = alert_message.decode("utf8")
        templateVars = { "title" : subject,
                         "description" : "Description",
                         "rule" : "Rule",
                         "github_link" : repo_commit.url,
                         "code" : alert_message }

        templateLoader = jinja2.FileSystemLoader( searchpath="/" )
        templateEnv = jinja2.Environment( loader=templateLoader )

        html_template_file = os.path.join(os.path.dirname(__file__),"templates/ruleengine_github.html")
        text_template_file = os.path.join(os.path.dirname(__file__),"templates/ruleengine_github.txt")

        html_template = templateEnv.get_template( html_template_file )
        text_template = templateEnv.get_template( text_template_file )

        html = html_template.render( templateVars )
        text = text_template.render( templateVars )

        EmailAlert().send(Alert(subject=subject, message=text.encode('utf-8'), message_html=html.encode('utf-8')), to_email=to_email)

    def _process_ruleset(self, all_lines, repo_patch, ruleset, run_tests=False, custom_match_callback=None, offending_line=None):
        if_conditions = ruleset.get("if")
        return_actions = {"actions":[],"logs":[], "matches":[]}
        if if_conditions:
            for line in all_lines:
                if_condition_met = True
                matches = []
                for if_condition in if_conditions:
                    ignorecase = re.compile(if_condition, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                    if ignorecase.search(line) is None:
                        if_condition_met = False
                        break
                    matches.append(if_condition)
                if if_condition_met:
                    return_actions["matches"].extend(matches)
                    then_rulesets = ruleset.get("then")
                    if (then_rulesets):
                        for then_ruleset in then_rulesets:
                            sub_actions = self._process_ruleset(all_lines, repo_patch, then_ruleset, run_tests=run_tests, custom_match_callback=custom_match_callback, offending_line=line)
                            return_actions["actions"] += sub_actions["actions"]
                            return_actions["logs"] += sub_actions["logs"]
                            return_actions["matches"] += sub_actions["matches"]
                        break
            else_rulesets = ruleset.get("else")
            if (else_rulesets and if_condition_met == False):
                for else_ruleset in else_rulesets:
                    sub_actions += self._process_ruleset(all_lines, repo_patch, else_ruleset, run_tests=run_tests, custom_match_callback=custom_match_callback)
                    return_actions["actions"] += sub_actions["actions"]
                    return_actions["logs"] += sub_actions["logs"]
                    return_actions["matches"] += sub_actions["matches"]
            return return_actions
        alert_actions = ruleset.get("alert")
        if alert_actions:
            for alert_action in alert_actions:
                return_actions["actions"].append(alert_action)
                if (run_tests == True):
                    continue
                alert_config_key = alert_action.get("alert config")
                alert_config = self._alert_configs.get(alert_config_key)
                if alert_config is None:
                    logger.error("Alert config for [%s] is None", alert_config_key);
                    continue
                if alert_config.get("email"):
                    default_email = config.Configuration('config.json').get(('email', 'to'))
                    to = alert_config.get("email", default_email)
                    patch_lines = u'\n'.join(repo_patch.diff.additions).encode('utf-8').strip()
                    self.send_alert_email(default_email,
                                          to,
                                          alert_action.get("subject","Unknown Subject"),
                                          patch_lines,
                                          repo_patch.repo_commit);
                if alert_config.get("custom"):
                    if custom_match_callback:
                        custom_match_callback(alert_config, alert_action, repo_patch, all_lines=all_lines, offending_line=offending_line)
            return return_actions
        log_actions = ruleset.get("log")
        if log_actions:
            for log_action in log_actions:
                pass
        return return_actions

    def test(self):
        results = []
        results.append("************************* Rule Engine Test *****************************")
        results.append("Test suite for %s version %s" % (self._name, self._version));
        if self._tests is None:
            results.append("[ No tests found ]");
            return (False, "\n".join(results))
        fail_count = 0
        pass_count = 0
        for test,expected_result in self._tests.items():
            results.append("  %s..." % (test,));
            try: 
                result = {"actions":[],"logs":[],"matches":[]}
                for ruleset in self._rules:
                    sub_results = self._process_ruleset([test], None, ruleset, run_tests=True)
                    result["actions"] += sub_results["actions"]
                    result["logs"] += sub_results["logs"]
                    result["matches"] += sub_results["matches"]
                if (sorted(result['matches']) == sorted(expected_result)):
                    results.append("  ...passed");
                    pass_count += 1
                else:
                    results.append("  ...failed");
                    fail_count += 1
            except Exception as e:
                results.append("!exception! %s" % (str(e),));
        results.append("  passed: %d / failed: %d" % (pass_count, fail_count));
        results.append("************************************************************************");
        if fail_count > 0:
            return (False, "\r\n".join(results))
        return (True, "\n".join(results))

    def match(self, all_lines, repo_patch, custom_match_callback=None):
        action_sets = []
        for ruleset in self._rules:
            action_sets.append(self._process_ruleset(all_lines, repo_patch, ruleset, custom_match_callback=custom_match_callback))
