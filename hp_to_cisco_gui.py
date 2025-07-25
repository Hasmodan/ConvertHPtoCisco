import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
from collections import defaultdict
import re
import os
import pyperclip

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
    try:
        lines = config_text.strip().splitlines()
        vlan_ports = defaultdict(lambda: {"untagged": [], "tagged": []})
        svi_config = {}
        interface_tagged = defaultdict(set)
        interface_descriptions = {}  # Nouveau : stocker descriptions par interface
        spanning_tree_present = False
        current_vlan = None
        current_intf = None
        hostname = None

        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith("hostname"):
                hostname = line.split(maxsplit=1)[1].strip('"')
            elif line == "spanning-tree":
                spanning_tree_present = True
            elif line.startswith("vlan "):
                current_vlan = int(line.split()[1])
                current_intf = None
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
            elif line.startswith("interface"):
                parts = line.split()
                if len(parts) == 2 and parts[1].isdigit():
                    current_intf = int(parts[1])
                    interface_tagged[current_intf] = set()
                else:
                    current_intf = None
                current_vlan = None
            elif line.startswith("name") and current_intf is not None:
                # ligne "name "...""
                # on enlève les guillemets si présent
                name_val = line.split(maxsplit=1)[1].strip('"')
                interface_descriptions[current_intf] = name_val
            elif line.startswith("tagged vlan") and current_intf is not None:
                vlan_list_str = line.replace("tagged vlan", "").strip()
                vlans = re.split(r'[, ]+', vlan_list_str)
                for v in vlans:
                    if v.isdigit():
                        interface_tagged[current_intf].add(int(v))
            elif line == "exit":
                current_vlan = None
                current_intf = None

        for port, tagged_vlans in interface_tagged.items():
            for vlan in tagged_vlans:
                if port not in vlan_ports[vlan]["tagged"]:
                    vlan_ports[vlan]["tagged"].append(port)

        return vlan_ports, svi_config, interface_tagged, interface_descriptions, hostname, spanning_tree_present, ""
    except Exception as e:
        return None, None, None, None, None, None, f"Erreur lors de l'analyse : {str(e)}"

def build_cisco_config(vlan_ports, svi_config, interface_tagged, interface_descriptions, hostname, spanning_tree_present):
    config_lines = []
    port_mode = defaultdict(lambda: {"access": None, "trunk": set()})

    for vlan, ports_types in vlan_ports.items():
        for port in ports_types["untagged"]:
            port_mode[port]["access"] = vlan
        for port in ports_types["tagged"]:
            port_mode[port]["trunk"].add(vlan)

    if hostname:
        config_lines.append(f"hostname {hostname}")

    for vlan in sorted(svi_config):
        ip = svi_config[vlan]
        config_lines.append(f"\ninterface Vlan{vlan}")
        config_lines.append(f" ip address {ip}")
        config_lines.append(" no shutdown")

    for port in sorted(port_mode):
        access_vlan = port_mode[port]["access"]
        trunk_vlans = port_mode[port]["trunk"]

        config_lines.append(f"\ninterface FastEthernet0/{port}")

        # Ajout de la description si présente
        if port in interface_descriptions:
            config_lines.append(f" description {interface_descriptions[port]}")

        if trunk_vlans:
            config_lines.append(" switchport mode trunk")
            allowed_vlans = ",".join(str(v) for v in sorted(trunk_vlans))
            config_lines.append(f" switchport trunk allowed vlan {allowed_vlans}")
        elif access_vlan:
            config_lines.append(" switchport mode access")
            config_lines.append(f" switchport access vlan {access_vlan}")
        else:
            config_lines.append(" switchport mode access")
            config_lines.append(" switchport access vlan 1")

    if spanning_tree_present:
        config_lines.append("\nspanning-tree")

    return "\n".join(config_lines)

def convert_config():
    hp_input = input_text.get("1.0", tk.END)
    vlan_ports, svi_config, interface_tagged, interface_descriptions, hostname, spanning_tree_present, error = parse_hp_config(hp_input)
    if error:
        messagebox.showerror("Erreur", error)
        return
    if not vlan_ports:
        messagebox.showerror("Erreur", "Aucune configuration VLAN détectée.")
        return
    cisco_output = build_cisco_config(vlan_ports, svi_config, interface_tagged, interface_descriptions, hostname, spanning_tree_present)
    output_text.delete("1.0", tk.END)
    output_text.insert(tk.END, cisco_output)

def load_file():
    filepath = filedialog.askopenfilename(filetypes=[("Fichiers texte", "*.txt")])
    if filepath:
        with open(filepath, 'r') as file:
            content = file.read()
            input_text.delete("1.0", tk.END)
            input_text.insert(tk.END, content)

def save_output():
    filepath = filedialog.asksaveasfilename(defaultextension=".txt",
                                            filetypes=[("Fichiers texte", "*.txt")])
    if filepath:
        with open(filepath, 'w') as file:
            file.write(output_text.get("1.0", tk.END))
        messagebox.showinfo("Sauvegardé", f"Configuration Cisco enregistrée dans :\n{os.path.basename(filepath)}")

def copy_to_clipboard():
    text = output_text.get("1.0", tk.END)
    pyperclip.copy(text)
    messagebox.showinfo("Copié", "Configuration Cisco copiée dans le presse-papier.")

root = tk.Tk()
root.title("HP → Cisco VLAN/LAG Converter")

tk.Label(root, text="🟡 Configuration HP/Aruba").pack()
input_text = scrolledtext.ScrolledText(root, width=100, height=15)
input_text.pack(padx=10, pady=5)

button_frame = tk.Frame(root)
button_frame.pack(pady=5)

tk.Button(button_frame, text="📁 Charger un fichier .txt", command=load_file).pack(side="left", padx=5)
tk.Button(button_frame, text="🔁 Convertir en Cisco", command=convert_config).pack(side="left", padx=5)

tk.Label(root, text="🔵 Configuration Cisco").pack()
output_text = scrolledtext.ScrolledText(root, width=100, height=20)
output_text.pack(padx=10, pady=5)

action_frame = tk.Frame(root)
action_frame.pack(pady=5)

tk.Button(action_frame, text="📋 Copier dans le presse-papier", command=copy_to_clipboard).pack(side="left", padx=5)
tk.Button(action_frame, text="💾 Sauvegarder la configuration", command=save_output).pack(side="left", padx=5)

root.mainloop()
