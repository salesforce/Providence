'''
Copyright (c) 2015, Salesforce.com, Inc.
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

* Neither the name of Salesforce.com nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

import imp
import os
import sys
import importlib
import config
import logging

logger = logging.getLogger(__name__)

PluginFolder = "./plugins"
MainModule = "main"

path = "plugins/"

class Plugins(object):
    def __init__(self,configuration):
        self._pluginFolder      = configuration.get(('plugins','folder'), default="./plugins")
        self._mainModule        = configuration.get(('plugins','main_module'), default="main.py")
        self._pluginTypes       = configuration.get(('plugins','plugin_types'))
        self._registeredPlugins = {}
        self._found_plugins      = []
        _enabled_plugin_names = configuration.get(('plugins','enabled'), default=[{}])
        self._enabled_plugin_names = _enabled_plugin_names[0]

    def _findPlugins(self, enabled_dict):
        _found_plugins = []
        return _found_plugins

    def enabled_plugins(self):
        return self.all_plugins(self._enabled_plugin_names)

    def all_plugins(self, enabled_dict=None):
        plugins = {"repositories":[],
                   "watchers":[],
                   "hourly":[],
                   "seven_minutes":[] }
        possiblePlugins = os.listdir(self._pluginFolder)
        for possible_plugin in possiblePlugins:
            if not os.path.isdir(os.path.join(self._pluginFolder,possible_plugin)):
                continue
            location = os.path.join(self._pluginFolder,possible_plugin)
            for pluginFile in os.listdir(location):
                if pluginFile != self._mainModule:
                    continue
                plugin_path = location.split("/")
                plugin_name = plugin_path[-1]
                enabled = True
                if enabled_dict is not None:
                    enabled = enabled_dict.get(plugin_name, False)
                if enabled != True:
                    continue
                plugin_mod_name = location[2:]
                main = imp.load_source(plugin_mod_name,os.path.join(location,"main.py"))
                plugin = main.Plugin()
                if hasattr(plugin, 'test') == False:
                    print "test() function required for ", info
                    continue
                if hasattr(plugin, 'request_credentials'):
                    creds_requested = plugin.request_credentials()
                    if creds_requested is not None:
                        for cred_requested in creds_requested:
                            if type(cred_requested) is dict:
                                cred_name = cred_requested["name"]
                                cred_type = cred_requested["type"]
                                creds = config.credential_manager.get_or_create_credentials_for(cred_name, cred_type)
                                if creds is None:
                                    continue
                if hasattr(plugin, 'register_repositories'):
                    plugins["repositories"].append(plugin)
                if hasattr(plugin, 'register_watcher'):
                    plugins["watchers"].append(plugin)
                if hasattr(plugin, 'run_hourly'):
                    plugins["hourly"].append(plugin)
                if hasattr(plugin, 'run_seven_minutes'):
                    plugins["seven_minutes"].append(plugin)
        return plugins

    def get_repositories(self, repository_plugins, tests=False):
        repositories = {}
        for plugin in repository_plugins:
            try:
                if hasattr(plugin, 'register_repositories'):
                    plugin_repos = plugin.register_repositories();
                    repositories.update(plugin_repos);
            except Exception, e:
                logger.exception(e)
        return repositories

    def get_watchers(self, watcher_plugins, tests=False):
        watchers = {}
        wildcards = []
        for plugin in watcher_plugins:
            try:
                repo_watchers = plugin.register_watcher();
                for repo_watcher in repo_watchers:
                    if repo_watcher.repo_identifier == "*":
                        repo_watcher.path = None
                        wildcards.append(repo_watcher)
                        continue
                    ident = repo_watcher.repo_identifier
                    if watchers.get(ident):
                        watchers[ident].append(repo_watcher)
                    else:
                        watchers[ident] = [repo_watcher]
            except Exception, e:
                logger.exception(e)

        for repo_identifier, repo_watchers in watchers.iteritems():
            categorized_by_path =  RepoWatcher.categorize_by_path(repo_watchers)
            for path, path_watchers in categorized_by_path.iteritems():
                path_watchers.extend(wildcards)
            watchers[repo_identifier] = categorized_by_path
        return watchers


    def _validateSinglePlugin(self):
        pass

    def _loadSinglePlugin(self):
        pass


class RepoWatcher(object):
    ALL=0
    GITHUB=1
    PERFORCE=2
    STASH=3

    def __init__(self, plugin, repo_type, repo_identifier, path=None):
        self.plugin = plugin
        self.repo_type = repo_type
        self.repo_identifier = repo_identifier
        self.path = path
        self.start_time_utc = None
        self.end_time_utc = None
        self.owner = None
        self.subpaths = []

    def search_path(self):
        if self.repo_type == RepoWatcher.PERFORCE:
            return self.path + "..."
        return self.path


    @staticmethod
    def _list_loop(repo_watcher, repo_watchers):
        reduced_paths = [repo_watcher]
        while len(repo_watchers) > 0:
            nextpath = repo_watchers[-1].path
            if nextpath is None:
                nextpath = ""
            if repo_watcher.path is None and nextpath is not None:
                return reduced_paths  
            elif repo_watcher.path != nextpath:
                nextpath = nextpath + "/"
                prefix = repo_watcher.path + "/"
                if nextpath.startswith(prefix) == False:
                    return reduced_paths
            next_watcher = repo_watchers.pop()
            reduced_paths.append(next_watcher)
            #reduced_paths[path] =  list_loop(path, paths)
        return reduced_paths

    @staticmethod
    def categorize_by_path(repo_watchers):
        reduced_paths = {}
        repo_watchers.sort(key=lambda x: x.path, reverse=True)
        while len(repo_watchers) > 0:
            repo_watcher = repo_watchers.pop()
            if (repo_watcher.path is None):
                repo_watcher.path = ""
            reduced_paths[repo_watcher.path] = RepoWatcher._list_loop(repo_watcher, repo_watchers)
        return reduced_paths


if __name__ == "__main__":
    repo_watchers = []
    repo_watchers.append(RepoWatcher(None, RepoWatcher.GITHUB, "*","/a"))
    repo_watchers.append(RepoWatcher(None, RepoWatcher.GITHUB, "x","/a"))
    repo_watchers.append(RepoWatcher(None, RepoWatcher.GITHUB, "x","/b/c/d"))
    repo_watchers.append(RepoWatcher(None, RepoWatcher.GITHUB, "x","/b"))

    watchers = {}
    wildcards = []
    for repo_watcher in repo_watchers:
        if repo_watcher.repo_identifier == "*":
            repo_watcher.path = None
            wildcards.append(repo_watcher)
            continue
        ident = repo_watcher.repo_identifier
        if watchers.get(ident):
            watchers[ident].append(repo_watcher)
        else:
            watchers[ident] = [repo_watcher]

    for repo_identifier, repo_watchers in watchers.iteritems():
        print repo_identifier

        categorized_by_path =  RepoWatcher.categorize_by_path(repo_watchers)
        for path, path_watchers in categorized_by_path.iteritems():
            path_watchers.extend(wildcards)
        watchers[repo_identifier] = categorized_by_path

    print watchers

    """
    def list_loop(prefix, paths):
        reduced_paths = [prefix]
        while len(paths) > 0:
            if paths[-1].startswith(prefix) == False:
                return reduced_paths
            path = paths.pop()
            reduced_paths.append(path)
            #reduced_paths[path] =  list_loop(path, paths)
        return reduced_paths

    def reduce_paths(paths):
        reduced_paths = {}
        paths.sort(reverse=True)
        while len(paths) > 0:
            path = paths.pop()
            reduced_paths[path] = list_loop(path, paths)
        print reduced_paths

    paths = ['/a/b/c','/x/b','/a/b','/a/g','/a/g/d/e']            
    reduce_paths(paths)
    """
