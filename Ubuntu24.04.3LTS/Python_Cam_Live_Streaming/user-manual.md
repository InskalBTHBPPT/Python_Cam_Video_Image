# Panduan — Live Streaming Kamera (MJPEG)

Modul ini hanya untuk **menonton live stream** di browser. **Tidak ada** rekaman video, folder `recordings/`, atau penyimpanan file MP4/AVI.

Cocok untuk **Ubuntu 24.04 LTS** dan **Raspberry Pi** dengan webcam USB (V4L2).

---

## 1. Ringkasan

| Item | Nilai |
|------|--------|
| Skrip utama | `live_stream_mjpeg.py` |
| Protokol | HTTP + MJPEG (`multipart/x-mixed-replace`) |
| Port default | `8080` |
| URL contoh (Pi di LAN) | `http://10.45.2.103:8080/` |
| Resolusi default | 640×320 (MJPG), optimal untuk LAN/WiFi |
| Kualitas JPEG default | 50 |
| Target FPS default | 15 |
| Deteksi gerakan | **Aktif** (kotak hijau + teks `MOTION DETECTED`) |
| Rekaman ke disk | **Tidak** |

---

## 2. Persyaratan

- **OS:** Ubuntu 24.04 LTS (termasuk di Raspberry Pi 4).
- **Python:** 3.10 atau lebih baru.
- **Kamera:** perangkat V4L2 (`/dev/video0` umum untuk webcam USB pertama).
- **Jaringan:** PC/HP penonton harus satu LAN dengan Raspberry Pi (misalnya subnet `10.45.2.x`).
- **Grup pengguna:** anggota grup `video` (lihat §7).

Tidak perlu monitor di Pi — cukup SSH (headless).

---

## 3. Struktur folder

Semua path relatif terhadap folder **`Python_Cam_Live_Streaming`**:

| File / folder | Keterangan |
|---------------|------------|
| `livestream/` | Lingkungan virtual Python (venv) — dibuat Anda, jangan di-commit |
| `live_stream_mjpeg.py` | Server HTTP streaming |
| `motion_detector.py` | Deteksi gerakan (referensi `Level_3_Deteksi_Gerakan.py`) |
| `telegram_notifier.py` | Notifikasi Telegram saat gerakan |
| `telegram.env.example` | Contoh konfigurasi bot Telegram |
| `v4l2_camera.py` | Konfigurasi kamera Linux/Pi |
| `requirements.txt` | Dependensi pip (OpenCV + Flask) |
| `user-manual.md` | Dokumen ini |
| `README.md` | Ringkasan singkat |

---

## 4. Dependensi sistem (sekali)

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv v4l-utils
```

Opsional — diagnosa USB:

```bash
sudo apt install -y usbutils
```

---

## 5. Panduan lengkap: virtual environment (venv)

Venv memisahkan paket pip proyek ini dari sistem Python global. Disarankan di Raspberry Pi dan PC Ubuntu.

### 5.1 Nama dan lokasi venv

Panduan ini memakai nama folder venv **`livestream`** di dalam `Python_Cam_Live_Streaming`:

```text
Python_Cam_Live_Streaming/
  livestream/          ← venv (jangan commit ke Git)
  live_stream_mjpeg.py
  requirements.txt
  ...
