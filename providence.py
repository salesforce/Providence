'''
Copyright (c) 2015, Salesforce.com, Inc.
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

* Neither the name of Salesforce.com nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

#-- Load libraries
import datetime
import imp
import os, sys
import getpass
import json
import pytz
import logging
import argparse

from uuid import uuid4
from apscheduler.scheduler import Scheduler
from alerts import Alert
from Empire.creds import CredentialManager
#-- Load configuration
#-- This method may change in the future
import config
#-- remember command line settings
import settings

def set_global_config():
    configuration = config.Configuration('config.json')
    config.providence_configuration = configuration
    return configuration

def set_logging_from_configuration(configuration):
    #-- Setup Logging
    logging.basicConfig(filename=configuration.get(('logging','filename')),
                        filemode='w',
                        level=logging.DEBUG if configuration.get(('logging','loglevel')) == 'debug' else logging.INFO,
                        format=configuration.get(('logging','stringfmt')), 
                        datefmt=configuration.get(('logging','datefmt')))
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter(configuration.get(('logging','formatter')))
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

if __name__ == "__main__":
    configuration = set_global_config()
    set_logging_from_configuration(configuration)
    logger = logging.getLogger(__name__)


    parser = argparse.ArgumentParser(description='Providence Monitor Framework')
    parser.add_argument('--tests','-t', action='store_true')
    parser.add_argument('--mode', help="specify production for production mode, or anything otherwise")
    parser.add_argument('--p4change', help="specify the p4 change number to debug")
    args = parser.parse_args()

    settings.init(args.mode, args.p4change)

    #-- Basic Credentials setup
    credentials_file = configuration.get('credentials_file')
    credential_key = os.environ.get('CREDENTIAL_KEY')
    if credential_key is None:
        credential_key = getpass.getpass('Credential Key:')
    credential_manager = CredentialManager(credentials_file, credential_key)
    config.credential_manager = credential_manager

    ## -- test just resets the db everytime --
    from models import Base
    from db import engine
    if not settings.in_production():
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    from repos import repotracker
    from plugins import RepoWatcher, Plugins
    from plugins.base import PluginTestError

#-- Load plugins
    loaded_plugins = Plugins(configuration)

    if args.tests:
        print "=======================  Loading plugins ======================="
        plugins = loaded_plugins.enabled_plugins()

        print "=======================  Running Plugin Tests ======================="
        for plugin_area in plugins:
            for plugin in plugins[plugin_area]:
                print "Running test for ", plugin.__module__
                try:
                    plugin.test()
                except PluginTestError, pte:
                    print "Test Failed for ", plugin.__module__
                    print pte.message
                    sys.exit(1)
        print "=======================  Tests Successful ======================="
        sys.exit(0)

#-- Setup RepoTracker plugin
    #tracker = RepoTracker(config);
    #new_datetime = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
    #new_datetime -= datetime.timedelta(hours=1)
    #tracker.new_date("github-relateiq/riq",new_datetime)
    #print "Setting to ", new_datetime
    
    def run_watchers():
        #hipalert.send(Alert("Running watchers", level=Alert.DEBUG))
        logger.info("Running watchers")

        plugins = loaded_plugins.enabled_plugins()

        repositories = loaded_plugins.get_repositories(plugins["repositories"])        
        watchers = loaded_plugins.get_watchers(plugins["watchers"])
        tracker = repotracker.RepoTracker();
        tracker.update_identifier("github-Pardot/pardot::", str(datetime.datetime.utcnow().replace(tzinfo=pytz.UTC) - datetime.timedelta(hours = 48)))

        for repository_name, repository_data in repositories.items():
            repository_watchers_by_path = watchers.get(repository_name)
            if repository_watchers_by_path is None:
                continue
            for repository_path, repo_watchers in repository_watchers_by_path.items():
                repository_db_identifier = repository_name
                if repository_path is not None:
                    repository_db_identifier += "::" + repository_path
                def commit_started_callback(repo_commit):
                    if repo_watchers:
                        for repo_watcher in repo_watchers:
                            plugin = repo_watcher.plugin
                            if hasattr(plugin, 'commit_started'):
                                plugin.commit_started(repository_name, repo_commit)
                def commit_finished_callback(repo_commit):
                    if repo_watchers:
                        for repo_watcher in repo_watchers:
                            plugin = repo_watcher.plugin
                            if hasattr(plugin, 'commit_finished'):
                                plugin.commit_finished(repository_name, repo_commit)
                    if repo_commit.identifier:
                        new_identifier = repo_commit.identifier
                        tracker.update_identifier(repository_db_identifier, new_identifier)
                def patch_callback(repo_patch):
                    if repo_watchers:
                        for repo_watcher in repo_watchers:
                            plugin = repo_watcher.plugin
                            if hasattr(plugin, 'patch'):
                                plugin.patch(repository_name, repo_patch)

                last_run_completed = tracker.last_run_completed(repository_db_identifier)
                if repository_data.get("check-every-x-minutes"):
                    now = datetime.datetime.utcnow()
                    if last_run_completed:
                        if (now - last_run_completed) < datetime.timedelta(minutes=repository_data.get("check-every-x-minutes")):
                            #continue;
                            pass;
                try:
                    last_identifier = tracker.last_identifier(repository_db_identifier)
                    repository_data["source"].processSinceIdentifier(last_identifier, 
                                                                     commit_started_callback=commit_started_callback,
                                                                     patch_callback=patch_callback,
                                                                     commit_finished_callback=commit_finished_callback,
                                                                     path=repository_path);

                    tracker.update_last_run_completed(repository_db_identifier, datetime.datetime.utcnow())
                except Exception, e:
                    logger.exception("Exception running repository: %s" % (repository_db_identifier))

    def run_hourly():
        hour = datetime.datetime.now().hour
        # Current hour

        logger.info("Running hourly")
        plugins = loaded_plugins.enabled_plugins()

        hourly_plugins = plugins.get("hourly")
        for plugin in hourly_plugins:
            try:
                hour = 1
                plugin.run_hourly(hour)
            except Exception, e:
                logger.exception("Exception running hourly: %s" % (plugin))

    def run_seven_minutes():
        hour = datetime.datetime.now().hour
        # Current hour

        logger.info("Running 7 minutes")

        plugins = loaded_plugins.enabled_plugins()
        seven_minute_plugins = plugins.get("seven_minutes")

        for plugin in seven_minute_plugins:
            try:
                plugin.run_seven_minutes()
            except Exception, e:
                logger.exception("Exception running 7 minutes: %s" % (plugin))
    
    run_seven_minutes()
    run_watchers()
    run_hourly()

    sched = Scheduler(standalone=True)
    watcher_interval = "*/" + configuration.get(("cron", "watcher_interval"))
    sched.add_cron_job(run_watchers, minute=watcher_interval);
    #sched.add_cron_job(run_seven_minutes, minute="*/7");
    #sched.add_cron_job(run_hourly, hour="*", minute="5");
    try:
        sched.start()
    except (KeyboardInterrupt, SystemExit):
        pass
