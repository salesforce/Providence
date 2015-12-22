'''
Copyright (c) 2015, Salesforce.com, Inc.
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

* Neither the name of Salesforce.com nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

import unittest
import os

from repos.base import RepoPatch, RepoCommit
from repos.diffparser import DiffParser

import json
from detection.pattern.regex_rule_engine import RepoPatchRegexRuleEngine

class RegexRuleEngineTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_config_one(self):
        testDiff = '''@@ -25,11 +25,15 @@
 ################################################################################
+Test exec abc
-Removed This Line
'''
        diff = DiffParser(testDiff)

        test_commit = RepoCommit(url="http://www.example.com/commit/1")
        test_patch = RepoPatch(repo_commit=test_commit, diff=diff)

        filename = os.path.join(os.path.dirname(__file__),"config_one.json")
        rule_engine = RepoPatchRegexRuleEngine(json.load(open(filename)), test_mode=True)
        rule_engine.process(test_patch)

