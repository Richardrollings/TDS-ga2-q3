from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path
import yaml
import os

# Load .env from project directory
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------
# Defaults
# -----------------------

config = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}


def to_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).lower() in ("true", "1", "yes", "on")


def convert(key, value):
    if key in ("port", "workers"):
        return int(value)

    if key == "debug":
        return to_bool(value)

    return str(value)


@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):
    cfg = config.copy()

    # ---------------- YAML ----------------

    yaml_file = Path(__file__).parent / "config.development.yaml"

    if yaml_file.exists():
        with open(yaml_file) as f:
            y = yaml.safe_load(f) or {}

        for k, v in y.items():
            cfg[k] = convert(k, v)

    # ---------------- ENV ----------------

    mapping = {
        "APP_PORT": "port",
        "NUM_WORKERS": "workers",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key",
    }

    for env_name, key in mapping.items():
        value = os.getenv(env_name)

        if value is not None:
            cfg[key] = convert(key, value)

    # ---------------- CLI ----------------

    for item in set:
        if "=" not in item:
            continue

        key, value = item.split("=", 1)

        cfg[key] = convert(key, value)

    # Mask secret
    cfg["api_key"] = "****"

    return cfg
