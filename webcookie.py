import os
import sys
import time
import urllib3
from pprint import pprint

import requests
from bs4 import BeautifulSoup
from requests_ntlm import HttpNtlmAuth

SAML_HOST = os.environ['SAML_HOST']
if not SAML_HOST:
    print("Missing SAML_HOST")

FS_AUTH_HOST = os.environ['FS_AUTH_HOST']
if not FS_AUTH_HOST:
    print("Missing FS_AUTH_HOST")

VPN_HOST = os.environ['VPN_HOST']
if not VPN_HOST:
    print("Missing VPN_HOST")

VPN_USERNAME = os.environ['VPN_USERNAME']
if not VPN_USERNAME:
    print("Missing VPN_USERNAME")

VPN_PASSWORD = os.environ['VPN_PASSWORD']
if not VPN_PASSWORD:
    print("Missing VPN_PASSWORD")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

s = requests.Session()

r = s.post(
    url='https://{}/+CSCOE+/saml/sp/login'.format(SAML_HOST),
    headers={
        "Host": SAML_HOST,
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:65.0) Gecko/20100101 Firefox/65.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://{}/+CSCOE+/logon.html".format(SAML_HOST),
        "Content-Type": "application/x-www-form-urlencoded",
        "DNT": "1",
        "Connection": "keep-alive",
        "Cookie": "webvpnlogin=1; webvpnLang=en",
        "Upgrade-Insecure-Requests": "1",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    },
    data="tgroup=&next=&tgcookieset=&group_list=SAML&Login=Login",
    verify=False,
    allow_redirects=False,
)

r = s.get(
    url=r.headers['Location'],
    headers={
        "Host": FS_AUTH_HOST,
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:65.0) Gecko/20100101 Firefox/65.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://{}/".format(SAML_HOST),
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    },
    verify=False,
    allow_redirects=False,
)
if r.status_code == 302:
    # When the server detects an existing session, it prompts for
    # confirmation of username and password using NTLM auth
    print("Existing session found")
    login_url = r.headers['Location']
    r = s.get(
        url=login_url,
        headers={
            "Host": FS_AUTH_HOST,
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:74.0) Gecko/20100101 Firefox/74.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-GB,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://{}".format(VPN_HOST),
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        },
        verify=False,
        allow_redirects=False,
        auth=HttpNtlmAuth(VPN_USERNAME, VPN_PASSWORD),
    )
else:
    soup = BeautifulSoup(r.text, 'html.parser')
    login_form = soup.find('form', id='loginForm')
    if not login_form:
        raise Exception("Failed to find #loginForm")
    login_url = 'https://{}{}'.format(FS_AUTH_HOST, login_form.attrs['action'])

    r = s.post(
        login_url,
        data={
            'UserName': '{}'.format(VPN_USERNAME),
            'Password': '{}'.format(VPN_PASSWORD),
        },
    )

while True:
    soup = BeautifulSoup(r.text, 'html.parser')
    error_field = soup.find('label', {'id': 'errorText'}) or soup.find('span', {'id': 'errorText'})
    if error_field and error_field.text:
        print(error_field.text)
        print("=" * 80)
        sys.exit(1)

    if not 'Multi-Factor Authentication' in soup.title:
        break

    mfa_form = soup.find('form', {'id': 'loginForm'})
    context = mfa_form.find('input', {'id': 'context'}).attrs['value']
    code_input = soup.find('input', {'id': 'verificationCodeInput'})
    if not code_input:
        print("Waiting for 2FA code prompt...")
        time.sleep(1)
        r = s.post(
            login_url,
            data={
                'AuthMethod': 'AzureMfaAuthentication',
                'Context': '{}'.format(context),
                '__EVENTTARGET': '',
            },
            verify=False,
            allow_redirects=False,
            auth=HttpNtlmAuth(VPN_USERNAME, VPN_PASSWORD),
        )
        continue

    verification_code = input("Verification code: ")

    r = s.post(
        login_url,
        headers={
            "Host": FS_AUTH_HOST,
            "Referer": login_url,
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:65.0) Gecko/20100101 Firefox/65.0",
        },
        data={
            'AuthMethod': 'AzureMfaAuthentication',
            'Context': '{}'.format(context),
            '__EVENTTARGET': '',
            'SignIn': 'Sign+in',
            'VerificationCode': verification_code,
        },
        auth=HttpNtlmAuth(VPN_USERNAME, VPN_PASSWORD),
    )
    soup = BeautifulSoup(r.text, 'html.parser')
    error_field = soup.find('label', {'id': 'errorText'}) or soup.find('span', {'id': 'errorText'})
    if error_field and error_field.text:
        print(error_field.text)
        print("=" * 80)
        sys.exit(1)
    else:
        # Code accepted
        break

vpn_form = soup.find("form", {'name': 'hiddenform'})
if not vpn_form:
    print("Login failed for unknown reason:")
    print(soup)
    print("=" * 80)
    sys.exit(1)
vpn_url = vpn_form.attrs['action']
saml_response = vpn_form.find('input').attrs['value']

r = s.post(
    '{}'.format(vpn_url),
    data={
        'SAMLResponse': saml_response,
    },
    verify=False,
)
soup = BeautifulSoup(r.text, 'html.parser')
saml_form = soup.find("form") # name='samlform'
saml_url = saml_form.attrs['action']
saml_response = saml_form.find('input', {'name': 'SAMLResponse'}).attrs['value']

r = s.post(
    'https://{}{}'.format(VPN_HOST, saml_url),
    data={
        'tgroup': '',
        'next': '',
        'tgcookieset': '',
        'group_list': 'SAML',
        'username': '',
        'password': '',
        'SAMLResponse': saml_response,
        'Login': 'Login',
    },
    headers={
        "Cookie": "webvpnlogin=1",
    },
    verify=False,
)
print("Got VPN cookie:")
print(s.cookies['webvpn'])
