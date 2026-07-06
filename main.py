from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import yaml
import os

load_dotenv()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------
# Hardcoded defaults
# -----------------------
defaults = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}


def to_bool(v):
    if isinstance(v, bool):
        return v
    return str(v).lower() in ["true", "1", "yes", "on"]


def coerce(key, value):
    if key in ["port", "workers"]:
        return int(value)

    if key == "debug":
        return to_bool(value)

    return str(value)


@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):
    config = defaults.copy()

    # YAML layer
    if os.path.exists("config.development.yaml"):
        with open("config.development.yaml") as f:
            yaml_cfg = yaml.safe_load(f) or {}

        for k, v in yaml_cfg.items():
            config[k] = coerce(k, v)

    # .env layer
    mapping = {
        "APP_PORT": "port",
        "NUM_WORKERS": "workers",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key",
    }

    for env_key, cfg_key in mapping.items():
        val = os.getenv(env_key)
        if val is not None:
            config[cfg_key] = coerce(cfg_key, val)

    # OS APP_* env vars
    # (already available through os.getenv; same mapping covers them)

    # CLI overrides
    for item in set:
        if "=" not in item:
            continue

        key, value = item.split("=", 1)

        if key == "workers":
            config["workers"] = coerce("workers", value)

        elif key == "port":
            config["port"] = coerce("port", value)

        elif key == "debug":
            config["debug"] = coerce("debug", value)

        elif key == "log_level":
            config["log_level"] = str(value)

        elif key == "api_key":
            config["api_key"] = value

        else:
            config[key] = str(value)

    # Mask secret
    config["api_key"] = "****"

    return config
