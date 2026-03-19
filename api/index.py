import sys
import os

# Add the project root to the python path so it can import app and train_model
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