```

Nama lain (misalnya `venv`) boleh dipakai — sesuaikan perintah `source` di bawah.

### 5.2 Buat venv (pertama kali)

```bash
cd /path/ke/Python_Cam_Live_Streaming
python3 -m venv livestream
```

Contoh path di Raspberry Pi:

```bash
cd ~/Python_Cam_Video_Image/Ubuntu24.04.3LTS/Python_Cam_Live_Streaming
python3 -m venv livestream
```

### 5.3 Aktifkan venv

**Linux / Raspberry Pi (bash):**

```bash
source livestream/bin/activate
```

Setelah aktif, prompt terminal biasanya diawali `(livestream)`.

**Windows (PowerShell)** — jika menguji skrip di PC:

```powershell
.\livestream\Scripts\Activate.ps1
```

**Windows (cmd):**

```cmd
livestream\Scripts\activate.bat
```

### 5.4 Pasang dependensi di dalam venv

Pastikan venv **sudah aktif** (`(livestream)` terlihat di prompt), lalu:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Verifikasi:

```bash
python -c "import cv2, flask; print('opencv', cv2.__version__); print('flask OK')"
```

### 5.5 Jalankan streaming (venv aktif)

```bash
python live_stream_mjpeg.py
```

Dari perangkat lain di LAN, buka browser:

```text
http://10.45.2.103:8080/
```

(Ganti `10.45.2.103` dengan IP LAN Raspberry Pi Anda: `hostname -I` atau `ip addr`.)

### 5.6 Keluar dari venv

```bash
deactivate
```

Prompt kembali normal (tanpa `(livestream)`). Server streaming harus sudah dihentikan (`Ctrl+C`) sebelum menutup terminal.

### 5.7 Tanpa perintah `activate` (opsional)

Anda bisa memanggil Python/pip langsung dari venv:

```bash
cd /path/ke/Python_Cam_Live_Streaming
livestream/bin/pip install -r requirements.txt
livestream/bin/python live_stream_mjpeg.py
```

Berguna untuk skrip systemd atau cron.

### 5.8 Venv sudah ada — update paket

```bash
cd /path/ke/Python_Cam_Live_Streaming
source livestream/bin/activate
pip install --upgrade pip
pip install -r requirements.txt --upgrade
```

### 5.9 Hapus dan buat ulang venv (jika rusak)

```bash
cd /path/ke/Python_Cam_Live_Streaming
deactivate 2>/dev/null || true
rm -rf livestream
python3 -m venv livestream
source livestream/bin/activate
pip install -r requirements.txt
```

### 5.10 Jangan commit venv ke Git

Folder `livestream/` ada di `.gitignore` repositori. Hanya commit skrip dan `requirements.txt`, bukan isi venv.

---

## 6. Menjalankan server streaming

### 6.1 Perintah default

```bash
cd /path/ke/Python_Cam_Live_Streaming
source livestream/bin/activate
python live_stream_mjpeg.py
```

### 6.2 Opsi baris perintah

| Opsi | Default | Keterangan |
|------|---------|------------|
| `--host` | `0.0.0.0` | Listen di semua interface LAN |
| `--port` | `8080` | Port HTTP |
| `--camera` | `0` | Indeks V4L2 (`/dev/video0` → 0) |
| `--width` | `640` | Lebar frame (piksel) |
| `--height` | `320` | Tinggi frame (piksel) |
| `--quality` | `50` | Kualitas JPEG 1–100 (lebih kecil = lebih ringan) |
| `--fps` | `15` | Target frame per detik |
| `--no-mirror` | — | Matikan cermin horizontal |
| `--no-motion` | — | Matikan deteksi gerakan (default: aktif) |
| `--min-motion-area` | otomatis | Luas kontur minimum (piksel²) |

Contoh:

```bash
python live_stream_mjpeg.py --port 5000 --camera 0
python live_stream_mjpeg.py --no-motion
```

### 6.3 Pengaturan performa

Default skrip sudah di-set untuk **LAN/WiFi tanpa lag** (640×320, kualitas 50, 15 fps). Cukup jalankan:

```bash
python live_stream_mjpeg.py
```

Setara dengan:

```bash
python live_stream_mjpeg.py --width 640 --height 320 --quality 50 --fps 15
```

Jika masih kurang lancar, turunkan lagi:

```bash
python live_stream_mjpeg.py --width 640 --height 320 --quality 40 --fps 12
```

Jika ingin gambar lebih tajam dan jaringan kuat:

```bash
python live_stream_mjpeg.py --width 640 --height 480 --quality 60 --fps 20
```

**Tips:** Satu tab browser saja; kabel Ethernet di Pi lebih stabil daripada WiFi.

### 6.4 Deteksi gerakan

Algoritma sama dengan `Level_3_Deteksi_Gerakan.py`:

1. Konversi ke grayscale + Gaussian blur  
2. `absdiff` dengan frame sebelumnya  
3. Threshold + dilate → kontur  
4. Kotak hijau pada area gerakan; teks **MOTION DETECTED** jika ada gerakan  

**Default aktif** — cukup jalankan `python live_stream_mjpeg.py`. Status gerakan tampil **langsung di video stream**:

- Overlay **MOTION ON** di pojok bawah
- Kotak hijau + teks **MOTION DETECTED** saat ada gerakan

Tidak ada polling HTTP berulang — log terminal sama tenang seperti versi tanpa deteksi (hanya `GET /` sekali dan `GET /video_feed` terus-menerus).

Matikan deteksi (stream lebih ringan):

```bash
python live_stream_mjpeg.py --no-motion
```

Sesuaikan sensitivitas — nilai lebih **kecil** = lebih sensitif:

```bash
python live_stream_mjpeg.py --min-motion-area 400
```

API status JSON (opsional — panggil manual jika perlu integrasi, tidak di-poll otomatis):

```text
GET http://10.45.2.103:8080/api/motion
→ {"enabled": true, "detected": false}
```

### 6.5 Notifikasi Telegram

Saat gerakan terdeteksi, skrip dapat mengirim pesan (dan foto frame) ke Telegram. **Cooldown default 60 detik** agar tidak spam.

#### Langkah 1 — Buat bot Telegram

1. Di Telegram, chat **@BotFather** → `/newbot` → ikuti petunjuk.
2. Simpan **token** bot (contoh: `7123456789:AAH...`).

#### Langkah 2 — Dapatkan Chat ID

1. Kirim pesan apa saja ke bot Anda (mis. `halo`).
2. Buka di browser (ganti `<TOKEN>`):

   ```text
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```

3. Cari `"chat":{"id":123456789}` — angka itu **Chat ID** Anda.

#### Langkah 3 — Buat file `telegram.env`

```bash
cd /path/ke/Python_Cam_Live_Streaming
cp telegram.env.example telegram.env
nano telegram.env
```

Isi:

```env
TELEGRAM_BOT_TOKEN=7123456789:AAHxxxxxxxx
TELEGRAM_CHAT_ID=123456789
TELEGRAM_COOLDOWN_SEC=60
TELEGRAM_SEND_PHOTO=1
```

**Jangan commit `telegram.env`** — sudah ada di `.gitignore`.

#### Langkah 4 — Jalankan server

```bash
python live_stream_mjpeg.py
```

Jika Telegram aktif, terminal menampilkan:

```text
  Telegram     : aktif (foto + teks, cooldown 60s)
