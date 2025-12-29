from agent.task_parser import parse_task
from agent.question_manager import get_questions
from llm.playbook_generator import generate_playbook
from ansible.inventory_generator import generate_inventory
from ansible.runner import run_playbook
from security.secrets_manager import SecretsManager

secrets = SecretsManager()

def handle_request(text, credentials=None):
    # 1. Parse user intent and hosts
    parsed = parse_task(text)

    # 2. Store credentials if provided
    if credentials:
        secrets.set("user", credentials["ssh_user"])
        secrets.set("password", credentials.get("password"))
        parsed["missing"] = []

    # 3. Ask questions if information is missing
    questions = get_questions(parsed["missing"])
    if questions:
        return {
            "status": "needs_input",
            "questions": questions
        }

    # 4. Generate playbook (AI planning step)
    playbook = generate_playbook(parsed["intent"])
    if playbook is None:
        secrets.clear()
        return {
            "status": "failed",
            "error": (
                "Could not generate automation tasks from the request. "
                "Please rephrase or provide more specific instructions."
            )
        }

    # 5. Generate inventory
    inventory = generate_inventory(parsed["hosts"])

    # 6. Execute Ansible
    try:
        result = run_playbook(
            playbook,
            inventory,
            secrets.get("user"),
            secrets.get("password")
        )
    except Exception as e:
        secrets.clear()
        return {
            "status": "failed",
            "error": str(e)
        }

    # 7. Cleanup secrets
    secrets.clear()

    return result
