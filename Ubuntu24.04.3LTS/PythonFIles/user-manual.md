# Panduan Pengguna — Python Camera GUI (Linux / Ubuntu 24.04)

Dokumen ini untuk versi Linux aplikasi `GUI_Camera_App.py` (termasuk Raspberry Pi dengan Ubuntu 24.04 LTS). Aplikasi memakai antarmuka grafis **PySide6** dan kamera lewat **OpenCV** dengan backend **V4L2**.

---

## 1. Ringkasan fitur

| Level | Nama | Fungsi singkat |
|-------|------|----------------|
| 1 | Capture Foto | Menyimpan satu frame ke file JPG |
| 2 | Rekam Video | Merekam aliran video ke file MP4 |
| 3 | Deteksi Gerakan | Kotak hijau pada area bergerak |
| 4 | Deteksi Warna | Deteksi merah / hijau / biru di ruang warna HSV |
| 6 | Deteksi Tangan/Jari | MediaPipe: landmark tangan + perkiraan jari terangkat |
| 7 | Deteksi Objek YOLO | Ultralytics YOLO pada frame kamera |

Tombol **Start Camera** / **Stop Camera** mengontrol aliran kamera. **Save Image** menyimpan foto dari frame terakhir. **Start Record** / **Stop Record** mengontrol rekaman video.

---

## 2. Persyaratan

- **OS:** Ubuntu 24.04 LTS (desktop atau varian kompatibel), termasuk pada Raspberry Pi jika mendukung paket yang sama.
- **Python:** 3.10 atau lebih baru (disarankan 3.12 sesuai repositori Ubuntu 24.04).
- **Tampilan grafis:** sesi X11 atau Wayland dengan dukungan Qt; aplikasi tidak dirancang untuk mode headless murni.
- **Kamera:** perangkat video V4L2 (misalnya `/dev/video0`). USB webcam biasanya langsung dikenali.

---

## 3. Instalasi dependensi sistem

Di terminal (contoh paket umum untuk OpenCV + Qt):

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv \
  libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 \
  libxcb-cursor0 libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 \
  libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-xfixes0
```

Paket `libxcb-cursor0` **wajib** untuk PySide6/Qt 6.5+ di X11 (tanpa ini GUI bisa gagal: *Could not load the Qt platform plugin "xcb"*).

Untuk alat diagnosa kamera (disarankan untuk §5):

```bash
sudo apt install -y v4l-utils usbutils
```

(`v4l-utils` → `v4l2-ctl`; `usbutils` → `lsusb`)

---

## 4. Lingkungan virtual dan pip

Masuk ke folder yang berisi `GUI_Camera_App.py` dan file `requirements*.txt`.

Panduan ini memakai venv bernama **`usbcamtest`**. Lokasi umum:

- `Python_Cam_Video_Image/usbcamtest/` (di root repo), atau
- `PythonFIles/usbcamtest/` (di samping skrip)

Nama folder bebas — sesuaikan perintah `source` di bawah.

### 4.1 Buat venv (semua platform)

```bash
cd /path/ke/Python_Cam_Video_Image
python3 -m venv usbcamtest
source usbcamtest/bin/activate
pip install --upgrade pip
```

Setelah aktif, prompt biasanya diawali `(usbcamtest)`. Keluar: `deactivate`.

Jangan commit folder `usbcamtest/` ke Git (sudah ada di `.gitignore` repo).

### 4.2 Raspberry Pi 4 — pemasangan aman (disarankan)

Di **aarch64** (Raspberry Pi), `pip install -r requirements.txt` saja sering menarik **PyTorch + CUDA** (`2.12+cu130`, paket `nvidia-*`). Itu memicu **`Illegal instruction (core dumped)`** saat Level 7 / `model.predict()`.

**Instalasi baru di Pi** — pakai file khusus Pi:

```bash
cd /path/ke/PythonFIles
source /path/ke/usbcamtest/bin/activate
pip install -r requirements-raspberrypi.txt
```

**Venv sudah ada / PyTorch salah** — jalankan skrip perbaikan (hapus torch CUDA, pasang torch CPU, tes YOLO):

```bash
cd /path/ke/PythonFIles
chmod +x fix_pytorch_raspi.sh
./fix_pytorch_raspi.sh
```

Skrip mencari venv aktif atau `usbcamtest` di root repo / `PythonFIles`, lalu:

1. Mencopot `torch`, `torchvision`, dan paket `nvidia-*` jika ada  
2. Memasang `torch==2.4.1` + `torchvision==0.19.1` (CPU, index PyTorch)  
3. Memasang dependensi lain dari `requirements-raspberrypi.txt`  
4. Menjalankan `check_yolo_torch.py` (tes inferensi singkat)

Verifikasi manual:

```bash
python -c "import torch; print(torch.__version__)"
# Harus: 2.4.1 (tanpa +cu)