```

Saat ada gerakan, HP Anda menerima foto + pesan `🚨 Gerakan terdeteksi`.

#### Opsi CLI Telegram

| Opsi | Keterangan |
|------|------------|
| `--telegram-env telegram.env` | File env (default: `telegram.env`) |
| `--telegram-token ...` | Override token |
| `--telegram-chat-id ...` | Override chat ID |
| `--telegram-cooldown 120` | Jeda antar notifikasi (detik) |
| `--telegram-text-only` | Hanya teks, tanpa foto |

Contoh tanpa file env:

```bash
python live_stream_mjpeg.py \
  --telegram-token "7123456789:AAHxxx" \
  --telegram-chat-id "123456789"
```

**Catatan:** Raspberry Pi perlu akses internet (HTTPS ke `api.telegram.org`).

### 6.6 Menonton stream

| Cara | URL |
|------|-----|
| Halaman web (disarankan) | `http://10.45.2.103:8080/` |
| Aliran MJPEG mentah | `http://10.45.2.103:8080/video_feed` |

VLC: *Media → Open Network Stream* → URL `video_feed` di atas.

### 6.7 Hentikan server

Di terminal Pi: **Ctrl+C**.

---

## 7. Memeriksa kamera sebelum streaming

```bash
lsusb
ls -l /dev/video*
v4l2-ctl --list-devices
```

Tes indeks dengan venv aktif:

```bash
source livestream/bin/activate
python3 -c "
import cv2
for i in range(4):
    cap = cv2.VideoCapture(i, cv2.CAP_V4L2)
    print(f'index {i}:', 'OK' if cap.isOpened() else 'gagal')
    cap.release()
"
```

Grup `video`:

```bash
groups
# Jika tidak ada 'video':
sudo usermod -aG video $USER
# Lalu logout/login atau reboot
```

---

## 8. SSH dan headless (Raspberry Pi)

Streaming **tidak** membutuhkan layar di Pi. Cukup SSH:

