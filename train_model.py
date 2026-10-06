import os
import sys

try:
    import sklearn
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report, accuracy_score
    import librosa
    import numpy as np
    import joblib
    import soundfile as sf
except ImportError as e:
    missing_module = str(e).split("'")[-2] if "'" in str(e) else "required dependency"
    print("\n" + "!" * 60)
    print(f"❌ CRITICAL ERROR: {e}")
    print(f"It seems '{missing_module}' is not installed in your current environment.")
    print(f"Please run: pip install {missing_module}")
    print("\n💡 TIP: If you are using a virtual environment, make sure it's activated:")
    print("   source venv/bin/activate  (Mac/Linux)")
    print("   venv\\Scripts\\activate     (Windows)")
    print("\n💡 TIP: If using VS Code, press 'Cmd+Shift+P', type 'Python: Select Interpreter',")
    print("   and select the one that points to your 'venv'.")
    print("!" * 60 + "\n")
    sys.exit(1)

# Dynamically locate dataset_1sec in the same directory as this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "dataset_1sec")
MODEL_OUTPUT_PATH = os.path.join(BASE_DIR, "cough_model.joblib")


def extract_features_from_array(audio_data, sample_rate):
    try:
        # 13 MFCC coefficients
        mfccs = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=13)
        mfcc_means = np.mean(mfccs, axis=1)

        # Spectral and temporal features
        spectral_centroid = librosa.feature.spectral_centroid(y=audio_data, sr=sample_rate)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=audio_data, sr=sample_rate)[0]
        zero_crossings = librosa.feature.zero_crossing_rate(audio_data)[0]
        rms = librosa.feature.rms(y=audio_data)[0]
        onset_env = librosa.onset.onset_strength(y=audio_data, sr=sample_rate)
        spectral_flux = np.mean(np.diff(np.abs(np.hstack(([0], onset_env)))))
        pitch_freq = np.mean(librosa.yin(audio_data, fmin=50, fmax=500, sr=sample_rate))

        features = np.concatenate((
            mfcc_means,
            [np.mean(spectral_centroid)],
            [np.mean(spectral_rolloff)],
            [np.mean(zero_crossings)],
            [np.mean(rms)],
            [spectral_flux],
            [pitch_freq]
        ))
        return np.nan_to_num(features)
    except Exception as err:
        return None


def extract_features(file_path):
    try:
        audio_data, sample_rate = sf.read(file_path, dtype='float32')
        # Convert stereo to mono if necessary
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)

        # Standardize sample rate to 22050 Hz
        if sample_rate != 22050:
            audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=22050)
            sample_rate = 22050

        return extract_features_from_array(audio_data, sample_rate)
    except Exception as err:
        return None


def main():
    if not os.path.exists(DATASET_PATH):
        print(f"❌ Error: Dataset directory not found at '{DATASET_PATH}'")
        sys.exit(1)

    X, y = [], []
    classes = ["covid", "healthy", "lower", "obstructive", "upper", "talking", "noise"]

    print("🔄 Extracting features...")
    for label in classes:
        folder_path = os.path.join(DATASET_PATH, label)
        if not os.path.exists(folder_path):
            print(f"⚠️ Folder {folder_path} missing, skipping...")
            continue

        files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.wav', '.mp3'))]
        print(f"📁 Processing {len(files)} {label} files...")
        
        for file in files:
            file_full_path = os.path.join(folder_path, file)
            features = extract_features(file_full_path)
            if features is not None:
                X.append(features)
                y.append(label)

    if len(X) == 0:
        print("❌ No valid audio files processed. Check folder contents.")
        sys.exit(1)

    X, y = np.array(X), np.array(y)
    print(f"✅ {len(X)} valid samples extracted across classes.")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    print(f"\n📊 Test Accuracy: {accuracy_score(y_test, y_pred):.4f}\n")
    print(classification_report(y_test, y_pred))

    joblib.dump(clf, MODEL_OUTPUT_PATH)
    print(f"💾 Model saved successfully to: {MODEL_OUTPUT_PATH}")
    return clf


if __name__ == "__main__":
    main()