python check_yolo_torch.py
# Harus: YOLO predict: OK
```

### 4.3 PC Ubuntu / x86_64 (bukan Raspberry Pi)

```bash
source usbcamtest/bin/activate
pip install -r requirements.txt
```

PyTorch dari Ultralytics biasanya cocok di PC. Tidak perlu `requirements-raspberrypi.txt` kecuali Anda ingin versi torch tertentu.

### 4.4 Tanpa perintah `activate`

```bash
/path/ke/usbcamtest/bin/pip install -r requirements-raspberrypi.txt
/path/ke/usbcamtest/bin/python GUI_Camera_App.py
```

**Catatan ARM:** PySide6 dan MediaPipe membutuhkan wheel **aarch64**. Jika `pip install` gagal, lihat dokumentasi resmi paket tersebut.

---

## 5. Memeriksa kamera USB di sistem

Lakukan pemeriksaan ini **sebelum** menjalankan aplikasi GUI, terutama saat kamera baru dipasang atau status **Kamera tidak terdeteksi**.

### 5.1 Urutan pemeriksaan (disarankan)

```text
1. Colokkan webcam USB ke port yang stabil (hindari hub rusak jika memungkinkan)
2. lsusb                    → muncul di bus USB?
3. ls -l /dev/video*        → ada node V4L2?
4. v4l2-ctl --list-devices  → nama perangkat & path /dev/videoN
5. (opsional) dmesg / journalctl → log driver saat colok
6. Tes OpenCV di venv       → indeks 0, 1, … bisa dibuka?
7. GUI_Camera_App.py        → Camera Index sesuai hasil tes
```

### 5.2 Bus USB — `lsusb`

```bash
lsusb
```

Cari baris yang menyerupai webcam, misalnya **Logitech**, **UVC**, **Webcam**, **PC CAMERA**, atau vendor kamera Anda. Jika **tidak ada** entri kamera tetapi keyboard/mouse terlihat, masalahnya biasanya di **kabel, port USB, atau perangkat kamera** — bukan di Python.

### 5.3 Node video V4L2 — `/dev/video*`

```bash
ls -l /dev/video*
```

| Hasil perintah | Artinya |
|----------------|---------|
| Ada `/dev/video0`, `/dev/video1`, … | Driver video mengenali perangkat; lanjut ke §5.4 |
| `No such file or directory` | Kamera belum terdeteksi, belum terpasang, atau driver gagal — cek §5.2 dan §5.5 |

Satu webcam sering membuat **beberapa** node (`video0`, `video1`, …). Untuk aplikasi ini, mulai dari indeks **0** di GUI; jika gagal, coba **1**, **2**, **3**.

### 5.4 Daftar perangkat V4L2 — `v4l2-ctl`

Pastikan `v4l-utils` sudah terpasang (§3), lalu:

```bash
v4l2-ctl --list-devices
```

Contoh keluaran normal:

```text
USB2.0 PC CAMERA (usb-xhci-hcd.0-1):
        /dev/video0
        /dev/video1
```

Jika muncul `Cannot open device /dev/video0` dan tidak ada daftar perangkat, kamera belum siap dipakai — ulangi §5.2–§5.5 setelah mencolok ulang.

### 5.5 Log kernel (setelah mencolok kamera)

Segera setelah mencolok USB:

```bash
dmesg | tail -30
```

Atau ikuti log langsung:

```bash
journalctl -k -f
```

(Ctrl+C untuk berhenti.) Cari baris seperti `uvcvideo`, `UVC`, atau `registered new video device` — itu tanda driver webcam UVC aktif.

### 5.6 Tes buka kamera dengan OpenCV (di venv)

Dari folder `PythonFIles`, dengan lingkungan `usbcamtest` aktif dan dependensi sudah terpasang:

```bash
source usbcamtest/bin/activate
python3 -c "
import cv2
for i in range(4):
    cap = cv2.VideoCapture(i, cv2.CAP_V4L2)
    print(f'index {i}:', 'OK' if cap.isOpened() else 'gagal')
    cap.release()
