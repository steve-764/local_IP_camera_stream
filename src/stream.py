import cv2
import requests
from requests import exceptions as rex

from .config import ConfigError

OPEN_TIMEOUT_MS = 6000
READ_TIMEOUT_MS = 6000
CHECK_TIMEOUT = (3, 3)


def check_camera(url: str, label: str) -> None:
    """Ask the camera for its headers only, and turn any failure into a clear message.

    Never put str(e) in a message: requests includes the full URL, password and all.
    """
    try:
        # stream=True fetches the headers without downloading the video body
        with requests.get(url, stream=True, timeout=CHECK_TIMEOUT) as resp:
            status = resp.status_code
    except (rex.InvalidURL, rex.MissingSchema, rex.InvalidSchema):
        raise ConfigError("The camera URL built from your config is not valid. Check camera.host, port and path.") from None
    except rex.Timeout:
        raise ConnectionError(
            f"Timed out waiting for the camera at {label}. The phone may be off or asleep, "
            "or on a different network, or the address is wrong."
        ) from None
    except rex.SSLError:
        raise ConnectionError(
            f"Secure connection to {label} failed. IP Webcam serves plain http by default, "
            "so try use_https: false."
        ) from None
    except rex.ConnectionError:
        raise ConnectionError(
            f"Nothing answered at {label}. Check that IP Webcam's server is started, "
            "the port is correct, and both devices are on the same network."
        ) from None
    except rex.RequestException:
        raise ConnectionError(f"The request to the camera at {label} failed.") from None

    if status in (401, 403):
        raise ConnectionError(f"The camera at {label} rejected the username or password.")
    if status == 404:
        raise ConnectionError(f"The camera at {label} is reachable, but camera.path was not found. IP Webcam uses /video.")
    if status >= 400:
        raise ConnectionError(f"The camera at {label} answered with HTTP error {status}.")


def open_stream(url: str , label: str) -> cv2.VideoCapture:
    params = [
        cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, OPEN_TIMEOUT_MS,
        cv2.CAP_PROP_READ_TIMEOUT_MSEC, READ_TIMEOUT_MS,
    ]
    cap = cv2.VideoCapture(url)
    if not cap.isOpened():
        cap.release()
        raise ConnectionError("Cannot access camera stream. Ensure the camera and access devide are on the same network.")
    return cap
