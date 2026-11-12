from pathlib import Path
from urllib.parse import quote
import yaml


# setting path to find config.yaml file
CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "config.yaml"


def load_config(path: Path = CONFIG_PATH) -> dict:

    if not path.exists():
        raise FileNotFoundError(
            f"Config not found at {path}."
        )
    with open(path) as f:
        return yaml.safe_load(f)


def build_stream_url(cfg: dict) -> str:
    cam = cfg["camera"]
    scheme = "https" if cam.get("use_https") else "http"
    auth = ""
    if cam.get("username"):
        auth = f"{quote(cam['username'])}:{quote(cam.get('password', ''))}@"
        
    return f"{scheme}://{auth}{cam['host']}:{cam['port']}{cam['path']}"