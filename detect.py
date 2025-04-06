import cv2
import mediapipe as mp
from opcua import Client, ua

# Alamat server OPC UA
opc_ua_server_url = "opc.tcp://0.tcp.ap.ngrok.io:14082"

# Inisialisasi client OPC UA
client = Client(opc_ua_server_url)

try:
    # Menghubungkan client ke server OPC UA
    client.connect()
    print("Client connected to OPC UA server")
except Exception as e:
    print(f"Error connecting to OPC UA server: {e}")
    exit()

# Inisialisasi MediaPipe dan OpenCV
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Fungsi untuk menghitung jumlah jari yang terangkat
def count_fingers(hand_landmarks):
    # Daftar titik referensi untuk setiap jari
    finger_tips = [8, 12, 16, 20]  # Ujung jari (telunjuk, tengah, manis, kelingking)
    finger_pips = [6, 10, 14, 18]  # Pangkal jari
    
    # Hitung jumlah jari yang terangkat
    count = 0
    for tip, pip in zip(finger_tips, finger_pips):
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y:
            count += 1
    
    # Cek ibu jari (di luar loop agar lebih cepat)
    if hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x:
        count += 1  # Tambahkan jika ibu jari terangkat
    
    return count

# Node ID untuk menulis hasil deteksi
node_id = "ns=2;s=MX_OPC.Device1.Dev04.Data_Tag.D0_OPC_DA"

# Mengakses kamera
cap = cv2.VideoCapture(0)

with mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5) as hands:
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("Ignoring empty camera frame.")
            continue

        # Flip gambar untuk tampilan seperti cermin dan konversi ke RGB
        image = cv2.flip(image, 1)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Proses gambar untuk deteksi tangan
        results = hands.process(image_rgb)
        
        # Gambar anotasi tangan di gambar
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                
                # Hitung jumlah jari yang terangkat
                finger_count = count_fingers(hand_landmarks)
                
                # Tampilkan jumlah jari yang terangkat
                cv2.putText(image, str(finger_count), (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
                
                # Cetak jumlah jari yang terangkat ke console
                print(f"Detected fingers: {finger_count}")
                
                # Menulis hasil deteksi ke Node OPC UA
                try:
                    node = client.get_node(node_id)
                    # Menulis nilai Word (UInt16) ke Node
                    datavalue = ua.DataValue(ua.Variant(finger_count, ua.VariantType.UInt16))
                    node.set_value(datavalue)
                    print(f"Value of {node_id} updated to: {finger_count}")
                except ua.UaError as e:
                    print(f"Error writing to node {node_id}: {e}")
                except Exception as e:
                    print(f"Unexpected error: {e}")

        # Tampilkan gambar
        cv2.imshow('MediaPipe Hands', image)
        
        # Keluar dari loop jika tombol ESC ditekan
        if cv2.waitKey(5) & 0xFF == 27:
            break

# Membersihkan sumber daya
cap.release()
cv2.destroyAllWindows()

# Memutuskan koneksi OPC UA client
client.disconnect()
print("Client disconnected")