# PMD plugin
This plugin uses a [fork](https://github.com/sgorbaty/pmd) of PMD to analyze Apex and Visualforce commits, and sends the resulting findings as Providence alerts. Since PMD is a source code analyzer, the findings here are generally more reliable than simple Regex matches provided by other plugins. Thanks to [Sergey Gorbaty](https://github.com/sgorbaty) for writing the Apex and Visualforce PMD rulesets.

## Requirements
    Java JRE 1.7+
    Maven

## Setup
### 1. Clone the Apex/VF ruleset PMD fork
    git clone git@github.com:sgorbaty/pmd.git
    
### 2. Checkout the `stable` branch
    cd pmd
    git checkout stable

### 3. Configure PMD Toolchains
See [How to Build PMD?](https://github.com/sgorbaty/pmd/blob/master/BUILDING.md)

### 4. Build PMD using Maven
from the pmd directory

    mvn clean package
    
### 5. Unzip PMD project
    cd pmd-dist/target
    unzip pmd-bin-5.6.0-SNAPSHOT.zip
    
### 6. Update your config.json to point to the PMD startup script
    "pmd_path": "/path/to/pmd/pmd-dist/target/pmd-bin-5.6.0-SNAPSHOT/bin/run.sh"
    
### 7. Enable the plugin!
    "plugins": {
        "enabled": [{
            ...
            "forcedotcom_pmd":true
        }]
    }
    
## About PMD

[**PMD**](https://pmd.github.io/) is a source code analyzer. It finds common programming flaws like unused variables, empty catch blocks,
unnecessary object creation, and so forth. It supports Java, JavaScript, Salesforce.com Apex, PLSQL, Apache Velocity,
XML, XSL.

Additionally it includes **CPD**, the copy-paste-detector. CPD finds duplicated code in
Java, C, C++, C#, Groovy, PHP, Ruby, Fortran, JavaScript, PLSQL, Apache Velocity, Scala, Objective C,
Salesforce.com Apex, Perl, Swift, Matlab, Python.

