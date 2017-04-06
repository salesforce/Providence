Plugins
==========
Providence plugins live in this directory.

## Directory Structure
```
plugins
|── basic_plugin_register
|   └── main.py
|── basic_plugin_watcher
|	|── main.py
|	|── js.json
|	└── java.json
|── forcedotcom_base_watcher
|	└── __init__.py
|── forcedotcom_apex
|	|-- main.py
|	└── regex.json
|── other forcedotcom plugins
└── base.py
```

## Plugin Roles
Plugins can contain any of the following Roles, and Providence will execute them as described. One plugin can handle any number of Roles, but the sample plugins here separates them for ease-of-maintenance. 

Plugins inherits the parent Plugin object from base.py and must define the method
```
test()
```

### Repository Registers
Repository register plugins sets up the code commit/bug systems for monitoring. It links each repository listed in `config.json` to its corresponding credential
and sets up the monitoring interval.

Must define the method
```
register_repositories()
```

### Watchers
Watcher plugins are for monitoring commits. These plugins use regex rules to search for patterns in a commit, and sends an alert if there is a match. The alert logic (such as sending email or creating a new work in your favorite bug system) is also defined here. The plsql database keeps a timestamp of the last time commits were processed, and will pull commits since that timestamp every time it executes. You can specify the execution interval in "watcher_interval" in `config.json`

Must define the methods
```
register_watcher()
commit_started()
patch()
commit_finished()
```

### Hourly/Seven minutes

Hourly and Seven Minute plugins run as often as their name states. These plugins are better suited for bug system monitoring instead of commit monitoring. 

Must have one of these defined
```
run_hourly()
run_seven_minutes()
```


## Sample Plugins
### basic_plugin_register
Registers the Perforce and Github repos

### basic_plugin_watcher
Looks for potential vulnerabilities in .js and .java files

1. `java.json`  will alert for possible instances of XXE in java
2. `js.json` contains warnings for risky JS coding

### forcedotcom_base_watcher
Parent class of other forcedotcom watcher plugins. Contains the hooks (`register_watcher()`, `commit_started()` etc) for providence.py but does not have any actual rules. The child classes contain the actual regex and rules. You do not need to include this file in your `config.json`

This and the child forcedotcom plugins are a great way to monitor issues that we check for during the AppExchange security review.

### forcedotcom_apex
Looks for common security issues in Apex classes

### forcedotcom_aura_cmp_ui
Looks for common security issues on the UI side of Aura components

### forcedotcom_aura_js
Looks for common security issues on the controller/helper sides of Aura components

### forcedotcom_vf
Looks for issues on VisualForce and javascript pages

### forcedotcom_pmd
Looks for common security issues in Apex classes and Visualforce pages, using the source code analyzer [PMD](https://pmd.github.io/). PMD is run against each commit, and the resulting findings are sent out as Providence alerts. 
This plugin requires additional [setup](forcedotcom_pmd/README.md)



