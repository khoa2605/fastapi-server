from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import paho.mqtt.client as mqtt
import threading

app = FastAPI()

# Cho phép gọi API từ web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép mọi domain gọi API
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dữ liệu sẽ được cập nhật mỗi khi ESP32 gửi lên
data = {
    "temperature": 0.0,
    "humidity": 0.0
}

@app.get("/api/data")
def get_data():
    return data

# Hàm callback khi nhận MQTT
def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    try:
        # Giả sử ESP32 gửi JSON kiểu {"temperature": 29.4, "humidity": 60}
        import json
        new_data = json.loads(payload)
        data["temperature"] = new_data.get("temperature", data["temperature"])
        data["humidity"] = new_data.get("humidity", data["humidity"])
    except Exception as e:
        print("Lỗi khi xử lý MQTT:", e)

def mqtt_thread():
    client = mqtt.Client()
    client.on_message = on_message
    client.connect("broker.hivemq.com", 8883, 60)
    client.subscribe("ESP32/data")
    client.loop_forever()

# Chạy MQTT ở luồng riêng
threading.Thread(target=mqtt_thread, daemon=True).start()
