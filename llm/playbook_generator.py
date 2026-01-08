import os
import re
import yaml
from llm.llm_client import query_llm

PLAYBOOK_DIR = "generated/playbooks"
PLAYBOOK_PATH = os.path.join(PLAYBOOK_DIR, "generated.yml")
MAX_ATTEMPTS = 6

# -------------------------------
# Normalize meta-packages
# -------------------------------
PACKAGE_EXPANSIONS = {
    "php": ["php-cli", "php-common", "libapache2-mod-php"],
}

# -------------------------------
def strip_code_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 1)[1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    return text.strip()

# -------------------------------
def detect_module(task: dict):
    for m in ("apt", "service", "systemd"):
        if m in task:
            return m
    return None

# -------------------------------
def normalize_apt_name(name):
    if not isinstance(name, str):
        return name
    base = re.sub(r"[0-9].*$", "", name).rstrip("-")
    return PACKAGE_EXPANSIONS.get(base, name)

# -------------------------------
def unwrap_task(task):
    """
    Converts:
    - task: { name: X, apt: {...} }
    into:
    { name: X, apt: {...} }
    """
    if "task" in task and isinstance(task["task"], dict):
        return task["task"]
    return task

# -------------------------------
def sanitize_task(task):
    if not isinstance(task, dict):
        return None

    task = unwrap_task(task)

    # Remove play-level keys
    for bad in ("hosts", "become", "tasks"):
        task.pop(bad, None)

    if "name" in task:
        task["name"] = re.sub(r"on .*", "", task["name"]).strip()

    task.pop("when", None)
    task.pop("register", None)

    module = detect_module(task)
    if not module:
        return None

    # ---------------- APT ----------------
    if module == "apt":
        apt = task.get("apt")
        if not isinstance(apt, dict):
            return None

        if "pkg" in apt:
            apt["name"] = apt.pop("pkg")
        if "package" in apt:
            apt["name"] = apt.pop("package")

        names = apt.get("name")
        if not names:
            return None

        if not isinstance(names, list):
            names = [names]

        expanded = []
        for n in names:
            norm = normalize_apt_name(n)
            if isinstance(norm, list):
                expanded.extend(norm)
            else:
                expanded.append(norm)

        apt["name"] = sorted(set(expanded))
        apt["state"] = apt.get("state", "present")
        apt["update_cache"] = apt.get("update_cache", True)

        allowed = {
            "name", "state", "update_cache",
            "cache_valid_time", "force",
            "install_recommends",
            "allow_unauthenticated"
        }

        for k in list(apt.keys()):
            if k not in allowed:
                apt.pop(k)

    # ---------------- SERVICE / SYSTEMD ----------------
    if module in ("service", "systemd"):
        svc = task.get(module)
        if not isinstance(svc, dict):
            return None

        svc["name"] = svc.get("name", "").split(".")[0]
        svc["state"] = svc.get("state", "started")
        svc.setdefault("enabled", True)

        for bad in ("host", "target", "ip"):
            svc.pop(bad, None)

    return task

# -------------------------------
def generate_playbook(intent: str):
    feedback = ""

    base_prompt = f"""
You are an Ansible automation engine.

Rules:
- Output ONLY valid YAML
- Output a LIST of Ansible TASKS only
- NO markdown
- NO explanations
- NO hosts, become, vars
- Use ONLY: apt, service, systemd
- Use Ubuntu service names

User request:
{intent}
"""

    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f">>> LLM CALL ATTEMPT {attempt} <<<")

        prompt = base_prompt
        if feedback:
            prompt += f"\n\nPrevious error:\n{feedback}"

        response = strip_code_fences(query_llm(prompt))

        print("\n=== RAW LLM OUTPUT ===")
        print(response)
        print("======================")

        try:
            parsed = yaml.safe_load(response)
        except Exception as e:
            feedback = f"YAML parse error: {e}"
            continue

        if not isinstance(parsed, list):
            feedback = "Output must be a list of tasks"
            continue

        sanitized = []
        for t in parsed:
            clean = sanitize_task(t)
            if clean:
                sanitized.append(clean)

        if not sanitized:
            feedback = "All tasks dropped during sanitization"
            continue

        playbook = [{
            "name": "LLM Generated Automation",
            "hosts": "all",
            "become": True,
            "tasks": sanitized
        }]

        os.makedirs(PLAYBOOK_DIR, exist_ok=True)
        with open(PLAYBOOK_PATH, "w") as f:
            yaml.safe_dump(playbook, f, sort_keys=False)

        print("✅ PLAYBOOK GENERATED SUCCESSFULLY")
        print(f"📄 {PLAYBOOK_PATH}")
        return PLAYBOOK_PATH

    return None
