#!/bin/bash

set -e

scriptDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
envFile="$scriptDir/.env"

# Check for and load the config
if [ ! -f "$envFile" ]; then
  echo "Please create a .env file as described in the README.md"
  exit 1
fi
source "$envFile"

# Read user's VPN password
if [ -z "$VPN_PASSWORD" ]; then
  echo -n "Please enter your VPN password: "
  read -s VPN_PASSWORD
  echo ""
fi

echo "Running samlwebcookie"

# Get the SAML cookie
VPN_COOKIE=$(
  docker run -it \
    --env VPN_PASSWORD=$VPN_PASSWORD \
    --env-file "$envFile" samlwebcookie | tee /dev/tty | tail -1
)

# Connect to the VPN
sudo openconnect $VPN_SERVER --cookie="$VPN_COOKIE"
