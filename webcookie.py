#!/usr/bin/env python3
import argparse
import sys
import time
import urllib3

import requests
from bs4 import BeautifulSoup
from requests_ntlm import HttpNtlmAuth


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('vpn_server', type=str, help='VPN server to obtain cookie for, e.g. vpn.company.org')
    parser.add_argument('--username', required=True, type=str)
    parser.add_argument('--password', required=True, type=str)
    parser.add_argument('--output-file', required=True, type=str, help='path to file to write cookie and server address to for subsequent bash evaluation')

    args = parser.parse_args()

    vpn_server = args.vpn_server
    vpn_username = args.username
    vpn_password = args.password
    output_file = args.output_file

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    s = requests.Session()

    r = s.post(
        url=f"https://{vpn_server}/+CSCOE+/saml/sp/login",
        headers={
            "Host": vpn_server,
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:65.0) Gecko/20100101 Firefox/65.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-GB,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": f"https://{vpn_server}/+CSCOE+/logon.html",
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

    fs_auth_login_url = r.headers["Location"]
    fs_auth_host = fs_auth_login_url.split("/")[2]

    r = s.get(
        url=fs_auth_login_url,
        headers={
            "Host": fs_auth_host,
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:65.0) Gecko/20100101 Firefox/65.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-GB,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": f"https://{vpn_server}/",
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
                "Host": fs_auth_host,
                "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:74.0) Gecko/20100101 Firefox/74.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-GB,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Referer": f"https://{vpn_server}",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            },
            verify=False,
            allow_redirects=False,
            auth=HttpNtlmAuth(vpn_username, vpn_password),
        )
    else:
        soup = BeautifulSoup(r.text, 'html.parser')
        login_form = soup.find('form', id='loginForm')
        if not login_form:
            raise Exception("Failed to find #loginForm")
        login_url = f"https://{fs_auth_host}{login_form.attrs['action']}"

        r = s.post(
            login_url,
            data={
                'UserName': f'{vpn_username}',
                'Password': f'{vpn_password}',
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
                    'Context': context,
                    '__EVENTTARGET': '',
                },
                verify=False,
                allow_redirects=False,
                auth=HttpNtlmAuth(vpn_username, vpn_password),
            )
            continue

        verification_code = input("Verification code: ")

        r = s.post(
            login_url,
            headers={
                "Host": fs_auth_host,
                "Referer": login_url,
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:65.0) Gecko/20100101 Firefox/65.0",
            },
            data={
                'AuthMethod': 'AzureMfaAuthentication',
                'Context': context,
                '__EVENTTARGET': '',
                'SignIn': 'Sign+in',
                'VerificationCode': verification_code,
            },
            auth=HttpNtlmAuth(vpn_username, vpn_password),
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
        vpn_url,
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
        f'https://{vpn_server}{saml_url}',
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
    cookie = s.cookies['webvpn']
    print("Got VPN cookie:")
    print(cookie)

    with open(output_file, 'w') as output_fd:
        output_fd.write(f"SWC_SERVER={vpn_server}\n")
        output_fd.write(f"SWC_COOKIE={cookie}\n")


if __name__ == "__main__":
    main()
