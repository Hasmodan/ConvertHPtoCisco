# ConvertHPtoCisco

# HP to Cisco VLAN Config Converter 🔄

Un outil simple en Python avec interface graphique pour convertir une configuration VLAN + LAG de switch HP/Aruba (style ProCurve) en configuration Cisco équivalente.

> 🧠 Pensé pour les ingénieurs réseau qui passent leur temps à traduire des configs HP mal documentées en Cisco.

## 📸 Capture d'écran

<img width="1498" height="1390" alt="image" src="https://github.com/user-attachments/assets/ebae7692-c3d1-45ce-aec4-61a8cfbf3b5e" />
<img width="1512" height="1392" alt="image" src="https://github.com/user-attachments/assets/edc4353a-7c6d-4efb-803a-f16c783bd5d4" />



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

### 2. Lancer l'application

```bash
python hp_to_cisco_gui.py
