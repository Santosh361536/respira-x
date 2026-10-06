# Respira-X

> **Breathe intelligence into respiratory health.**  
> Respira-X is an acoustic screening platform that extracts clinical biomarkers and spectral signatures from cough recordings to deliver immediate, non-invasive respiratory pattern analysis.

---

## Project Overview

Respira-X provides an accessible, pre-diagnostic evaluation of respiratory acoustic signals. By capturing a single-burst cough through standard consumer audio hardware, the system eliminates background silence, calculates acoustic features (MFCCs, spectral roll-off, centroid, flux, RMS energy, and pitch), and classifies the input against verified clinical patterns.

### Supported Diagnostic Classes
* **Normal / Throat Clearing** (`healthy`)
* **COVID-19 Positive Pattern** (`covid`)
* **Bronchial Obstruction / Asthma / Bronchitis** (`obstructive`)
* **Respiratory Tract Infection** (`upper` / `lower`)
* **False Signal Rejection** (`talking` / `noise` / duration anomaly)

---

## 🛠️ System Architecture & Tech Stack

```text
[ User Microphone / .wav ]
           │
           ▼
[ React + Vite + Tailwind Client ]
           │ (Multipart Form Data / Axios)
           ▼
[ FastAPI Backend (app.py) ]
           │
   ┌───────┴────────────────────────┐
   ▼                                ▼
[ Librosa Audio Pipeline ]   [ Random Forest Classifier ]
 • Silence trimming           • cough_model.joblib
 • 13 MFCCs extraction        • 7-class probability map
 • Spectral & temporal stats  • Outlier/speech rejection
```

### Technology Breakdown
* **Client / UI:** React 18, Vite, TypeScript, Tailwind CSS, shadcn/ui
* **Server / API:** Python 3.10+, FastAPI, Uvicorn, Jinja2 (fallback rendering)
* **Audio Engineering:** Librosa, SoundFile, NumPy
* **Machine Learning:** Scikit-Learn (`RandomForestClassifier`, serialized via `joblib`)
* **Target Hardware:** Cross-platform (optimized for Apple Silicon / M-series and mobile browsers)

---

## 📂 Repository Structure

```text
├── dataset_1sec/          # Training audio samples split by class
├── src/                   # React frontend source code
├── api/                   # Serverless deployment adapter
├── static/                # Static assets (icons, styles)
├── templates/             # Server-rendered fallback templates
├── app.py                 # FastAPI application & real-time inference server
├── train_model.py         # Feature extraction & Random Forest training script
├── test_audio.py          # Audio validation & buffer compatibility test suite
├── cough_model.joblib     # Pre-trained acoustic classification model
├── test.wav               # Verification audio sample
├── package.json           # Frontend dependencies & build scripts
└── requirements.txt       # Python core dependencies
```

---

## Getting Started..

### Prerequisites
* **Node.js** (v18.x or later) / **Bun**
* **Python** (3.9 - 3.11 recommended)
* **Virtual Environment tool** (`venv`)

---

### 1. Backend Setup & Training

1. **Clone the repository and enter the directory:**
   ```bash
   git clone [https://github.com/Santosh361536/respira-x.git](https://github.com/Santosh361536/respira-x.git)
   cd respira-x
   ```

2. **Create and activate a Python virtual environment:**
   ```bash
   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate

   # Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Verify audio pipeline:**
   ```bash
   python test_audio.py
   ```

5. **Train the classification model (optional if `cough_model.joblib` exists):**
   ```bash
   python train_model.py
   ```

6. **Start the FastAPI backend:**
   ```bash
   python app.py
   ```
   *The API will start at `http://127.0.0.1:8000` with interactive docs at `/docs`.*

---

### 2. Frontend Setup

1. **Install JavaScript dependencies:**
   ```bash
   npm install
   # or
   bun install
   ```

2. **Run the local development server:**
   ```bash
   npm run dev
   # or
   bun run dev
   ```

3. **Build for production:**
   ```bash
   npm run build
   ```
   *The built assets will output to `dist/`, which FastAPI serves automatically.*

---

## 🔬 Acoustic Feature Pipeline

For every audio signal loaded at `22,050 Hz`:
1. **Silence Removal:** `librosa.effects.trim(top_db=20)` isolates the impulse cough burst.
2. **Impulse Validation:** Recordings where active audio exceeds 1.6 seconds are rejected as continuous speech/background noise.
3. **Feature Vector Extraction:** Extracts 13 MFCC means, spectral centroid, spectral roll-off, zero-crossing rate, RMS energy, spectral flux, and pitch frequency ($f_0$).
4. **Classification & Overrides:** An ensemble of 100 decision trees calculates class posterior probabilities with confidence safety thresholds to suppress false positives.

---

## Future Scope & Roadmap

* [ ] **Cough Quality Index (CQI):** Quantifying acoustic damping ratios to systematically separate wet vs. dry productive coughs.
* [ ] **2D CNN Migration:** Transitioning from 1D tabular statistics to 2D Log-Mel Spectrogram matrices analyzed via a lightweight MobileNet/CNN architecture.
* [ ] **AI Stethoscope (IoT Auscultation):** Direct sensor streaming (via BLE/ESP32) for internal lung sounds (wheezing, fine/coarse crackles, and stridor).
