import ansible_runner

def run_playbook(playbook, inventory, user, password=None):
    extravars = {"ansible_user": user}

    if password:
        extravars["ansible_password"] = password
        extravars["ansible_become_password"] = password

    result = ansible_runner.run(
        playbook=playbook,
        inventory=inventory,
        extravars=extravars
    )

    return {
        "status": result.status,
        "rc": result.rc,
        "stdout": result.stdout.read() if result.stdout else "",
        "stderr": result.stderr.read() if result.stderr else ""
    }
