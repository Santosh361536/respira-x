# Respira-X 🫁

> **Breathe intelligence into respiratory health.**  
> Respira-X is an acoustic screening platform that extracts clinical biomarkers and spectral signatures from cough recordings to deliver immediate, non-invasive respiratory pattern analysis.

---

## 📌 Project Overview

Respira-X provides an accessible, pre-diagnostic evaluation of respiratory acoustic signals. By capturing a single-burst cough through standard consumer audio hardware, the system eliminates background silence, calculates acoustic features (MFCCs, spectral roll-off, centroid, flux, RMS energy, and pitch), and classifies the input against verified clinical patterns.

### Supported Diagnostic Classes
* **Normal / Throat Clearing** (`healthy`)
* **COVID-19 Positive Pattern** (`covid`)
* **Bronchial Obstruction / Asthma / Bronchitis** (`obstructive`)
* **Respiratory Tract Infection** (`upper` / `lower`)
* **False Signal Rejection** (`talking` / `noise` / duration anomaly)

---

## 🛠️ System Architecture & Tech Stack
