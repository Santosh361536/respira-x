import sys
import os
import glob
import io
import soundfile as sf
import librosa

# Dynamically locate project root and dataset directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "dataset_1sec")
FALLBACK_FILE = os.path.join(BASE_DIR, "test.wav")

# Find a test file dynamically
found_files = glob.glob(os.path.join(DATASET_PATH, "**/*.wav"), recursive=True)

if found_files:
    path = found_files[0]
    print(f"✅ Found sample audio file in dataset: {path}")
elif os.path.exists(FALLBACK_FILE):
    path = FALLBACK_FILE
    print(f"⚠️ No files found in dataset. Falling back to root sample: {path}")
else:
    print(f"❌ Error: Neither dataset files in '{DATASET_PATH}' nor '{FALLBACK_FILE}' were found.")
    sys.exit(1)

print("\n--- 1. Testing soundfile ---")
try:
    data, sr = sf.read(path, dtype='float32')
    print(f"✅ soundfile success (Sample Rate: {sr}, Shape: {data.shape})")
except Exception as e:
    print(f"❌ soundfile failed: {e}")

print("\n--- 2. Testing librosa ---")
try:
    data, sr = librosa.load(path, sr=22050)
    print(f"✅ librosa success (Sample Rate: {sr}, Shape: {data.shape})")
except Exception as e:
    print(f"❌ librosa failed: {e}")

print("\n--- 3. Testing BytesIO Stream ---")
try:
    with open(path, 'rb') as f:
        audio_bytes = f.read()

    print("Testing soundfile BytesIO...")
    try:
        data, sr = sf.read(io.BytesIO(audio_bytes), dtype='float32')
        print("✅ soundfile BytesIO success")
    except Exception as e:
        print(f"❌ soundfile BytesIO failed: {e}")

    print("Testing librosa BytesIO...")
    try:
        data, sr = librosa.load(io.BytesIO(audio_bytes), sr=22050)
        print("✅ librosa BytesIO success")
    except Exception as e:
        print(f"❌ librosa BytesIO failed: {e}")

except Exception as e:
    print(f"BytesIO stream test failed: {e}")
