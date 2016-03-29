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
    git clone https://github.com/SalesforceEng/Providence --recursive
    cd Providence

###5. Install the VirtualEnv in your Providence Directory & Install Dependencies
####Linux
    sudo apt-get install python-pip python-virtualenv

####OS X
    sudo easy_install virtualenv
    brew install swig postgresql wget 

####Configuration On All Systems
You may need to follow the instructions here for the cryptography module in the next steps: https://cryptography.io/en/latest/installation/  On OSX the install will fail without the proper environmental variables being set.

####All Systems
    virtualenv venv
    source venv/bin/activate
    pip install -r requirements.txt
    pip install -r Empire/requirements.txt

If you need to deactivate the virtualenv just type `deactivate`

####If you would like to use Perforce monitoring
    (follow steps above, make sure you have run 'source venv/bin/activate')

Install p4 client (http://www.perforce.com/downloads)

Make a directory (vendor for example) and download and uncompress p4python api:
    http://www.perforce.com/downloads/Perforce/20-User?qt-perforce_downloads_step_3=7#product-54

Download and uncompress the C++ API (p4python is just an interface to this)
    http://cdist2.perforce.com/perforce/r14.2/bin.linux26x86_64/
    (http://www.perforce.com/downloads/Perforce/20-User?qt-perforce_downloads_step_3=7#product-49 may not work)

From the p4python uncompressed directory
(openssl lib dir is probably /usr/include/openssl)
```
python setup.py build --apidir <directory_of_uncompressed_cpp_api> --ssl <path_to_openssl_1_lib_dir>
python setup.py install --apidir <directory_of_uncompressed_cpp_api> --ssl <path_to_openssl_1_lib_dir>
```

###6. Generate a Credentials Key
```
dd if=/dev/urandom bs=32 count=1 2>/dev/null | openssl base64
```
This key can be stored in the environmental variable $CREDENTIAL_KEY or entered when Providence is first run. It's highly 
recommended you don't keep the key on the same server as the credentials.json file, and use something like LastPass for 
keeping it safe.

###7. Entering Credentials
When you start up Providence it will ask you for credentials that aren't found, or you can edit the credentials.json file yourself (useful if one github account works for several repositories).

####Or manually create the credentials file.

You can encrypt a passwords using the command:
```
python Empire/creds/encrypt-cred.py
```

copy credentials.json.example to credentials.json and update it as needed:
```json
{    
   "postgres-providence": {
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

###8. Adjust which plugins you want to run
Enable plugins in your new config.json file, several examples will be there.
Currently the 'plugins' directory contains a base plugin which has two example regex files:

1. `java.json`  will alert for possible instances of XXE in java
2. `js.json` contains warnings for risky JS coding

###9. Run Providence!
```
python providence.py
```


