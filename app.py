import os
import io
import traceback
import tempfile
import numpy as np
import joblib
import librosa
import soundfile as sf
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Respira-X API")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
DIST_DIR = os.path.join(BASE_DIR, "dist")
DIST_ASSETS_DIR = os.path.join(DIST_DIR, "assets")
DIST_INDEX = os.path.join(DIST_DIR, "index.html")
MODEL_PATH = os.path.join(BASE_DIR, "cough_model.joblib")

for folder in [STATIC_DIR, TEMPLATES_DIR]:
    os.makedirs(folder, exist_ok=True)

if os.path.exists(DIST_ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=DIST_ASSETS_DIR), name="assets")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=TEMPLATES_DIR) if os.path.exists(TEMPLATES_DIR) else None

model = None
if os.path.exists(MODEL_PATH):
    try:
        model = joblib.load(MODEL_PATH)
        print(f"✅ MODEL LOADED: {MODEL_PATH}")
    except Exception as e:
        print(f"❌ MODEL LOAD FAILED: {e}")
else:
    print(f"⚠️ NO MODEL FILE FOUND at {MODEL_PATH}. Run: python train_model.py")


@app.get("/")
async def home(request: Request):
    if os.path.exists(DIST_INDEX):
        return FileResponse(DIST_INDEX)
    return JSONResponse({
        "status": "online",
        "service": "Respira-X Audio Analysis API",
        "version": "1.0.0",
        "endpoints": {
            "analyze": "POST /analyze (multipart/form-data: cough_audio)"
        }
    })


@app.post("/analyze")
async def analyze(cough_audio: UploadFile = File(...)):
    print(f"📥 Received file: {cough_audio.filename} ({cough_audio.content_type})")

    if not model:
        return {
            "status": "Analysis Failed",
            "prediction": "ERROR ❌",
            "confidence": "N/A%",
            "details": "Model pipeline not loaded on server. Run train_model.py first.",
            "severity": "high",
        }

    try:
        audio_bytes = await cough_audio.read()
        if len(audio_bytes) == 0:
            raise ValueError("Uploaded audio file is empty.")
    except Exception as e:
        return {
            "status": "Analysis Failed",
            "prediction": "ERROR ❌",
            "confidence": "N/A%",
            "details": f"File read error: {e}",
            "severity": "high",
        }

    try:
        try:
            audio_data, sr = librosa.load(io.BytesIO(audio_bytes), sr=22050)
        except Exception:
            suffix = os.path.splitext(cough_audio.filename or ".wav")[-1] or ".wav"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            try:
                audio_data, sr = librosa.load(tmp_path, sr=22050)
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

        trimmed_audio, _ = librosa.effects.trim(audio_data, top_db=22)
        if len(trimmed_audio) == 0:
            return {
                "status": "Analysis Complete",
                "prediction": "SILENCE / NO SIGNAL",
                "confidence": "100%",
                "details": "Audio recording contains no audible cough signature. Please try again.",
                "severity": "low",
            }

        duration = librosa.get_duration(y=trimmed_audio, sr=sr)
        print(f"📊 Active audio duration after trimming: {duration:.2f}s")

        if duration > 1.25:
            return {
                "status": "Analysis Complete",
                "prediction": "SPEECH / PROLONGED SOUND",
                "confidence": "N/A",
                "details": f"Recording duration ({duration:.2f}s) exceeded a single cough burst. Please record an isolated, single cough.",
                "severity": "low",
            }

        if duration < 0.15:
            return {
                "status": "Analysis Complete",
                "prediction": "SIGNAL TOO SHORT",
                "confidence": "N/A",
                "details": "Audio snippet was too brief to extract clinical markers.",
                "severity": "low",
            }

        from train_model import extract_features_from_array
        features = extract_features_from_array(trimmed_audio, sr)

        if features is None:
            raise ValueError("Feature vector formulation failed.")

        probabilities = model.predict_proba([features])[0]
        ml_prediction = model.predict([features])[0]
        confidence = float(np.max(probabilities) * 100)

        classes_debug = dict(zip(model.classes_, [f"{p*100:.1f}%" for p in probabilities]))
        print(f"🎯 Prediction: {ml_prediction} ({confidence:.1f}%) | Probabilities: {classes_debug}")

        if ml_prediction in ["talking", "noise"]:
            return {
                "status": "Analysis Complete",
                "prediction": "NOT A COUGH",
                "confidence": f"{confidence:.1f}%",
                "details": f"Sound identified as human speech or background ambient noise ({ml_prediction}). Please submit an isolated cough sound.",
                "severity": "low",
            }

        if confidence < 45.0:
            return {
                "status": "Analysis Complete",
                "prediction": "INCONCLUSIVE / UNCLEAR",
                "confidence": f"{confidence:.1f}%",
                "details": "Acoustic signature could not be matched with high certainty. Try recording closer to the microphone.",
                "severity": "low",
            }

        if ml_prediction == "covid":
            prediction = "COVID-19 PATTERN DETECTED"
            severity = "high"
            details = f"Acoustic features display signatures consistent with COVID-19 pulmonary patterns ({duration:.2f}s). Seek clinical confirmation."
        elif ml_prediction == "healthy":
            prediction = "NORMAL"
            severity = "low"
            details = f"No abnormal respiratory signatures detected ({duration:.2f}s). Sounds consistent with a clear throat or healthy cough."
        elif ml_prediction in ["upper", "lower"]:
            prediction = "RESPIRATORY TRACT INFECTION"
            severity = "medium"
            details = f"Detected spectral characteristics indicative of respiratory tract inflammation ({duration:.2f}s)."
        elif ml_prediction == "obstructive":
            prediction = "BRONCHIAL OBSTRUCTION"
            severity = "medium"
            details = f"Acoustic markers show airflow resistance consistent with bronchitis/asthmatic cough ({duration:.2f}s)."
        else:
            prediction = str(ml_prediction).upper()
            severity = "low"
            details = f"Classification: {ml_prediction}."

        return {
            "status": "Analysis Complete",
            "prediction": prediction,
            "confidence": f"{confidence:.1f}%",
            "details": details,
            "severity": severity,
        }

    except Exception as e:
        error_msg = f"Inference error: {str(e)}\n{traceback.format_exc()}"
        print(f"❌ {error_msg}")
        return {
            "status": "Analysis Failed",
            "prediction": "ERROR ❌",
            "confidence": "N/A%",
            "details": str(e),
            "severity": "high",
        }


@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    if full_path == "analyze":
        return JSONResponse({"status": "error", "message": "Method Not Allowed on GET"}, status_code=405)
    file_target = os.path.join(DIST_DIR, full_path)
    if os.path.isfile(file_target):
        return FileResponse(file_target)
    if os.path.exists(DIST_INDEX):
        return FileResponse(DIST_INDEX)
    return HTMLResponse("<h1>404 Not Found</h1>", status_code=404)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
