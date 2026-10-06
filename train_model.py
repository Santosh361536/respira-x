import os
import sys

try:
    import sklearn
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report, accuracy_score
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline
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
    print("!" * 60 + "\n")
    sys.exit(1)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "dataset_1sec")
MODEL_OUTPUT_PATH = os.path.join(BASE_DIR, "cough_model.joblib")


def extract_features_from_array(audio_data, sample_rate):
    try:
        if np.max(np.abs(audio_data)) > 0:
            audio_data = audio_data / np.max(np.abs(audio_data))

        # 1. MFCCs and Temporal Deltas
        mfccs = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=13)
        mfcc_means = np.mean(mfccs, axis=1)
        mfcc_stds = np.std(mfccs, axis=1)
        delta_mfccs = librosa.feature.delta(mfccs)
        delta2_mfccs = librosa.feature.delta(mfccs, order=2)
        delta_means = np.mean(delta_mfccs, axis=1)
        delta2_means = np.mean(delta2_mfccs, axis=1)

        # 2. Spectral Features
        spectral_centroid = librosa.feature.spectral_centroid(y=audio_data, sr=sample_rate)[0]
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=audio_data, sr=sample_rate)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=audio_data, sr=sample_rate, roll_percent=0.85)[0]
        spectral_contrast = np.mean(librosa.feature.spectral_contrast(y=audio_data, sr=sample_rate), axis=1)

        # 3. Time-Domain / Energy Features
        zero_crossings = librosa.feature.zero_crossing_rate(audio_data)[0]
        rms = librosa.feature.rms(y=audio_data)[0]

        # 4. Harmonic vs Percussive Ratio (Separating speech from coughs)
        harmonic, percussive = librosa.effects.hpss(audio_data)
        harmonic_ratio = np.mean(rms) / (np.mean(librosa.feature.rms(y=harmonic)[0]) + 1e-6)

        # 5. Onset and Flux
        onset_env = librosa.onset.onset_strength(y=audio_data, sr=sample_rate)
        spectral_flux = np.mean(np.diff(np.abs(np.hstack(([0], onset_env)))))

        # 6. Fundamental Frequency / Pitch
        try:
            f0 = librosa.yin(audio_data, fmin=50, fmax=500, sr=sample_rate)
            pitch_freq = np.nanmean(f0)
            if np.isnan(pitch_freq):
                pitch_freq = 0.0
        except Exception:
            pitch_freq = 0.0

        features = np.concatenate((
            mfcc_means,
            mfcc_stds,
            delta_means,
            delta2_means,
            [np.mean(spectral_centroid)],
            [np.std(spectral_centroid)],
            [np.mean(spectral_bandwidth)],
            [np.mean(spectral_rolloff)],
            spectral_contrast,
            [np.mean(zero_crossings)],
            [np.mean(rms)],
            [np.std(rms)],
            [harmonic_ratio],
            [spectral_flux],
            [pitch_freq]
        ))

        return np.nan_to_num(features)
    except Exception:
        return None


def extract_features(file_path):
    try:
        audio_data, sample_rate = sf.read(file_path, dtype='float32')
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)

        if sample_rate != 22050:
            audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=22050)
            sample_rate = 22050

        trimmed, _ = librosa.effects.trim(audio_data, top_db=25)
        if len(trimmed) > 0:
            audio_data = trimmed

        return extract_features_from_array(audio_data, sample_rate)
    except Exception:
        return None


def main():
    if not os.path.exists(DATASET_PATH):
        print(f"❌ Error: Dataset directory not found at '{DATASET_PATH}'")
        sys.exit(1)

    X, y = [], []
    classes = ["covid", "healthy", "lower", "obstructive", "upper", "talking", "noise"]

    print("🔄 Extracting rich acoustic features...")
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
    print(f"\n✅ {len(X)} valid samples extracted across available classes.")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('classifier', RandomForestClassifier(
            n_estimators=300,
            max_depth=20,
            min_samples_split=4,
            class_weight="balanced_subsample",
            random_state=42,
            n_jobs=-1
        ))
    ])

    print("🌲 Training Balanced Ensemble Classifier...")
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    print(f"\n📊 Test Accuracy: {accuracy_score(y_test, y_pred):.4f}\n")
    print(classification_report(y_test, y_pred, zero_division=0))

    joblib.dump(pipeline, MODEL_OUTPUT_PATH)
    print(f"💾 Model pipeline saved successfully to: {MODEL_OUTPUT_PATH}")
    return pipeline


if __name__ == "__main__":
    main()
