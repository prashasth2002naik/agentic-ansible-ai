import os
import subprocess


def run_playbook(playbook, inventory, user, password, sudo_password, check=False):
    cmd = [
        "ansible-playbook",
        playbook,
        "-i", inventory,
        "-u", user,
        "--become"
    ]

    if check:
        cmd.append("--check")

    env = os.environ.copy()

    if password:
        env["ANSIBLE_PASSWORD"] = password
        cmd += ["--extra-vars", f"ansible_password={password}"]

    if sudo_password:
        env["ANSIBLE_BECOME_PASS"] = sudo_password

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )

    stdout, stderr = process.communicate()

    return {
        "rc": process.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "dry_run": check
    }
