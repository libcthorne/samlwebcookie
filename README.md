# SAML Web Cookie

This utility allows you to authenticate using **Azure AD SAML** and
2FA from the command line and then connect to your VPN using
OpenConnect.

## Setup and usage

Start by installing OpenConnect if you don't have it already. ([Ubuntu instructions](https://grepitout.com/install-openconnect-ubuntu-vpn-client/))

### Using pip

To install `samlwebcookie`:
```
pip install samlwebcookie
```

To run `samlwebcookie` and pass the result to `openconnect` (after filling in your server, username, and password):
```
VPN_SERVER="vpn.company.org"
VPN_USERNAME="username"
VPN_PASSWORD="password"
export SWC_OUTPUT_FILE=<(:) && samlwebcookie $VPN_SERVER --username="$VPN_USERNAME" --password="$VPN_PASSWORD" --output-file=$SWC_OUTPUT_FILE && . $SWC_OUTPUT_FILE && sudo openconnect $SWC_SERVER --cookie=$SWC_COOKIE
```

Example output:
```
Waiting for 2FA code prompt...
Verification code: 123456
Got VPN cookie:
AAAAAAABBABABABAB@@AAAEXAMPLECOOKLIEPLEASEIGNORETHIOSVALYEHERE
[sudo] password for user:
Attempting to connect to server 111.111.111.11:443
Connected to 111.111.111.11:443
```

### Using Docker

#### 1. Clone this code and build the container

```bash
git clone git@github.com:libcthorne/samlwebcookie.git
cd samlwebcookie
docker build -t samlwebcookie .
```

#### 2. Create the .env file with the local config

```
VPN_SERVER=vpn.company.org
VPN_USERNAME=username@company.org
VPN_PASSWORD=password
```

#### 3. Run connect.sh

The `connect.sh` script will first ask you for your VPN password, then your 2FA verification code, and finally it will ask you to `sudo` - do not be alarmed when it prompts you for these.

Once connected, the `openconnect` command will remain running.

```bash
./connect.sh
```

You should see output similar to:

```
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
