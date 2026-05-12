# Belajar Camera, Video, dan Motion Detection dengan Python

Folder ini berisi beberapa file latihan Python untuk belajar menggunakan USB camera dengan OpenCV.

Semua contoh memakai:

- `cv2.VideoCapture(1)` untuk membuka kamera eksternal.
- Folder `captures` untuk menyimpan foto.
- Folder `recordings` untuk menyimpan video.

Jika kamera tidak terbuka, ubah nilai kamera dari `1` menjadi `0` atau `2`.

```python
cap = cv2.VideoCapture(1)
```

## Level_1_Capture_Foto.py

File ini adalah latihan Level 1 untuk membuka USB camera dan menyimpan foto.

Fitur:

- Menampilkan live preview dari kamera.
- Menyimpan satu frame kamera sebagai file gambar `.jpg`.
- Membuat folder `captures` otomatis jika belum ada.

Tombol:

- `s` untuk menyimpan foto.
- `q` untuk keluar.

Cara menjalankan:

```bash
python PythonFile/Level_1_Capture_Foto.py
```

Output foto akan tersimpan seperti ini:

```text
captures/capture_20260512_091200.jpg
```

## Level_2_Rekam_Video.py

File ini adalah latihan Level 2 untuk merekam video dari USB camera.

Fitur:

- Menampilkan live preview dari kamera.
- Menyimpan foto seperti Level 1.
- Merekam video ke file `.avi`.
- Menampilkan tulisan `REC` saat video sedang direkam.
- Membuat folder `captures` dan `recordings` otomatis jika belum ada.

Tombol:

- `s` untuk menyimpan foto.
- `r` untuk mulai atau berhenti merekam video.
- `q` untuk keluar.

Cara menjalankan:

```bash
python PythonFile/Level_2_Rekam_Video.py
```

Output video akan tersimpan seperti ini:

```text
recordings/recording_20260512_091500.avi
```

## Level_3_Deteksi_Gerakan.py

File ini adalah latihan Level 3 untuk deteksi gerakan sederhana seperti CCTV.

Fitur:

- Menampilkan live preview dari kamera.
- Menyimpan foto.
- Merekam video.
- Mengaktifkan atau menonaktifkan deteksi gerakan.
- Memberi kotak hijau pada area yang bergerak.
- Menampilkan teks `MOTION DETECTED` saat ada gerakan.
- Tetap bisa merekam video saat deteksi gerakan aktif.

Tombol:

- `s` untuk menyimpan foto.
- `r` untuk mulai atau berhenti merekam video.
- `m` untuk mengaktifkan atau menonaktifkan deteksi gerakan.
- `q` untuk keluar.

Cara menjalankan:

```bash
python PythonFile/Level_3_Deteksi_Gerakan.py
```

Jika `m` dan `r` aktif bersamaan, hasil video akan ikut menyimpan tampilan kotak deteksi gerakan.

## Simple_Cam.py

File ini adalah versi gabungan dari latihan sebelumnya.

Fitur di dalamnya:

- Capture foto.
- Rekam video.
- Deteksi gerakan.

File ini tetap bisa dipakai, tetapi untuk belajar bertahap lebih mudah menggunakan file Level 1, Level 2, dan Level 3.

## Catatan Penting

Jika kamera eksternal tidak tampil, coba ganti index kamera:

```python
cap = cv2.VideoCapture(0)
```

atau:

```python
cap = cv2.VideoCapture(2)
```

Jika video tidak bisa dibuka di media player tertentu, codec `.avi` mungkin tidak cocok. Nanti bisa dicoba mengganti codec ke format lain seperti `MJPG` atau menyimpan ke `.mp4`.
