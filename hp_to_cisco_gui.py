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
        lag_config = {}
        current_vlan = None

        for line in lines:
            line = line.strip()

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
            elif line.startswith("trunk"):
                parts = line.split()
                if len(parts) >= 4:
                    ports = parse_ports(parts[1])
                    trk_name = parts[2]
                    mode = parts[3]
                    lag_config[trk_name] = {"ports": ports, "mode": mode}
        return vlan_ports, svi_config, lag_config, ""
    except Exception as e:
        return None, None, None, f"Erreur lors de l'analyse : {str(e)}"

def build_cisco_config(vlan_ports, svi_config, lag_config):
    config_lines = []
    port_mode = defaultdict(lambda: {"access": None, "trunk": []})
    lag_ports = {}

    for trk, conf in lag_config.items():
        for p in conf["ports"]:
            lag_ports[p] = trk

    for vlan, types in vlan_ports.items():
        for p in types["untagged"]:
            if p not in lag_ports:
                port_mode[p]["access"] = vlan
        for p in types["tagged"]:
            if p not in lag_ports:
                port_mode[p]["trunk"].append(vlan)

    for vlan in sorted(svi_config):
        ip = svi_config[vlan]
        config_lines.append(f"interface Vlan{vlan}")
        config_lines.append(f" ip address {ip}")
        config_lines.append(" no shutdown\n")

    for port in sorted(port_mode):
        if port_mode[port]["access"] and not port_mode[port]["trunk"]:
            config_lines.append(f"interface FastEthernet0/{port}")
            config_lines.append(" switchport mode access")
            config_lines.append(f" switchport access vlan {port_mode[port]['access']}\n")
        elif port_mode[port]["trunk"]:
            config_lines.append(f"interface FastEthernet0/{port}")
            config_lines.append(" switchport mode trunk")
            allowed_vlans = ','.join(map(str, sorted(port_mode[port]["trunk"])))
            config_lines.append(f" switchport trunk allowed vlan {allowed_vlans}\n")

    for idx, (trk, conf) in enumerate(lag_config.items(), start=1):
        config_lines.append(f"interface Port-channel{idx}")
        config_lines.append(" switchport")
        config_lines.append(" switchport mode trunk")
        config_lines.append(" switchport trunk allowed vlan all\n")
        for port in conf["ports"]:
            config_lines.append(f"interface FastEthernet0/{port}")
            config_lines.append(" switchport")
            config_lines.append(" switchport mode trunk")
            mode = "active" if conf["mode"] == "lacp" else "on"
            config_lines.append(f" channel-group {idx} mode {mode}\n")

    return "\n".join(config_lines)

def convert_config():
    hp_input = input_text.get("1.0", tk.END)
    vlan_ports, svi_config, lag_config, error = parse_hp_config(hp_input)
    if error:
        messagebox.showerror("Erreur", error)
        return
    if not vlan_ports:
        messagebox.showerror("Erreur", "Aucune configuration VLAN détectée.")
        return
    cisco_output = build_cisco_config(vlan_ports, svi_config, lag_config)
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

# Interface graphique
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
