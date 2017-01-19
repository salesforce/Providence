Plugins
==========
Providence plugins live in this directory.

## Directory Structure
```
plugins
|── base_plugin
|   └── main.py
|── base_plugin_watcher
|	|── main.py
|	|── js.json
|	└── java.json
└── base.py
```

## Plugin Attributes
Plugins can contain the following attributes, and Providence will execute them as described. One plugin can include any number of the attributes, but the samples plugins here separates them for ease-of-maintenance. 

Plugins inherits the parent Plugin object from base.py and must define the method
```
test()
```

### Repository Registers
Repository registers sets up the code commit/bug systems for monitoring. It links each repository listed in config.json to its corresponding credential
and sets up the monitoring interval.

Must define the method
```
register_repositories()
```

### Watchers
Watchers contain the monitoring logic. Most plugins use regex to search for patterns in a commit. If match, send an alert. Watchers also contain the logic for sending the alerts. Their execution interval is defined as "watcher_interval" in config.json. 

Must define the methods
```
register_watcher()
commit_started()
patch()
commit_finished()
```

### Hourly/Seven minutes

Hourly and Seven Minute plugins run as often as their name states. These plugins are better suited for bug system instead of commit monitoring. 

Must have one of these defined
```
run_hourly()
run_seven_minutes()
```


## Sample Plugins
### base_plugin
Registers the Perforce and Github repos

### base_plugin_watcher
Look for potential vulnerabilities in .js and .java files

1. `java.json`  will alert for possible instances of XXE in java
2. `js.json` contains warnings for risky JS coding