"
```

Indeks yang mencetak **OK** adalah kandidat **Camera Index** di GUI. Tes satu indeks saja:

```bash
python3 -c "import cv2; c=cv2.VideoCapture(0, cv2.CAP_V4L2); print('OK' if c.isOpened() else 'gagal'); c.release()"
```

### 5.7 Izin pengguna (grup `video`)

```bash
groups
```

Pastikan ada grup **`video`**. Jika tidak:

```bash
sudo usermod -aG video $USER
```

Lalu **logout dan login lagi** (atau reboot). Tanpa ini, `/dev/video*` bisa ada tetapi aplikasi gagal membuka kamera.

---

## 6. Menjalankan aplikasi

```bash
source usbcamtest/bin/activate
python GUI_Camera_App.py
```

### 6.1 Akses jarak jauh (SSH)

Jika Anda login lewat SSH tanpa monitor, set variabel tampilan ke sesi grafis yang aktif (ganti `:0` sesuai lingkungan):

```bash
export DISPLAY=:0
python GUI_Camera_App.py
```

Atau gunakan desktop jarak jauh (VNC, RDP, dll.) dan jalankan aplikasi dari sesi grafis tersebut.

### 6.2 Jendela GUI tidak muncul — error Qt `xcb`

Contoh pesan:

```text
xcb-cursor0 or libxcb-cursor0 is needed ...
Could not load the Qt platform plugin "xcb" in ".../cv2/qt/plugins"
```

**Langkah 1 — paket sistem (paling sering cukup):**

```bash
sudo apt update
sudo apt install -y libxcb-cursor0 libxkbcommon-x11-0
```

**Langkah 2 — jalankan dari sesi desktop** (bukan SSH tanpa DISPLAY):

```bash
export DISPLAY=:0
cd /path/ke/PythonFIles
source /path/ke/usbcamtest/bin/activate
python GUI_Camera_App.py
```

**Langkah 3 — paksa plugin PySide6 (bukan OpenCV):** skrip `GUI_Camera_App.py` sudah mengatur ini; pastikan file terbaru.

**Langkah 4 — Wayland vs X11:** jika masih gagal:

```bash
export QT_QPA_PLATFORM=xcb
python GUI_Camera_App.py
```

---

## 7. Struktur folder aplikasi

Semua path di bawah ini relatif terhadap folder tempat `GUI_Camera_App.py` berada (**APP_ROOT**).

| Folder / file | Keterangan |
|---------------|------------|
| `usbcamtest/` | Lingkungan virtual (biasanya di root repo). Jangan di-commit ke Git. |
| `requirements.txt` | Dependensi umum; **bukan** untuk Pi saja (Level 7). |
| `requirements-raspberrypi.txt` | Dependensi Pi 4: torch CPU + ultralytics (§4.2). |
| `fix_pytorch_raspi.sh` | Perbaiki PyTorch salah di venv yang sudah ada (§4.2). |
| `check_yolo_torch.py` | Tes torch + YOLO setelah pemasangan. |
| `v4l2_camera.py` | Buka kamera USB dengan MJPG 640×480 (hindari gambar terpotong). |
| `models/` | Model unduhan: `hand_landmarker.task` (Level 6), file `*.pt` YOLO (Level 7). Dibuat otomatis jika perlu. |
| `captures/` | Foto hasil **Save Image** (`gui_capture_YYYYMMDD_HHMMSS.jpg`). |
| `recordings/` | Video hasil rekaman (`gui_recording_YYYYMMDD_HHMMSS.mp4`, codec **mp4v**). |

---

## 8. Pengaturan di antarmuka

### 8.1 Pilih Level

Pilih level sebelum **Start Camera**. Mengganti level saat kamera aktif dinonaktifkan sampai kamera dihentikan.

### 8.2 Camera Index

Angka ini sesuai indeks perangkat V4L2 (biasanya **0** untuk kamera pertama di Raspberry Pi). Jika kamera tidak terbuka, coba **1**, **2**, atau **3**.

Untuk memastikan kamera terdeteksi sistem, ikuti **§5** (`lsusb`, `/dev/video*`, `v4l2-ctl`, tes OpenCV).

### 8.3 Level 4 — Warna

Pilih **semua**, **merah**, **hijau**, atau **biru**. Pencarian warna memakai ruang HSV pada frame BGR dari kamera.

### 8.4 Level 7 — YOLO

- **Model YOLO:** daftar file `*.pt` di folder `models/`. Jika model belum ada, Ultralytics dapat mengunduh saat pertama kali dimuat (perlu internet).
- **Objek YOLO:** filter kelas; **semua** berarti tanpa filter kelas.
- **Confidence YOLO:** ambang kepercayaan deteksi (0.25–0.90).

Ganti model YOLO hanya saat kamera **tidak** aktif.

---

## 9. Pratinjau dan orientasi

Frame ditampilkan **dicerminkan horizontal** (`flip` sumbu Y) agar terasa seperti cermin untuk webcam. Orientasi ini mempengaruhi tampilan dan file rekaman/capture.

---

## 10. Pemecahan masalah

### Kamera tidak terbuka

Ikuti langkah lengkap di **§5** terlebih dahulu. Ringkasannya:

1. Grup `video` dan logout/login (§5.7).
2. `lsusb` — kamera terlihat di USB? (§5.2)
3. `ls -l /dev/video*` — ada node video? (§5.3)
4. `v4l2-ctl --list-devices` (§5.4)
5. Tes indeks OpenCV (§5.6), lalu sesuaikan **Camera Index** di GUI.
6. Pastikan tidak ada aplikasi lain yang memegang kamera secara eksklusif.

### Pratinjau / foto terpotong — bagian atas & bawah tertukar

Gejala: sekitar **1/3 bawah** tampil di **atas**, **2/3 atas** di **bawah** (garis horizontal tajam). Bukan cermin horizontal (`flip` kiri–kanan).

Penyebab umum di **USB webcam + V4L2 + format YUYV** tanpa resolusi/format yang benar (buffer stride salah).

**Perbaikan di kode:** semua skrip memakai `v4l2_camera.py` — set **MJPG**, **640×480**, buffer 1, warmup frame.

**Jika masih terjadi**, di terminal:

```bash
v4l2-ctl -d /dev/video0 --list-formats-ext
v4l2-ctl -d /dev/video0 --set-fmt-video=width=640,height=480,pixelformat=MJPG
```

Lalu jalankan ulang GUI. Hindari indeks `/dev/video1` (sering bukan perangkat capture).

### Rekaman gagal atau file rusak

Writer memakai **MP4** + **mp4v**. Jika `VideoWriter` gagal dibuka, instal codec/paket multimedia sistem (misalnya paket `ffmpeg` terkait) dan coba lagi.

### Level 6 — MediaPipe

- Pastikan `mediapipe` terpasang.
- Model `hand_landmarker.task` diunduh otomatis ke `models/` saat pertama dipakai; butuh koneksi internet.

### Level 7 — `Illegal instruction (core dumped)`

Penyebab umum di **Raspberry Pi 4**: PyTorch dari pip bertanda **`+cu`** (CUDA) atau versi **2.11 / 2.12** yang memakai instruksi CPU tidak didukung Cortex-A72. Kamera bisa sudah aktif, lalu program crash saat inferensi pertama.

Gejala: keluaran berhenti setelah `Kamera aktif — index 0`, atau crash pada `model.predict()`.

**Perbaikan (venv sudah ada):**

```bash
cd /path/ke/PythonFIles
source /path/ke/usbcamtest/bin/activate
./fix_pytorch_raspi.sh
```

**Perbaikan manual:**

```bash
pip uninstall -y torch torchvision
pip list --format=freeze | sed -n 's/^\(nvidia-[^=]*\)==.*/\1/p' | xargs -r pip uninstall -y
pip install torch==2.4.1 torchvision==0.19.1 --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements-raspberrypi.txt
python check_yolo_torch.py
```

Pastikan `python -c "import torch; print(torch.__version__)"` menampilkan **`2.4.1`** tanpa **`+cu`**.

### Level 7 — YOLO lambat atau error memori

Gunakan model lebih kecil (`yolo11n.pt`). Skrip Level 7 memakai `imgsz=320` untuk Pi. Turunkan resolusi kamera di sistem jika perlu; 8 GB RAM Pi 4 biasanya cukup, bottleneck di CPU.

### Import / pip gagal

Periksa `python3 --version`, aktifkan venv, lalu:

- **Raspberry Pi:** `pip install -r requirements-raspberrypi.txt` atau `./fix_pytorch_raspi.sh`
- **PC x86_64:** `pip install -r requirements.txt`

Pada ARM, gunakan wheel resmi; hindari mencampur `requirements.txt` saja lalu menginstal ultralytics tanpa torch CPU yang dipin.

---

## 11. Referensi cepat perintah

```bash
# Cek kamera USB / V4L2 (§5)
lsusb
ls -l /dev/video*
v4l2-ctl --list-devices
dmesg | tail -30

# Tes OpenCV (venv aktif)
source usbcamtest/bin/activate
python3 -c "import cv2; c=cv2.VideoCapture(0, cv2.CAP_V4L2); print('OK' if c.isOpened() else 'gagal'); c.release()"

# Raspberry Pi: perbaiki / pasang PyTorch aman
cd /path/ke/PythonFIles && ./fix_pytorch_raspi.sh

# Tes torch + YOLO (Pi)
python check_yolo_torch.py

# Aktifkan venv usbcamtest dan jalankan GUI
cd /path/ke/PythonFIles && source ../usbcamtest/bin/activate && python GUI_Camera_App.py
```

---

## 12. Lisensi dan dependensi pihak ketiga

Fitur Level 6 dan 7 bergantung pada **MediaPipe** dan **Ultralytics YOLO**; patuhi lisensi masing-masing proyek dan model yang Anda unduh.

Jika ada bagian manual ini yang perlu disesuaikan untuk lingkungan laboratorium Anda (path tetap, proxy, atau kebijakan jaringan), salin bagian yang relevan ke dokumentasi internal Anda.
