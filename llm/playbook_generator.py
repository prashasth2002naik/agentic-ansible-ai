import os
import re
import yaml
from llm.llm_client import query_llm

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLAYBOOK_DIR = os.path.join(BASE_DIR, "generated", "playbooks")
os.makedirs(PLAYBOOK_DIR, exist_ok=True)


def clean_llm_output(text: str) -> str:
    """
    Remove markdown fences and extra text from LLM output
    """
    text = re.sub(r"```[a-zA-Z]*", "", text)
    text = re.sub(r"```", "", text)
    return text.strip()


def normalize_tasks(data):
    """
    Normalize different LLM output shapes into a pure task list
    """
    # Case 1: LLM returned list of tasks
    if isinstance(data, list):
        # If list of plays, extract tasks
        if data and isinstance(data[0], dict) and "tasks" in data[0]:
            return normalize_tasks(data[0]["tasks"])
        return data

    # Case 2: dict with "tasks"
    if isinstance(data, dict) and "tasks" in data:
        return normalize_tasks(data["tasks"])

    return None


def sanitize_task(task: dict) -> dict:
    """
    Sanitize a single Ansible task produced by an LLM.
    Enforces module schemas and removes hallucinated keys.
    """

    # ---- REMOVE LOOPING (LLMs hallucinate loops often) ----
    task.pop("with_items", None)
    task.pop("loop", None)
    task.pop("loop_control", None)

    # ---- APT MODULE ----
    if "apt" in task:
        apt = task["apt"]

        # Map common aliases
        if "pkg" in apt:
            apt["name"] = apt.pop("pkg")
        if "package" in apt:
            apt["name"] = apt.pop("package")
        if "args" in apt:
            apt["name"] = apt.pop("args")

        # Keep only valid apt parameters
        allowed_keys = {
            "name",
            "state",
            "update_cache",
            "cache_valid_time",
            "force",
            "default_release",
            "install_recommends",
            "allow_unauthenticated"
        }

        for key in list(apt.keys()):
            if key not in allowed_keys:
                apt.pop(key)

        apt.setdefault("state", "present")

    # ---- SERVICE / SYSTEMD MODULE ----
    # ---- SERVICE / SYSTEMD MODULE ----
    for module in ("service", "systemd"):
        if module in task:
            svc = task[module]

            # Remove hallucinated host-related keys
            for bad_key in ("host", "hosts", "target", "ip"):
                svc.pop(bad_key, None)

            # Clean service name (remove host text like ": host", "on <ip>")
            if "name" in svc:
                svc["name"] = svc["name"].split(":")[0]
                svc["name"] = svc["name"].split(" on ")[0]
                svc["name"] = svc["name"].strip()

            # Remove fake services like git
            if svc.get("name") in {"git"}:
                task.pop(module)
            else:
                svc.setdefault("state", "started")

    return task


def generate_playbook(intent: str):
    """
    Generate a valid Ansible playbook using ONLY LLM output,
    normalized and sanitized before execution.
    """

    prompt = f"""
You are an Ansible task generator.

Rules:
- Output ONLY valid YAML
- Output ONLY Ansible TASKS
- DO NOT include hosts, become, vars, or play definitions
- DO NOT include explanations or markdown
- Use apt and service/systemd modules where appropriate
- Target OS is Ubuntu

If the task cannot be expressed as Ansible tasks, return an empty list: []

User request:
"{intent}"
"""

    # Call LLM
    response = query_llm(prompt)
    cleaned = clean_llm_output(response)

    try:
        raw = yaml.safe_load(cleaned)
    except Exception:
        return None

    tasks = normalize_tasks(raw)
    if not tasks:
        return None

    # Sanitize all tasks
    tasks = [sanitize_task(task) for task in tasks if isinstance(task, dict)]

    if not tasks:
        return None

    # Build final playbook
    playbook = [{
        "name": "LLM Generated Automation",
        "hosts": "all",
        "become": True,
        "tasks": tasks
    }]

    playbook_path = os.path.join(PLAYBOOK_DIR, "generated.yml")
    with open(playbook_path, "w") as f:
        yaml.dump(playbook, f, default_flow_style=False)

    return playbook_path
