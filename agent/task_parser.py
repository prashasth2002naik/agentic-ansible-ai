import re
import ipaddress

def extract_hosts(text: str):
    hosts = set()

    # IPs
    ips = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text)
    hosts.update(ips)

    # CIDR
    cidrs = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}/\d{1,2}\b", text)
    for cidr in cidrs:
        for ip in ipaddress.ip_network(cidr, strict=False):
            hosts.add(str(ip))

    return list(hosts)


def parse_task(text: str):
    hosts = extract_hosts(text)

    missing = []
    if not hosts:
        missing.append("hosts")

    missing.append("credentials")

    return {
        "intent": text,
        "hosts": hosts,
        "missing": missing
    }
