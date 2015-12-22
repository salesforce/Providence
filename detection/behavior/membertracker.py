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
import os
from time import sleep
from models import Repo, RepoDocument
from db import Session, get_one_or_create
import config
import copy

class MemberTracker(object):
    def __init__(self, repository_name, new_members=True, odd_hours=False):
        self.session = Session();
        self.repository_name = repository_name;
        self.new_members = new_members;

    @classmethod
    def doc_name(cls, member_identifier):
        return "%s" % (member_identifier,)

    @classmethod
    def tool_name(cls):
        return "Detection::Behavior::Members"

    def check_if_new(self, member_identifier, add_if_new=True, alert_function=None):
        if member_identifier is None:
            return False
        name = MemberTracker.doc_name(member_identifier)
        tool = MemberTracker.tool_name()
        repo, did_add = get_one_or_create(self.session, Repo, name=self.repository_name)
        members_doc, did_add = get_one_or_create(self.session, RepoDocument, repo=repo, tool=tool, name=name)
        if did_add:
            members_doc.data = {}
            if alert_function:
                alert_function(member_identifier)
            self.session.commit()
            return True
        self.session.commit()
        return False
