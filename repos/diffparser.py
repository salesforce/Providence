'''
Copyright (c) 2015, Salesforce.com, Inc.
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

* Neither the name of Salesforce.com nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

class DiffParser:
    def __init__(self, difftext):
        self.additions = []
        self.deletions = []
        self.after = []
        for line in difftext.splitlines():
            if len(line) > 0:
                    if line[0] == '+':
                        self.additions.append(line[1:])
                        self.after.append(line[1:])
                    elif line[0] == '-':
                        self.deletions.append(line[1:])
                    else:
                        self.after.append(line[1:])



if __name__ == "__main__":
    sampleDiff = '''
@@ -25,11 +25,15 @@
 ################################################################################
 
 import base64
+import sys
 
 import github.GithubObject
 import github.Repository
 
 
+atLeastPython3 = sys.hexversion >= 0x03000000
+
+
 class ContentFile(github.GithubObject.CompletableGithubObject):
     """
     This class represents ContentFiles as returned for example by http://developer.github.com/v3/todo
'''
    x = DiffParser(sampleDiff)
    print x.additions
    print x.deletions
