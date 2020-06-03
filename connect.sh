#!/bin/bash

set -e

scriptDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check for and load the config
if [ ! -f "$scriptDir/.env" ]; then
  echo "Please create a .env file as described in the README.md"
  exit 1
fi
source "$scriptDir/.env"

# Read user's VPN password
echo -n "Please enter your VPN password: "
read -s VPN_PASSWORD

echo ""
echo "Running samlwebcookie"

# Get the SAML cookie
VPN_COOKIE=$(
  docker run -it --env-file "$scriptDir/.env" samlwebcookie |
  tee /dev/tty |
  tail -1
)

# Connect to the VPN
sudo openconnect -v "$VPN_HOST" --cookie="$VPN_COOKIE"
