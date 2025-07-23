# ConvertHPtoCisco

# HP to Cisco VLAN Config Converter 🔄

Un outil simple en Python avec interface graphique pour convertir une configuration VLAN + LAG de switch HP/Aruba (style ProCurve) en configuration Cisco équivalente.

> 🧠 Pensé pour les nuls comme moi :D 

## 📸 Capture d'écran

<img width="1652" height="1452" alt="image" src="https://github.com/user-attachments/assets/4400cd82-8b5f-4d68-87f6-84f6aaa15c83" />




## ✨ Fonctionnalités

✅ Conversion des VLANs (tagged / untagged)  
✅ Détection des ports access / trunk  
✅ Traduction des SVI (IP sur VLANs)  
✅ Traduction des LAGs (port-channel LACP ou statique)  
✅ Interface graphique avec Tkinter  
✅ Résultat copiable facilement ou exportable

---

## 🖥️ Utilisation

### 1. Prérequis

- Python 3.x  
- Aucun module externe requis (Tkinter est inclus avec Python)
- pyperclip

### 2. Lancer l'application

```bash
python hp_to_cisco_gui.py
