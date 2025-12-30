# agentic-ansible-ai
Agentic AI system that converts natural language into Ansible automation using open-source LLMs



#Steps to execute
🧱 STEP 1 — Prepare your system (foundation)
1.1 Install OS packages

You need a Linux machine (Ubuntu preferred).

Install basics:

sudo apt update
sudo apt install -y python3 python3-pip git ssh ansible

1.2 Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

🧠 STEP 2 — Run an open-source LLM locally

This is your AI brain.

2.1 Install Ollama (open source)
curl -fsSL https://ollama.com/install.sh | sh

2.2 Pull open-source models
Reasoning model:
ollama pull mistral

Code / Ansible playbook model:
ollama pull deepseek-coder


✔ Both are fully open source
✔ Runs locally
✔ No internet dependency


Step 3 - clone the git repo

📦 STEP 4 — Install Python dependencies

requirements.txt

fastapi
uvicorn
pyyaml
ansible-runner
requests


Install:

pip install -r requirements.txt


