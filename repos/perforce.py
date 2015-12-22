'''
Copyright (c) 2015, Salesforce.com, Inc.
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

* Neither the name of Salesforce.com nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

from P4 import P4,P4Exception    # Import the module
import json
import datetime
import dateutil.parser
import urllib
import os
import pytz
import sys
import settings

from repos.base import RepoSource, RepoCommit, RepoPatch
from repos.diffparser import DiffParser
import logging
logger = logging.getLogger('repos_perforce')

class PerforceSource(RepoSource):
    def __init__(self, creds, port, directory):
        self._last_identifier = None
        self.creds = creds
        self.port = port
        self.directory = directory

    def initialize_client(self):
        p4 = P4()                        # Create the P4 instance
        p4.port = self.port
        p4.user = self.creds.username
        p4.password = self.creds.password
        return p4

    # Retrieve a single file from perforce
    def retrieve_file(self,file_path):
        p4 = self.initialize_client()
        try:
          p4.connect()
          # all lines have to be included because the file is split
          perforce_file = ''.join(p4.run("print", "-q", file_path)[1:])
          return perforce_file
        except P4Exception as pre:
            #logger.error(pre)
            for e in p4.errors:            # Display errors
                print e
        return None

    def processSinceIdentifier(self, identifier, commit_started_callback, patch_callback, commit_finished_callback, path):
        p4 = self.initialize_client()
        directory = self.directory

        try:                             # Catch exceptions with try/except
            max_patches = 1
            if settings.in_production():
                max_patches = 1000
            p4.connect()                   # Connect to the Perforce Server
            if identifier is None:
                # Get latest changenum in client mapping
                changes = p4.run("changes", "-s", "submitted", "-m", str(max_patches), self.directory)
                # empty repo
                if len(changes) <= 0:
                    return
                changenum = changes[len(changes)-1]['change']
                identifier = changenum
            else:
                identifier = str(long(identifier) + 1)
            # This is the default if there is no identifier

            #if identifier:
                #Todo, add a check here that it's a valid change
            #    search_for = "@%s" % (identifier)

            def process_patches(process_from_change_id, process_to_change_id=-1, patches_processed=0):
                if process_to_change_id == -1:
                    process_to = "#head"
                else:
                    process_to = "@" + str(process_to_change_id)
                changes = p4.run( 'changes', '-m','%s' %(max_patches),'%s@%s,%s' % (directory, process_from_change_id, process_to))
                changes = changes[::-1]
                if len(changes) == 0:
                    return patches_processed;
                earliest_change_id = changes[0].get("change")
                try:
                    if earliest_change_id is None or long(earliest_change_id) < long(process_from_change_id):
                        return patches_processed;
                    if changes[0]['change'] != process_from_change_id:
                        patches_processed = process_patches(process_from_change_id, str(long(earliest_change_id)-1), patches_processed)
                except:
                    pass

                logger.info("processing " + str(len(changes)) + " commit from " + process_from_change_id + " to " + process_to)
                for change in changes:
                    try:
                        if patches_processed >= max_patches:
                            return patches_processed
                        patches_processed += 1
                        change_id = change.get("change")
                        if change_id is None:
                            logger.log("Change id was none: " + directory + search_for)
                            continue
                        change_time = change.get('time')
                        change_datetime = datetime.datetime.utcfromtimestamp(long(change_time))

                        # option to debug a single commit
                        debug_change_id = settings.get_change_id()
                        if not settings.in_production() and debug_change_id:
                            change_id = debug_change_id
                        describes = p4.run( 'describe', change_id)
                        if describes is None or len(describes) < 1:
                            continue
                        describe = describes[0]
                        if isinstance(describe, basestring):
                            continue
                        user = describe.get("user")
                        description = describe.get("desc")
                        status = describe.get("status")
                        old_change_id = describe.get("oldChange")

                        files = describe.get("depotFile")
                        types = describe.get("type")
                        actions = describe.get("action")
                        digests = describe.get("digest")
                        revs = describe.get("rev")

                        perforce_commit = RepoCommit()
                        perforce_commit.sha = None
                        perforce_commit.identifier = change_id
                        perforce_commit.repo_source = self

                        perforce_commit.url = "http://www.example.com/?change=" + change_id
                        # get the real email of the user
                        email_address = p4.run('users', user)
                        if len(email_address) >= 1:
                            perforce_commit.committer_email = email_address[0].get('Email')

                        perforce_commit.date = change_datetime
                        perforce_commit.committer_login = user
                        perforce_commit.committer_name = user
                        perforce_commit.committer_type = 'user'
                        perforce_commit.files = files
                        perforce_commit.message = description
                        perforce_commit.username = user

                        commit_started_callback(perforce_commit)

                        if files is None:
                            #Todo: we should still record something here, behavioral
                            continue

                        logger.info("processing commit " + change_id + " in repo " + self.directory)
                        for i in range(len(files)):
                            filename = files[i]

                            # only check added and edited files
                            if "edit" not in actions[i] and "add" not in actions[i]:
                                continue

                            if old_change_id == None:
                                # fabricate a changelist if a new file is added. (because there is no previous file version to diff against)
                                file_string = self.retrieve_file(filename)
                                diff2 = file_string.split('\n')
                                diff2.insert(0, '') 
                                for i in range(len(diff2)):
                                    diff2[i] = '+ ' + diff2[i]
                            else:
                                diff2 = p4.run('diff2','-u',
                                         "%s@%s" % (filename, old_change_id),
                                         "%s@%s" % (filename, change_id),
                                         tagged=False);
                            # diff2 is an array now and well-formatted
                            # change diff2 to a string before passing to diffparser
                            if diff2 is not None and len(diff2) > 1:
                                diffstring = '\n'.join(diff2[1:])
                                diff = DiffParser(diffstring)
                                repo_patch = RepoPatch(repo_commit=perforce_commit)
                                repo_patch.diff = diff
                                repo_patch.filename = filename
                                patch_callback(repo_patch)

                        self._last_identifier = change_id
                        commit_finished_callback(perforce_commit)
                    except:
                        print "Unexpected error:", sys.exc_info()[0]
                return patches_processed
            patches_processed = process_patches(identifier)
            p4.disconnect()                # Disconnect from the Server
        except P4Exception as pre:
            logger.error(pre)
            for e in p4.errors:            # Display errors
                print e

        return None

if __name__ == "__main__":
    test = GithubSource();
    test.processRequetsSince("2014-03-14T12:00:00Z");
