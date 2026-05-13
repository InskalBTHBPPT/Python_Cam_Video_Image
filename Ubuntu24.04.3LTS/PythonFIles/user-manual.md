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
  libgl1 libglib2.0-0 libsm6 libxext6 libxrender1
```

Untuk alat diagnosa kamera (opsional):

```bash
sudo apt install -y v4l-utils
```

---

## 4. Lingkungan virtual dan pip

Masuk ke folder yang berisi `GUI_Camera_App.py` dan `requirements.txt`:

```bash
cd /path/ke/PythonFIles
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**Catatan Raspberry Pi (ARM):** beberapa paket (PySide6, MediaPipe, PyTorch lewat Ultralytics) membutuhkan wheel yang tersedia untuk arsitektur Anda. Jika `pip install` gagal, periksa dokumentasi resmi paket tersebut untuk **aarch64** / **arm64**.

---

## 5. Menjalankan aplikasi

```bash
source .venv/bin/activate
python GUI_Camera_App.py
```

### 5.1 Akses jarak jauh (SSH)

Jika Anda login lewat SSH tanpa monitor, set variabel tampilan ke sesi grafis yang aktif (ganti `:0` sesuai lingkungan):

```bash
export DISPLAY=:0
python GUI_Camera_App.py
```

Atau gunakan desktop jarak jauh (VNC, RDP, dll.) dan jalankan aplikasi dari sesi grafis tersebut.

### 5.2 Wayland vs X11

Jika jendela tidak tampil atau ada error Qt terkait platform, coba:

```bash
export QT_QPA_PLATFORM=xcb
python GUI_Camera_App.py
```

---

## 6. Struktur folder aplikasi

Semua path di bawah ini relatif terhadap folder tempat `GUI_Camera_App.py` berada (**APP_ROOT**).

| Folder / file | Keterangan |
|---------------|------------|
| `models/` | Model unduhan: `hand_landmarker.task` (Level 6), file `*.pt` YOLO (Level 7). Dibuat otomatis jika perlu. |
| `captures/` | Foto hasil **Save Image** (`gui_capture_YYYYMMDD_HHMMSS.jpg`). |
| `recordings/` | Video hasil rekaman (`gui_recording_YYYYMMDD_HHMMSS.mp4`, codec **mp4v**). |

---

## 7. Pengaturan di antarmuka

### 7.1 Pilih Level

Pilih level sebelum **Start Camera**. Mengganti level saat kamera aktif dinonaktifkan sampai kamera dihentikan.

### 7.2 Camera Index

Angka ini sesuai indeks perangkat V4L2 (biasanya **0** untuk kamera pertama di Raspberry Pi). Jika kamera tidak terbuka, coba **1**, **2**, atau **3**.

Memeriksa perangkat di terminal:

```bash
v4l2-ctl --list-devices
```

### 7.3 Level 4 — Warna

Pilih **semua**, **merah**, **hijau**, atau **biru**. Pencarian warna memakai ruang HSV pada frame BGR dari kamera.

### 7.4 Level 7 — YOLO

- **Model YOLO:** daftar file `*.pt` di folder `models/`. Jika model belum ada, Ultralytics dapat mengunduh saat pertama kali dimuat (perlu internet).
- **Objek YOLO:** filter kelas; **semua** berarti tanpa filter kelas.
- **Confidence YOLO:** ambang kepercayaan deteksi (0.25–0.90).

Ganti model YOLO hanya saat kamera **tidak** aktif.

---

## 8. Pratinjau dan orientasi

Frame ditampilkan **dicerminkan horizontal** (`flip` sumbu Y) agar terasa seperti cermin untuk webcam. Orientasi ini mempengaruhi tampilan dan file rekaman/capture.

---

## 9. Pemecahan masalah

### Kamera tidak terbuka

1. Pastikan pengguna ada di grup `video`: `groups` — jika perlu: `sudo usermod -aG video $USER` lalu logout/login.
2. Cek perangkat: `ls -l /dev/video*`.
3. Uji indeks lain di **Camera Index**.
4. Pastikan tidak ada aplikasi lain yang memegang kamera secara eksklusif.

### Rekaman gagal atau file rusak

Writer memakai **MP4** + **mp4v**. Jika `VideoWriter` gagal dibuka, instal codec/paket multimedia sistem (misalnya paket `ffmpeg` terkait) dan coba lagi.

### Level 6 — MediaPipe

- Pastikan `mediapipe` terpasang.
- Model `hand_landmarker.task` diunduh otomatis ke `models/` saat pertama dipakai; butuh koneksi internet.

### Level 7 — YOLO lambat atau error memori

Gunakan model lebih kecil (misalnya `yolo11n.pt`), turunkan resolusi kamera di pengaturan sistem/driver jika memungkinkan, atau jalankan di mesin dengan RAM lebih besar.

### Import / pip gagal

Periksa versi Python (`python3 --version`) dan gunakan `venv` yang sama dengan `pip install -r requirements.txt`. Pada ARM, gunakan wheel resmi atau sumber build yang didukung vendor.

---

## 10. Referensi cepat perintah

```bash
# Aktifkan venv dan jalankan
cd /path/ke/PythonFIles && source .venv/bin/activate && python GUI_Camera_App.py

# Daftar kamera V4L2
v4l2-ctl --list-devices
```

---

## 11. Lisensi dan dependensi pihak ketiga

Fitur Level 6 dan 7 bergantung pada **MediaPipe** dan **Ultralytics YOLO**; patuhi lisensi masing-masing proyek dan model yang Anda unduh.

Jika ada bagian manual ini yang perlu disesuaikan untuk lingkungan laboratorium Anda (path tetap, proxy, atau kebijakan jaringan), salin bagian yang relevan ke dokumentasi internal Anda.
