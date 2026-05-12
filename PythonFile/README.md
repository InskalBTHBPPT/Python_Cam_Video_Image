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

## Level_4_Deteksi_Warna.py

File ini adalah latihan Level 4 untuk mendeteksi benda berdasarkan warna.

Warna yang dideteksi:

- Merah.
- Hijau.
- Biru.

Fitur:

- Menampilkan live preview dari kamera.
- Mendeteksi warna menggunakan format HSV.
- Memberi kotak pada benda berwarna yang terdeteksi.
- Memilih warna tertentu atau mendeteksi semua warna sekaligus.
- Menyimpan hasil tampilan sebagai foto.

Tombol:

- `1` untuk deteksi warna merah.
- `2` untuk deteksi warna hijau.
- `3` untuk deteksi warna biru.
- `a` untuk deteksi semua warna.
- `s` untuk menyimpan foto.
- `q` untuk keluar.

Cara menjalankan:

```bash
python PythonFile/Level_4_Deteksi_Warna.py
```

Output foto akan tersimpan seperti ini:

```text
captures/color_detection_20260512_092900.jpg
```

Catatan: hasil deteksi warna sangat dipengaruhi pencahayaan kamera. Jika warna tidak terdeteksi dengan baik, nilai HSV di `COLOR_RANGES` bisa disesuaikan.

## Level_6_Deteksi_Tangan_Jari.py

File ini adalah latihan Level 6 untuk mendeteksi tangan dan menghitung jumlah jari yang terangkat.

Level ini memakai library tambahan bernama MediaPipe. Jika belum terinstall, jalankan:

```bash
pip install mediapipe
```

Pada MediaPipe versi baru, script memakai API `mediapipe.tasks`. Saat pertama kali dijalankan, script akan mengunduh model `hand_landmarker.task` ke folder `models`.

Fitur:

- Menampilkan live preview dari kamera.
- Mendeteksi maksimal 2 tangan.
- Menggambar titik dan garis landmark tangan.
- Menghitung jumlah jari yang terangkat pada setiap tangan.
- Menampilkan total tangan dan total jari di layar.
- Menyimpan hasil tampilan sebagai foto.

Tombol:

- `s` untuk menyimpan foto.
- `q` untuk keluar.

Cara menjalankan:

```bash
python PythonFile/Level_6_Deteksi_Tangan_Jari.py
```

Output foto akan tersimpan seperti ini:

```text
captures/hand_detection_20260512_093200.jpg
```

Catatan: hasil hitung jari paling baik jika telapak tangan menghadap kamera dan jari tidak saling menutup.

## Level_7_Deteksi_Objek_YOLO.py

File ini adalah latihan Level 7 untuk mendeteksi objek umum dengan YOLO.

Level ini memakai library tambahan bernama Ultralytics. Jika belum terinstall, jalankan:

```bash
pip install ultralytics
```

Script ini memakai model pretrained `yolo11n.pt`. Model tersebut sudah dilatih untuk mengenali objek umum, misalnya orang, botol, kursi, laptop, kendaraan, dan objek lain dari dataset COCO. Saat pertama kali dijalankan, model akan diunduh otomatis.

Fitur:

- Menampilkan live preview dari kamera.
- Mendeteksi banyak objek umum dengan YOLO.
- Memberi kotak, nama objek, dan confidence pada objek yang terdeteksi.
- Menampilkan jumlah objek yang terdeteksi.
- Menyimpan hasil tampilan sebagai foto.

Tombol:

- `s` untuk menyimpan foto.
- `q` untuk keluar.

Cara menjalankan:

```bash
python PythonFile/Level_7_Deteksi_Objek_YOLO.py
```

Output foto akan tersimpan seperti ini:

```text
captures/object_detection_20260512_095100.jpg
```

Catatan: Level 7 belum training model sendiri. Level ini memakai model yang sudah dilatih sebelumnya. Training model sendiri akan masuk ke Level 8.

## Simple_Cam.py

File ini adalah versi gabungan dari latihan sebelumnya.

Fitur di dalamnya:

- Capture foto.
- Rekam video.
- Deteksi gerakan.

File ini tetap bisa dipakai, tetapi untuk belajar bertahap lebih mudah menggunakan file Level 1, Level 2, Level 3, Level 4, Level 6, dan Level 7.

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
