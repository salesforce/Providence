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
sys.path.append(
	os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from plugins.forcedotcom_base_watcher import ForceDotComBasePlugin
import logging
import config
import re
from lxml import etree
import tempfile
import subprocess

logger = logging.getLogger(__name__)
class Plugin(ForceDotComBasePlugin):
	EMAIL_SUBJECT = "PMD rule '%s' triggered"
	pmd_path = ""

	def __init__(self):
		super(Plugin, self).__init__("", "", self, logger)
		self.pmd_path = self.configuration.get("pmd_path")
		if not self.pmd_path:
			logger.error("pmd_path not defined in config.json")

	def patch(self, repository_name, repo_patch):
		filename = repo_patch.filename
		# CLS_SOURCE_FILE_PATTERN = "\.(cls|apex)$"
		if re.search(ForceDotComBasePlugin.CLS_SOURCE_FILE_PATTERN, filename):
			logger.debug("filename %s processing...", (filename))
			file_content = repo_patch.repo_commit.repo_source.retrieve_file(filename)
			if file_content == '' or file_content is None:
				logger.error("%s repo probably did not implement retrieve_file()", repository_name)
				return
			# pmd-apex throws parsing error on anything other than .cls, so force .cls file extension
			temp = tempfile.NamedTemporaryFile(mode='w+t', suffix='.cls')
			pmd_output = None
			try:
				temp.write(file_content.encode('utf-8'))
				temp.seek(0)
				pmd_output = self.run_pmd(temp.name)
			except Exception as e: 
				logger.exception("Error in salesforce_perforce_pmd %s", e)
			finally:
				temp.close()

			if pmd_output is not None:
				logger.debug("pmd found violations in %s", filename)
				lines = file_content.splitlines()
				pmd_xml = etree.fromstring(pmd_output)
				for v in pmd_xml.findall(".//violation"):
					begin_line = int(v.get("beginline")) - 1
					# only send alert if pmd results match change additions
					if lines[begin_line] in repo_patch.diff.additions:
						rule = v.get("rule")
						link = v.get("externalInfoUrl")
						info = v.text
						alert_msg = '<br /><br />LINE NUMBERS<br />' + v.get("beginline") + ' - ' + v.get("endline") +\
						'<br /><br /><a href="' + link + '">RULE INFO</a><br />' + info
						super(Plugin, self).send_alert(repo_patch, repo_patch.repo_commit, self.EMAIL_SUBJECT % rule, lines[begin_line], alert_msg)

	def run_pmd(self, file):
	# returns the raw pmd output as string
		try:
			results = subprocess.check_output([self.pmd_path, "pmd", "-R", "apex-security", "-l", "apex", "-f", "xml", "-d", file])
		except subprocess.CalledProcessError as e:
			# pmd exits with 4 if violations are found 
			if e.returncode == 4:
				return e.output
			else:
				logger.exception("Error executing pmd with code %s", e.returncode)
		return None

if __name__ == "__main__":
	pass