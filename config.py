'''
Copyright (c) 2015, Salesforce.com, Inc.
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

* Neither the name of Salesforce.com nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

#-- Imports
import json
from lib.helpers import *

class Configuration(object):
  config_filename = "config.json"

  def __init__(self,configFile=None):
    if configFile is None:
      configFile = Configuration.config_filename
    self.__configFile = configFile 
    self.__load()

  def __load(self):
    with open(self.__configFile) as fp:
      self.__configData = json.load(fp, object_hook=convert)

  def get(self,keys,data=None,default=None):
    if type(keys) is tuple and len(keys) > 1:
      if not data:
        retData = self.get(keys[1:],self.__configData.get(keys[0]))
        if retData is None:
          return default
        return retData
      else:
        retData = self.get(keys[1:],data[keys[0]])
        if retData is None:
          return default
        return retData
    else:
      if type(keys) is str:
          retData = data.get(keys, default) if data else self.__configData.get(keys, default)
      else:
        retData = data.get(keys[0], default) if data else self.__configData.get(keys[0], default)
      if type(retData) is dict:
        raise Exception("Cannot return multiple entries")
      else:
        return retData 

  def set(self,keys,value,data=None):
    pass

  def persist(self):
    pass
      
credential_manager = None
