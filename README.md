Providence
==========
Providence is a system for code commit & bug system monitoring. It is deployed within an organization to monitor code commits for security (or other) concerns, via customizable plugins. A plugin performs logic whenever a commit occurs.

##### Cool Stuff
* Build plugin to run a something everytime a commit happens
* `Empire` contains some useful tools for credential management
* Find our slides from our AppSec presentation [here](http://www.slideshare.net/salesforceeng/providence-rapid-vulnerability-prevention)

## Requirements
    python2.7
    postgresql 9.4+

##Steps: Local install with pip and virtualenv


###1. OS X Prerequisites
* Homebrew (http://brew.sh)
* XCode (once installed, open up and accept license)
* Xcode Command Line Tools (from Terminal.app)
    xcode-select --install

###2. Setup Postgresql on your server

###3. Setup the Database 
Create a database named 'providence'

###4. Checkout Providence and Submodules
    git clone https://github.com/Salesforce/Providence --recursive
    cd Providence

###5. Install the VirtualEnv in your Providence Directory & Install Dependencies
####Linux
    sudo apt-get install python-pip python-virtualenv

####OS X
    sudo easy_install virtualenv
    brew install swig postgresql wget 

####Configuration On All Systems
You may need to follow the instructions here for the cryptography module in the next steps: https://cryptography.io/en/latest/installation/
On OSX the install will fail without the proper environmental variables being set.

####All Systems
    virtualenv venv
    source venv/bin/activate
    pip install -r requirements.txt
    pip install -r Empire/requirements.txt

If you need to deactivate the virtualenv just type `deactivate`

####If you would like to use Perforce monitoring
    (follow steps above, make sure you have run 'source venv/bin/activate')
    pip install p4python

###6. Configuration
The config.json file contains the settings for which to run Providence with. 

Modify the postgresql server address and port if necessary, and set up the email and repos section with your information. 

`watcher_interval` sets the time in minutes between each scheduled processing.

###7. Adjust which plugins you want to run
Enable plugins in your new config.json file, several examples will be there.
Currently the 'plugins' directory contains a base plugin which has two example regex files:

1. `java.json`  will alert for possible instances of XXE in java
2. `js.json` contains warnings for risky JS coding

###8. Generate a Credentials Key
```
dd if=/dev/urandom bs=32 count=1 2>/dev/null | openssl base64
```
This key can be stored in the environmental variable $CREDENTIAL_KEY or entered when Providence is first run. It's highly 
recommended you don't keep the key on the same server as the credentials.json file, and use something like LastPass for 
keeping it safe.

###9. Entering Credentials
When you start up Providence it will try to connect to the repositories set up in config.json, and ask you for credentials that aren't found. Alternatively you can edit the credentials.json file yourself (useful if one github account works for several repositories).

####Manually create the credentials file.

You can encrypt a passwords using the command:
```
python Empire/creds/encrypt-cred.py
```

copy credentials.json.example to credentials.json and update it as needed:
```json
{    
   "plsqlcreds": {
        "type":"password",
        "username":"<username>",
        "password":"<password or fernet-encrypted password>"
   },
   "github": {
        "type":"password",
        "username":"<myusername>",
        "password":"<my password or fernet-encrypted password>"
    }
}
```

###10. Run Providence!
```
python providence.py
```


