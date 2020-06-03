# SAML Web Cookie VPN Connect
 
### This utility allows you to authenticate using SAML and 2FA and then connect to your VPN using OpenConnect at the command line on Linux.

## Setup

### 1. Install the dependencies if you do not already have them

- Docker ([Download Page](https://www.docker.com/get-docker))
- OpenConnect (please use your package manager to install this)

### 2. Clone this code and build the container

```bash
git clone git@github.com:libcthorne/samlwebcookie.git
cd samlwebcookie
docker build -t samlwebcookie .
```

### 3. Create the .env file with the local config

```
SAML_HOST=saml.host.my.company
FS_AUTH_HOST=auth.host.my.company
VPN_HOST=the.vpn.my.company
VPN_USERNAME=my.username@my.company
```

## Usage

The `connect.sh` script will first ask you for your VPN password, then your 2FA verification code, and finally it will ask you to `sudo` - do not be alarmed when it prompts you for these.

Once connected, the `openconnect` command will remain running.

```bash
./connect.sh
```

You should see output similar to:

```
Please enter your VPN password: 
Running samlwebcookie
Waiting for 2FA code prompt...
Verification code: 999999
Got VPN cookie:
AAAAAAABBABABABAB@@AAAEXAMPLECOOKLIEPLEASEIGNORETHIOSVALYEHERE
[sudo] password for ubuntu:
Attempting to connect to server 111.111.111.11:443
Connected to 111.111.111.11:443
...
```

To disconnect from the VPN, simply hit Ctrl+C to terminate the `connect.sh` script.
