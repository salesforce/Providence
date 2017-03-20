Empire
==========
Common API Libraries and libraries related to acquisition systems


## Requirements
    python2.7

## Setup
The following is only necessary if using Empire separate from Providence. The Providence setup will also set up Empire. 

### 1. OS X Prerequisites
* Homebrew (http://brew.sh)
* XCode (once installed, open up and accept license)
* Xcode Command Line Tools (from Terminal.app)
    xcode-select --install

### 2. Install the VirtualEnv in your Empire Directory & Install Dependencies
#### Linux
    sudo apt-get install python-pip python-virtualenv

#### OS X
    sudo easy_install virtualenv

#### Confiuration On All Systems
You may need to follow the instructions here for the cryptography module in the next steps: https://cryptography.io/en/latest/installation/

On OSX the install will fail without the proper environmental variables being set.

#### All Systems
    virtualenv venv
    source venv/bin/activate
    pip install -r requirements.txt

If you need to deactivate the virtualenv just type `deactivate`

### 3. Generate a Credentials Key
```
dd if=/dev/urandom bs=32 count=1 2>/dev/null | openssl base64
```
This key can be stored in the environmental variable $CREDENTIAL_KEY or entered when Providence is first run. It's highly 
recommended you don't keep the key on the same server as the credentials.json file, and use something like LastPass for 
keeping it safe.

### 4. Entering Credentials
When you start up Providence it will ask you for credentials that aren't found, or you can edit the credentials.json file yourself (useful if one github account works for several repositories).

You can encrypt a passwords using the command:
```
python Empire/creds/encrypt-cred.py
```

copy example_credentials.json to credentials.json and update it as needed:
```json
{
   "github": {
        "type":"password",
        "username":"myusername",
        "password":"plaintext-password or fernet-encrypted password"
    }
}
```