```bash
ssh user@10.45.2.103
cd /path/ke/Python_Cam_Live_Streaming
source livestream/bin/activate
python live_stream_mjpeg.py
```

Biarkan terminal terbuka selama stream berjalan, atau gunakan `screen` / `tmux` / systemd (di luar cakupan manual ini).

---

## 9. Firewall

Jika browser di PC tidak bisa membuka `http://10.45.2.103:8080/`:

```bash
sudo ufw allow 8080/tcp
sudo ufw status
```

Atau matikan ufw sementara untuk uji di lab tertutup (tidak disarankan di produksi).

---

## 10. Pemecahan masalah

### Kamera tidak terbuka

1. Pastikan tidak ada `GUI_Camera_App.py` atau skrip lain yang memakai kamera bersamaan.
2. Coba `--camera 0` lalu `1` hanya jika `v4l2-ctl --list-devices` menunjukkan perangkat capture di indeks itu.
3. Cek grup `video` (§7).

### Halaman web tidak bisa diakses dari PC

1. Ping Pi: `ping 10.45.2.103`
2. Pastikan server masih jalan di Pi (tidak `Ctrl+C`).
3. Cek firewall (§9).
4. Pastikan IP benar: `hostname -I` di Pi.

### Gambar terpotong / atas-bawah tertukar

Skrip memakai `v4l2_camera.py` (MJPG 640×480). Jika masih terjadi:

```bash
v4l2-ctl -d /dev/video0 --set-fmt-video=width=640,height=480,pixelformat=MJPG
```

### Port sudah dipakai

```bash
python live_stream_mjpeg.py --port 8081
```

### Stream lambat / putus-putus / tidak real-time

1. Default sudah optimal; jika masih lag, turunkan (§6.3):

   ```bash
   python live_stream_mjpeg.py --quality 40 --fps 12
   ```

2. Pastikan hanya **satu tab** browser yang membuka stream.
3. Coba **kabel Ethernet** di Pi jika memungkinkan (lebih stabil daripada WiFi).
4. Tutup skrip lain yang memakai kamera (`GUI_Camera_App.py`, dll.).

### Deteksi gerakan terlalu sensitif / banyak false alarm

Turunkan sensitivitas dengan **menaikkan** `--min-motion-area`:

```bash
python live_stream_mjpeg.py --min-motion-area 900
```

Atau matikan sementara: `--no-motion`.

### Telegram tidak terkirim

1. Pastikan `telegram.env` ada dan token/chat ID benar.
2. Pi harus online ke internet: `curl -I https://api.telegram.org`
3. Cek terminal: `[telegram] Gagal kirim: ...`
4. Pastikan Anda sudah chat bot minimal sekali (`/start`).
5. Turunkan cooldown jika uji: `--telegram-cooldown 10`

### `pip install` gagal di Raspberry Pi

Gunakan venv (§5), bukan `sudo pip install` ke sistem. Pastikan `python3 -m venv` berhasil dan arsitektur **aarch64** didukung wheel OpenCV.

---

## 11. Perbedaan dengan folder `PythonFIles`

| | `PythonFIles` | `Python_Cam_Live_Streaming` |
|--|----------------|------------------------------|
| Tujuan | Foto, rekam, deteksi, GUI | Hanya live stream |
| venv disarankan | `usbcamtest` (repo root) | `livestream` (di folder ini) |
| Dependensi | Besar (Qt, YOLO, …) | Kecil (OpenCV + Flask) |
| Rekaman | Ada | **Tidak** |

Kedua venv **boleh terpisah** — tidak perlu memakai `usbcamtest` untuk streaming.

---

## 12. Referensi cepat

```bash
# Buat & aktifkan venv
cd /path/ke/Python_Cam_Live_Streaming
python3 -m venv livestream
source livestream/bin/activate
pip install -r requirements.txt

# Jalankan (default 640×320, quality 50, 15 fps)
python live_stream_mjpeg.py

# Browser (ganti IP)
# http://10.45.2.103:8080/

# Keluar venv
deactivate
```

---

## 13. Keamanan

Stream tidak memakai kata sandi. Hanya untuk **jaringan lokal tepercaya**. Jangan expose port 8080 ke internet publik tanpa reverse proxy dan autentikasi.
