# THIMS (Turbine Health Index & Maintenance Scheduler)

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)
![Market](https://img.shields.io/badge/Marché-Algérien%20🇩🇿-white)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

**Logiciel de gestion préventive des turbines à gaz — السوق الجزائرية**

*Sonatrach · Sonelgaz · GTP Hassi R'Mel · SKB Berkine*

</div>

---

## 📋 Description

Application desktop Python dédiée à la **surveillance de la santé des turbines à gaz** et à la **planification de la maintenance préventive**, développée pour répondre aux besoins du marché énergétique algérien.

Elle calcule automatiquement le **Turbine Health Index (THI)** à partir des paramètres opérationnels et thermodynamiques, et génère des ordres de travail compatibles CMMS (SAP PM, IBM Maximo).

---

## ✨ Fonctionnalités

| Fonctionnalité | Description |
|---|---|
| 📊 **Dashboard interactif** | Jauge THI, cartes KPI, barres de santé colorées |
| 🔧 **Saisie des données** | Formulaire complet avec sélection du modèle de turbine |
| 📈 **Historique & Tendances** | Graphe matplotlib de l'évolution du THI dans le temps |
| 📄 **Rapport & Export** | JSON (CMMS), CSV (Excel), rapport texte imprimable |
| 🇩🇿 **Marché algérien** | Opérateurs (Sonatrach, Sonelgaz…) et coûts en **DZD** |
| 🌙 **Thème industriel sombre** | Interface professionnelle dark mode |

---

## ⚙️ Modèles de turbines supportés

- **GE Frame 6B** (PG6581B) — EOH limit: 32 000 h
- **GE Frame 9E** (PG9171E) — EOH limit: 25 000 h
- **GE LM2500+** — EOH limit: 20 000 h
- **Siemens SGT-800** — EOH limit: 30 000 h
- **Solar Centaur 50** — EOH limit: 18 000 h
- **Rolls-Royce Avon** — EOH limit: 20 000 h

---

## 🧮 Équations mathématiques utilisées

### Equivalent Operating Hours (EOH)
$$EOH = OH + f_s \times N_s$$

### Turbine Health Index (THI)
$$THI = 0.55 \times H_{EOH} + 0.35 \times H_{Perf} + 0.10 \times H_{PR}$$

### Classification de la maintenance
| THI | État | Action |
|---|---|---|
| > 80% | 🟢 Fonctionnement Normal | Surveillance standard |
| 60% – 80% | 🟡 Inspection Combustion | Inspection + lavage compresseur |
| < 60% ou EOH ≥ Limite | 🔴 Grande Révision | Arrêt planifié immédiat |

---

## 🚀 Installation & Lancement

### Prérequis
- Python 3.8 ou supérieur
- pip

### 1. Cloner le dépôt
```bash
git clone https://github.com/VOTRE_USERNAME/THIMS.git
cd THIMS
```

### 2. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 3. Lancer l'application
```bash
python turbine_ui_v2.py
```

---

## 📁 Structure du projet

```
turbine-health-scheduler/
├── turbine_ui_v2.py          # Application principale (UI + moteur de calcul)
├── turbine_health_scheduler.py # Version ligne de commande (CLI)
├── requirements.txt           # Dépendances Python
├── turbine_history.json       # Base de données locale (auto-générée)
├── README.md                  # Ce fichier
└── LICENSE                    # Licence MIT
```

---

## 📸 Aperçu

> Interface dark mode avec jauge THI, dashboard KPI, graphe historique et export CMMS.

---

## 🏭 Opérateurs algériens intégrés

- Sonatrach — Division Production
- Sonelgaz — Groupe Production
- GTP — Groupement Hassi R'Mel
- SKB — Groupement Berkine
- Groupement Bir Seba
- SHPG — Hassi Messaoud

---

## 📤 Export CMMS (SAP PM / IBM Maximo)

L'application génère des ordres de travail structurés en **JSON** prêts à être importés dans un système CMMS :

```json
{
  "work_order_id": "WO-1727519846",
  "equipment_id": "GT-101",
  "operator": "Sonatrach — Division Production",
  "turbine_model": "GE Frame 6B (PG6581B)",
  "priority": "HAUTE",
  "work_type": "MP",
  "urgency": "Grande Revision Requise",
  "THI": 8.0,
  "EOH": 34750.0,
  "cout_DZD": { "min": 45000000, "max": 180000000 }
}
```

---

## 📜 Licence

Distribué sous licence **MIT**. Voir [LICENSE](LICENSE) pour plus de détails.

---

## 👤 Auteur

Développé avec ❤️ pour le secteur énergétique algérien.
