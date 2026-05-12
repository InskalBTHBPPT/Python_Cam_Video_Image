import cv2

cap = cv2.VideoCapture(1) # 0 untuk kamera internal, 1 untuk kamera eksternal

if not cap.isOpened():
    print("Kamera tidak terdeteksi")
    exit()

while True:
    ret, frame = cap.read()

    if not ret:
        print("Gagal membaca frame")
        break

    cv2.imshow("USB Camera", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()