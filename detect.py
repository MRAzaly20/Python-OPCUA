import cv2
import mediapipe as mp
from opcua import Client, ua

opc_ua_server_url = "opc.tcp://127.0.0.1:4840"

client = Client(opc_ua_server_url)

try:
    client.connect()
    print("Client connected to OPC UA server")
except Exception as e:
    print(f"Error connecting to OPC UA server: {e}")
    exit()

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

def count_fingers(hand_landmarks):
    finger_tips = [8, 12, 16, 20]  
    finger_pips = [6, 10, 14, 18] 
    
    count = 0
    for tip, pip in zip(finger_tips, finger_pips):
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y:
            count += 1
    
    if hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x:
        count += 1 
    
    return count

node_id = "ns=2;s=MX_OPC.Device1.Dev04.Data_Tag.D0_OPC_DA"

cap = cv2.VideoCapture(0)

with mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5) as hands:
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("Ignoring empty camera frame.")
            continue

        image = cv2.flip(image, 1)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        results = hands.process(image_rgb)
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                
                finger_count = count_fingers(hand_landmarks)
                
                cv2.putText(image, str(finger_count), (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
                
                print(f"Detected fingers: {finger_count}")
                
                try:
                    node = client.get_node(node_id)
                    datavalue = ua.DataValue(ua.Variant(finger_count, ua.VariantType.UInt16))
                    node.set_value(datavalue)
                    print(f"Value of {node_id} updated to: {finger_count}")
                except ua.UaError as e:
                    print(f"Error writing to node {node_id}: {e}")
                except Exception as e:
                    print(f"Unexpected error: {e}")

        cv2.imshow('MediaPipe Hands', image)
        
        if cv2.waitKey(5) & 0xFF == 27:
            break

cap.release()
cv2.destroyAllWindows()

client.disconnect()
print("Client disconnected")