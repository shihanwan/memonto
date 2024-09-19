import os
from dotenv import load_dotenv

load_dotenv()

MODEL_PROVIDER = os.getenv("MODEL_PROVIDER")
MODEL_NAME = os.getenv("MODEL_NAME")
MODEL_API_KEY = os.getenv("MODEL_API_KEY")
MODEL_TEMPERATURE = os.getenv("MODEL_TEMPERATURE")

DEBUG_MODE = os.getenv("DEBUG_MODE").lower in ["true", "True"]
