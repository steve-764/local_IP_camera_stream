# IP Camera Viewer

A Python tool that shows a live video feed from an authorized phone camera running the **IP Webcam** Android app, over your local network. It adds an on-screen overlay, and lets you take screenshots and record video.


## Setup

1. **Start the camera.** In the IP Webcam app, tap *Start server* and note the address it shows (for example `192.168.1.50:8080`). The phone and your computer must be on the same Wi-Fi network.
2. **Install the dependencies** (Python 3.8+):
   ```
   pip install -r requirements.txt
   ```
3. **Create your config file** by copying the template:
   ```
   cp config/config.example.yaml config/config.yaml
   ```
   Then edit `config/config.yaml`:
   ```yaml
   camera:
     name: Living Room Phone   # shown in the overlay
     host: 192.168.1.50        # just the address, no http://
     port: 8080
     path: /video              # IP Webcam's MJPEG stream
     username: ""              # only if you set a login in the app
     password: ""
     use_https: false

   display:
     width: 800                # frames are resized to this width
   ```
  

## Run

```
python main.py
```

A window opens with the live feed. Click it so it has keyboard focus, then use the keys below.

## Controls

| Key | What it does |
|-----|--------------|
| **Esc** | Quits. It finishes any recording in progress, releases the camera and closes the window. |
| **S** | Saves the current frame to `screenshots/` and shows a short confirmation. |
| **R** | Starts a recording. Press it again to stop and save. A red dot and `REC mm:ss` show while recording. |

- Screenshots are saved as `screenshots/screenshot_YYYYMMDD_HHMMSS_mmm.png`.
- Recordings are saved as `recordings/recording_YYYYMMDD_HHMMSS_mmm.mp4`.
- Both folders are created automatically if missing.
- Filenames include the time down to the **millisecond**, so a new file never overwrites an old one.
- Pressing Ctrl+C in the terminal also shuts down safely.

## What each file does

```
ipcam-project/
├── config/
│   └── config.yaml           your real settings (gitignored, you create it)
├── src/ipcam/
│   ├── config.py             loads and validates the config, builds the stream URL
│   ├── stream.py             checks the camera answers, then opens the video stream
│   └── recorder.py           writes recorded frames on a background thread
├── main.py                   the display loop, overlay, screenshots, reconnects, shutdown
├── requirements.txt          opencv-python, pyyaml, requests
└── .gitignore                keeps config.yaml, screenshots and recordings out of git
```

## Why it works this way

**Settings and credentials live in a config file.** The camera address and password are kept out of the source code, so the code can be shared or committed without leaking them. `config.yaml` is gitignored. Error messages only ever print `host:port`, never the full URL, so the password doesn't end up in terminals or logs.

**The camera is checked with Requests before OpenCV opens it.** OpenCV only reports "could not open", with no reason. A quick HTTP request (3-second timeout, headers only) tells the failures apart: a timeout means the phone is off or on another network, a refused connection means the server or port is wrong, 401 means a bad login, and 404 means a wrong path.

**Frames are resized by width, keeping the aspect ratio.** The new height is `round(height × new_width / width)`. For example, 1920×1080 resized to width 960 gives 960×540.

**FPS is estimated from the time between frames.** Each frame, `fps = 1 / (time since previous frame)`, using `time.perf_counter()`. A single reading jumps around because Wi-Fi delivery and decoding time vary, so the value is smoothed: `fps = 0.9 × old + 0.1 × new`. The timer is reset after a reconnect so the gap doesn't cause a false spike.

**The clock text updates once per second.** The date and time string is rebuilt only when the wall-clock second changes and reused for the frames in between, which saves a formatting call on every frame.

**Recording runs on a separate thread.** Video encoding is the heaviest step in the loop. The main loop only copies each frame onto a queue, and a worker thread encodes and writes it, so the live display stays smooth. The queue holds 60 frames; if the encoder falls behind, frames are dropped (and counted) rather than slowing the display. Frames are copied before queueing so the REC badge is never burned into the video.

**Reconnects are limited.** If the connection drops, the program tries up to 5 times, 2 seconds apart, then gives up with a clear message. That rides out a short Wi-Fi blip without retrying forever on a camera that is really gone. Esc cancels the wait.

**Cleanup always runs.** The `finally` block releases the camera, finishes the recording and closes all windows on Esc, Ctrl+C, giving up on reconnecting, or any error. This matters most for recordings: an MP4 is only finalized when it is closed, so an unreleased file can be unplayable.


## Troubleshooting

| Message | What to check |
|---------|---------------|
| Config file not found / Missing `camera.x` | Copy `config.example.yaml` to `config.yaml` and fill it in. |
| Timed out waiting for the camera | Phone is off or asleep, on a different network, or the IP is wrong. |
| Nothing answered at host:port | The IP Webcam server isn't started, or the port is wrong. |
| Rejected the username or password | Match the login set in the IP Webcam app. |
| Path was not found / not a video stream | Set `camera.path` to `/video`. |
| Timeouts or crashes opening the stream | Use OpenCV 4.5.2 or newer. |

## Notes

- Recordings use a fixed frame rate taken at the moment you start, so if frames are dropped the video may play slightly faster than real time.
- A screenshot is taken from the displayed frame, so it includes the overlay text, and the REC badge if you are recording.