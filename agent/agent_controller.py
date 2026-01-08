from agent.task_parser import parse_task
from llm.playbook_generator import generate_playbook
from ansible.inventory_generator import generate_inventory
from ansible.runner import run_playbook
from security.secrets_manager import SecretsManager

secrets = SecretsManager()


def handle_request(text, credentials=None):
    parsed = parse_task(text)

    if credentials:
        secrets.set("user", credentials["ssh_user"])
        secrets.set("password", credentials.get("password"))
        secrets.set("sudo_password", credentials.get("sudo_password"))
        parsed["missing"] = []

    playbook = generate_playbook(parsed["intent"])
    if not playbook:
        return {"status": "failed", "error": "Playbook generation failed after retries"}

    inventory = generate_inventory(parsed["hosts"])

    dry_run = run_playbook(
        playbook,
        inventory,
        secrets.get("user"),
        secrets.get("password"),
        secrets.get("sudo_password"),
        check=True
    )

    if dry_run["rc"] != 0:
        return {"status": "failed", "dry_run": dry_run}

    execution = run_playbook(
        playbook,
        inventory,
        secrets.get("user"),
        secrets.get("password"),
        secrets.get("sudo_password"),
        check=False
    )

    secrets.clear()
    return {"status": "success", "execution": execution}
