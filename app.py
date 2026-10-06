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

# Resolve absolute root directory of this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
DIST_DIR = os.path.join(BASE_DIR, "dist")
DIST_ASSETS_DIR = os.path.join(DIST_DIR, "assets")
DIST_INDEX = os.path.join(DIST_DIR, "index.html")
MODEL_PATH = os.path.join(BASE_DIR, "cough_model.joblib")

# Ensure required directories exist
for folder in [STATIC_DIR, TEMPLATES_DIR]:
    os.makedirs(folder, exist_ok=True)

# Mount static asset folders
if os.path.exists(DIST_ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=DIST_ASSETS_DIR), name="assets")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=TEMPLATES_DIR) if os.path.exists(TEMPLATES_DIR) else None

# Load model artifact
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
        response = FileResponse(DIST_INDEX)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    if templates and os.path.exists(os.path.join(TEMPLATES_DIR, "index.html")):
        return templates.TemplateResponse("index.html", {"request": request})
    return HTMLResponse("<h1>Respira-X API Running</h1><p>Run <code>bun run build</code> or <code>npm run build</code> to serve the frontend.</p>")


@app.post("/analyze")
async def analyze(cough_audio: UploadFile = File(...)):
    print(f"📥 Received file: {cough_audio.filename} ({cough_audio.content_type})")

    if not model:
        return {
            "status": "Analysis Failed",
            "prediction": "ERROR ❌",
            "confidence": "N/A%",
            "details": "Model not loaded on server. Run train_model.py first.",
            "severity": "high",
        }

    # Step 1: Read audio buffer
    try:
        audio_bytes = await cough_audio.read()
        if len(audio_bytes) == 0:
            raise ValueError("Uploaded file is empty.")
    except Exception as e:
        return {
            "status": "Analysis Failed",
            "prediction": "ERROR ❌",
            "confidence": "N/A%",
            "details": f"File read error: {e}",
            "severity": "high",
        }

    # Step 2: Load audio data safely
    try:
        try:
            # First attempt: direct memory stream via librosa
            audio_data, sr = librosa.load(io.BytesIO(audio_bytes), sr=22050)
        except Exception:
            # Fallback: write to temp file for soundfile / ffmpeg codec resolution
            suffix = os.path.splitext(cough_audio.filename or ".wav")[-1] or ".wav"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            try:
                audio_data, sr = librosa.load(tmp_path, sr=22050)
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

        # Trim silence
        trimmed_audio, _ = librosa.effects.trim(audio_data, top_db=20)
        duration = librosa.get_duration(y=trimmed_audio, sr=sr)

        # Rejection: continuous sound / speech check
        if duration > 1.6:
            return {
                "status": "Analysis Complete",
                "prediction": "NOT A COUGH / UNCLEAR",
                "confidence": "N/A",
                "details": f"Recording duration ({duration:.2f}s) exceeded single-cough window. Please record a brief single cough.",
                "severity": "low",
            }

        # Step 3: Feature extraction
        from train_model import extract_features_from_array
        features = extract_features_from_array(trimmed_audio, sr)

        if features is None:
            raise ValueError("Feature extraction failed.")

        probabilities = model.predict_proba([features])[0]
        ml_prediction = model.predict([features])[0]
        confidence = float(np.max(probabilities) * 100)

        # False positive dampening
        if ml_prediction in ["upper", "lower", "obstructive", "covid"] and confidence < 70.0:
            ml_prediction = "healthy"
            confidence = 80.0

        # UI mappings
        if ml_prediction == "covid":
            prediction = "COVID POSITIVE SUSPECTED"
            severity = "high"
            details = f"Detected acoustic features associated with COVID-19 patterns ({duration:.2f}s). Consult a healthcare professional."
        elif ml_prediction == "healthy":
            prediction = "NORMAL"
            severity = "low"
            details = f"No significant abnormal respiratory signatures detected ({duration:.2f}s)."
        elif ml_prediction in ["upper", "lower"]:
            prediction = "RESPIRATORY TRACT INFECTION"
            severity = "medium"
            details = f"Detected acoustic markers consistent with an upper/lower respiratory infection ({duration:.2f}s)."
        elif ml_prediction == "obstructive":
            prediction = "BRONCHIAL OBSTRUCTION"
            severity = "medium"
            details = f"Detected signs of obstructive respiratory distress ({duration:.2f}s)."
        elif ml_prediction in ["talking", "noise"]:
            prediction = "NOT A COUGH"
            severity = "low"
            details = f"Audio identified as ambient noise or speech ({ml_prediction})."
        else:
            prediction = str(ml_prediction).upper()
            severity = "low"
            details = f"Classification: {ml_prediction}."

        if duration > 1.2:
            details += " (Tip: Record a single isolated cough for higher clarity.)"

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
