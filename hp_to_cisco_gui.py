import tkinter as tk
from tkinter import scrolledtext
from collections import defaultdict
import re

def parse_ports(port_str):
    ports = []
    parts = port_str.split(',')
    for part in parts:
        if '-' in part:
            start, end = map(int, part.strip().split('-'))
            ports.extend(range(start, end + 1))
        else:
            ports.append(int(part.strip()))
    return ports

def parse_hp_config(config_text):
    lines = config_text.strip().splitlines()
    vlan_ports = defaultdict(lambda: {"untagged": [], "tagged": []})
    svi_config = {}  # SVI config : vlan_id -> ip address
    lag_config = {}  # Trunked ports (LACP or static) : trk_name -> {"ports": [...], "mode": "lacp/static"}
    current_vlan = None

    for line in lines:
        line = line.strip()

        # VLANs
        if line.startswith("vlan "):
            current_vlan = int(line.split()[1])
        elif "ip address" in line and current_vlan:
            match = re.search(r'ip address (\d+\.\d+\.\d+\.\d+) (\d+\.\d+\.\d+\.\d+)', line)
            if match:
                ip, mask = match.groups()
                svi_config[current_vlan] = f"{ip} {mask}"
        elif line.startswith("untagged") and current_vlan:
            ports = parse_ports(line.replace("untagged", "").strip())
            vlan_ports[current_vlan]["untagged"].extend(ports)
        elif line.startswith("tagged") and current_vlan:
            ports = parse_ports(line.replace("tagged", "").strip())
            vlan_ports[current_vlan]["tagged"].extend(ports)

        # LAGs (trunks)
        elif line.startswith("trunk"):
            parts = line.split()
            if len(parts) >= 4:
                ports = parse_ports(parts[1])
                trk_name = parts[2]
                mode = parts[3]
                lag_config[trk_name] = {"ports": ports, "mode": mode}

    return vlan_ports, svi_config, lag_config

def build_cisco_config(vlan_ports, svi_config, lag_config):
    config_lines = []

    # SVI interfaces (interface vlan X)
    for vlan in sorted(svi_config):
        ip = svi_config[vlan]
        config_lines.append(f"interface Vlan{vlan}")
        config_lines.append(f" ip address {ip}")
        config_lines.append(" no shutdown")
        config_lines.append("")

    # Détection des ports dans des LAGs
    lag_ports = {}
    for trk, conf in lag_config.items():
        for p in conf["ports"]:
            lag_ports[p] = trk

    # Interface port + VLAN
    port_mode = defaultdict(lambda: {"access": None, "trunk": []})
    for vlan, types in vlan_ports.items():
        for p in types["untagged"]:
            if p not in lag_ports:
                port_mode[p]["access"] = vlan
        for p in types["tagged"]:
            if p not in lag_ports:
                port_mode[p]["trunk"].append(vlan)

    # Interfaces physiques non LAG
    for port in sorted(port_mode):
        if port_mode[port]["access"] and not port_mode[port]["trunk"]:
            config_lines.append(f"interface FastEthernet0/{port}")
            config_lines.append(" switchport mode access")
            config_lines.append(f" switchport access vlan {port_mode[port]['access']}")
            config_lines.append("")
        elif port_mode[port]["trunk"]:
            config_lines.append(f"interface FastEthernet0/{port}")
            config_lines.append(" switchport mode trunk")
            allowed_vlans = ','.join(map(str, sorted(port_mode[port]["trunk"])))
            config_lines.append(f" switchport trunk allowed vlan {allowed_vlans}")
            config_lines.append("")

    # LAG (Port-channel) config
    for idx, (trk, conf) in enumerate(lag_config.items(), start=1):
        po_num = idx  # Port-channel number
        mode = conf["mode"]
        config_lines.append(f"interface Port-channel{po_num}")
        config_lines.append(" switchport")
        config_lines.append(" switchport mode trunk")
        config_lines.append(" switchport trunk allowed vlan all")
        config_lines.append("")

        for port in conf["ports"]:
            config_lines.append(f"interface FastEthernet0/{port}")
            config_lines.append(" switchport")
            config_lines.append(" switchport mode trunk")
            if mode == "lacp":
                config_lines.append(f" channel-group {po_num} mode active")
            else:
                config_lines.append(f" channel-group {po_num} mode on")
            config_lines.append("")

    return "\n".join(config_lines)

def convert_config():
    hp_input = input_text.get("1.0", tk.END)
    vlan_ports, svi_config, lag_config = parse_hp_config(hp_input)
    cisco_output = build_cisco_config(vlan_ports, svi_config, lag_config)
    output_text.delete("1.0", tk.END)
    output_text.insert(tk.END, cisco_output)

# Interface graphique
root = tk.Tk()
root.title("HP → Cisco VLAN/LAG Converter")

tk.Label(root, text="🟡 Configuration HP/Aruba").pack()
input_text = scrolledtext.ScrolledText(root, width=90, height=15)
input_text.pack(padx=10, pady=5)

tk.Button(root, text="Convertir en Cisco", command=convert_config).pack(pady=10)

tk.Label(root, text="🔵 Configuration Cisco").pack()
output_text = scrolledtext.ScrolledText(root, width=90, height=20)
output_text.pack(padx=10, pady=5)

root.mainloop()
