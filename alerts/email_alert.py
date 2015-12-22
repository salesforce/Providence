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

import jinja2
import logging
import config
import os

logger = logging.getLogger('alert_email')

class EmailAlert(object):
    @staticmethod
    def email_templates(templateVars, textTemplateFilename, htmlTemplateFilename=None):
        templateLoader = jinja2.FileSystemLoader( searchpath="/" )
        templateEnv = jinja2.Environment( loader=templateLoader )

        text_template_file = os.path.join(os.path.dirname(__file__),textTemplateFilename)
        text_template = templateEnv.get_template( text_template_file )
        text = text_template.render( templateVars )

        html = None
        if htmlTemplateFilename is not None:
            html_template_file = os.path.join(os.path.dirname(__file__),htmlTemplateFilename)
            html_template = templateEnv.get_template( html_template_file )
            html = html_template.render( templateVars )

        return (text, html)

    def __init__(self, alert=None, creds=None):
        configuration = config.Configuration('config.json')

        self.server = configuration.get(('email', 'host'))
        self.to_email = configuration.get(('email', 'to'))
        self.from_email = self.to_email 
        self.creds=creds
        self.alert=alert

    def send(self, alert=None, to_email=None, from_email=None):
        if alert is None:
            alert = self.alert
        if to_email is None:
            to_email = self.to_email
        if from_email is None:
            from_email = self.from_email

        logger.debug("Preparing email to %s", to_email)

        if type(to_email) is not list:
            to_email = [to_email,]

        self.emails = ",".join(to_email)

        self.from_email = from_email
        self.subject = alert.subject
        self.text = alert.message
        self.html = alert.message_html

        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Providence Alert: " + self.subject
        msg['From'] = self.from_email
        msg['To'] = self.emails

        part1 = MIMEText(self.text, 'plain')
        msg.attach(part1)

        if self.html:
            part2 = MIMEText(self.html.encode('utf-8'), 'html', 'utf-8')
            msg.attach(part2)

        s = smtplib.SMTP(self.server)

        safe_to_email_addresses = []
        for email_address in to_email:
            break_up_email = re.match("^([\w\d\.-]+)(\+.*)?@(.*)", email_address)
            if break_up_email is None:
                logger.error("Email address [%s] could not be parsed",  str(email_address))
                return False
            if len(break_up_email.groups()) != 3:
                logger.error("Email address [%s] did not parse correctly",  str(email_address))
                return False
            safe_to_email = "@".join( (break_up_email.groups()[0], break_up_email.groups()[2]) )
            safe_to_email_addresses.append(safe_to_email)
        s.sendmail(from_email, safe_to_email_addresses, msg.as_string())
        logger.info("Email sent to [%s] with subject [%s]", msg['To'], msg['Subject'])
        s.quit()
        return True

if __name__ == "__main__":
    templateVars = { "title" : "Test Example 3",
                     "description" : "A simple inquiry of function.",
                     "rule" : "Rule test X",
                     "github_link" : "#",
                     "code" : "\n".join(["a","b","c"])
                   }
    (text, html) = EmailAlert.email_templates(templateVars, "templates/test_email.txt", "templates/test.html")
    EmailAlert().send(Alert(message=text, message_html=html), to_email=config.Configuration('config.json').get(('email', 'to')))

    
