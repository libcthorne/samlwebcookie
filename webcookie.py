import os
import sys
import urllib3
from pprint import pprint

import requests
from bs4 import BeautifulSoup

SAML_HOST = os.environ['SAML_HOST']
FS_AUTH_HOST = os.environ['FS_AUTH_HOST']
VPN_HOST = os.environ['VPN_HOST']
USERNAME = os.environ['VPN_USERNAME']
PASSWORD = os.environ['VPN_PASSWORD']

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
)
soup = BeautifulSoup(r.text, 'html.parser')
login_form = soup.find('form', id='loginForm')
login_url = login_form.attrs['action']

r = s.post(
    'https://{}{}'.format(FS_AUTH_HOST, login_url),
    data={
        'UserName': '{}'.format(USERNAME),
        'Password': '{}'.format(PASSWORD),
    },
)
soup = BeautifulSoup(r.text, 'html.parser')
vpn_form = soup.find("form") # name='hiddenform'
vpn_url = vpn_form.attrs['action']
if 'https' not in vpn_url:
    error_message = "\<n".join(soup.find('span', {'id': 'errorText'}).contents)
    if error_message:
        print(error_message)
    else:
        print("Login failed")
    sys.exit(1)    
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
print(s.cookies['webvpn'])
