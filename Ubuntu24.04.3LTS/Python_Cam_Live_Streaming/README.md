# Python Cam Live Streaming

Live view kamera USB lewat browser (MJPEG over HTTP). **Tidak merekam** video ke disk.

| File | Keterangan |
|------|------------|
| `live_stream_mjpeg.py` | Server streaming |
| `v4l2_camera.py` | Buka kamera stabil di Linux/Pi (MJPG 640×480) |
| `requirements.txt` | OpenCV + Flask |
| `user-manual.md` | Panduan lengkap termasuk **venv** |

**Mulai cepat (Raspberry Pi, IP contoh `10.45.2.103`):**

```bash
cd /path/ke/Python_Cam_Live_Streaming
python3 -m venv livestream
source livestream/bin/activate
pip install -r requirements.txt
python live_stream_mjpeg.py
```

Buka di browser (LAN): **http://10.45.2.103:8080/**

Detail instalasi, venv, firewall, dan troubleshooting: lihat **`user-manual.md`**.
