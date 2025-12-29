import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INVENTORY_DIR = os.path.join(BASE_DIR, "generated", "inventory")

def generate_inventory(hosts):
    os.makedirs(INVENTORY_DIR, exist_ok=True)
    path = os.path.join(INVENTORY_DIR, "hosts.ini")

    with open(path, "w") as f:
        f.write("[targets]\n")
        for host in hosts:
            f.write(f"{host}\n")

    return path
