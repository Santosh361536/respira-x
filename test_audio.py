import sys
import os
import soundfile as sf
import librosa
import io
# Find a test file in the dataset if the hardcoded one is missing
import glob
DATASET_PATH = "/Users/tadisaisantosh/Downloads/dataset_1sec"
path = "/Users/tadisaisantosh/Downloads/dataset_1sec/covid/5131b118-88df-4d26-90bb-85b726fe0b5a_1.wav"

if not os.path.exists(path):
    print(f"⚠️ Hardcoded path {path} not found. Searching in {DATASET_PATH}...")
    found_files = glob.glob(os.path.join(DATASET_PATH, "**/*.wav"), recursive=True)
    if found_files:
        path = found_files[0]
        print(f"✅ Found alternative file: {path}")
    else:
        # Final fallback to test.wav in current dir
        path = "test.wav"
        print(f"⚠️ No files found in dataset. Falling back to: {path}")

print("Testing soundfile...")
try:
    data, sr = sf.read(path)
    print("✅ soundfile success")
except Exception as e:
    print(f"❌ soundfile failed: {e}")

print("Testing librosa...")
try:
    data, sr = librosa.load(path)
    print("✅ librosa success")
except Exception as e:
    print(f"❌ librosa failed: {e}")

print("\n=== BYTESIO TEST ===")
try:
    with open(path, 'rb') as f:
        audio_bytes = f.read()
    
    print("Testing soundfile BytesIO...")
    try:
        data, sr = sf.read(io.BytesIO(audio_bytes))
        print("✅ soundfile BytesIO success")
    except:
        print("❌ soundfile BytesIO failed (expected for some formats)")
    
    print("Testing librosa BytesIO...")
    data, sr = librosa.load(io.BytesIO(audio_bytes))
    print("✅ librosa BytesIO success")
except Exception as e:
    print(f"Test failed: {e}")
