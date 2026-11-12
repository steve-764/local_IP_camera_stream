from pathlib import Path
from urllib.parse import quote
import yaml


# setting path to find config.yaml file
CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "config.yaml"


class ConfigError(Exception):
    """The config file is missing, or holds unusable values"""


def load_config(path: Path = CONFIG_PATH) -> dict:
    # checking or config file
    if not path.exists():
        raise FileNotFoundError(
            f"Config not found at {path}."
        )
    try:
        with open(path) as f:
            return yaml.safe_load(f)
    except yaml.YAMLError:
        raise ConfigError(f"{path} is not a valid YAML file. Verify its formatting ")
    return validate_config(cfg)


# validating data in the YAML file
def validate_config(cfg) -> dict:
    # checking camera object exists
    if not isinstance(cfg, dict) or not isinstance(cfg.get("camera"), dict):
        raise ConfigError("Config needs a 'camera name' section.")
    cam = cfg["camera"]

    # validating expected keys exist in the camera object
    for key in ("name", "host", "port", "path"):
        if cam.get(key) in (None, ""):
            raise ConfigError(f"Missing 'camera.{key}' in the config file.")
    
    # validating host format
    host = str(cam["host"])
    if any(bad in host for bad in ("/", "@", " ")):
        raise ConfigError(f"Invalid camera.host '{host}'. Use address format in config.example.yaml ")

    # validating if port numbers are valid
    port = cam["port"]
    if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
        raise ConfigError(f"Invalid camera.port '{port}'. Port number must be between 1 and 65535")

    # validating if path format valid
    if not str(cam["path"]).startswith("/"):
        raise ConfigError(f"Invalid camera.path '{cam['path']}")

    # validating frame width, reject if not int or < 0
    width = (cfg.get("display") or {}).get("width")
    if isinstance(width, bool) or not isinstance(width, int) or width <= 0:
        raise ConfigError("Display width must be an integer greater than 0")

    return cfg

    
def build_stream_url(cfg: dict) -> str:
    cam = cfg["camera"]
    scheme = "https" if cam.get("use_https") else "http"
    auth = ""
    if cam.get("username"):
        auth = f"{quote(cam['username'])}:{quote(cam.get('password', ''))}@"

    return f"{scheme}://{auth}{cam['host']}:{cam['port']}{cam['path']}"


def camera_label(cfg: dict) -> str:
    cam = cfg["camera"]
    return f"{cam['host']}:{cam['port']}"