from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import paho.mqtt.client as mqtt
import threading
import json
import time
import os

app = FastAPI()

# Cho phép gọi API từ web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép mọi domain gọi API
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dữ liệu sẽ được cập nhật mỗi khi ESP32 gửi lên và lưu lịch sử
data = {
    "temperature": 0.0,
    "humidity": 0.0,
    "timestamp": time.time(),
}
history_data = []  # Danh sách lưu lịch sử để vẽ biểu đồ

@app.get("/api/data")
def get_data():
    return data


@app.get("/")
def read_root():
    return {"message": "FastAPI server is running!"}
mqtt_status = {
    "connected": False,
    "last_attempt": None
}
@app.get("/api/status")
def get_status():
    return {
        "connected": mqtt_status["connected"],
        "last_attempt": mqtt_status["last_attempt"]
    }



@app.get("/api/history")
def get_history():
    return history_data[-50:]  # Trả về ... mẫu gần nhất (hoặc điều chỉnh tùy bạn)

# MQTT callback
def on_connect(client, userdata, flags, rc):
    mqtt_status["connected"] = True
    mqtt_status["last_attempt"] = time.time()
    
    if rc == 0:
        print("[MQTT] Successfully connecting to broker.")
        client.subscribe("ESP32/data")
    else:
        print(f"[MQTT] Connect fail, Error: {rc}")

def on_disconnect(client, userdata, rc):
    print("[MQTT] Lost connected. Reconnecting...")
    mqtt_status["connected"] = False
    mqtt_status["last_attempt"] = time.time()


# Hàm callback khi nhận MQTT
def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    print(f"[MQTT] Received topic: {msg.topic} at {time.strftime('%H:%M:%S')} – payload: {payload}")
    try:
        new_data = json.loads(payload)
        data["temperature"] = new_data.get("temperature", data["temperature"])
        data["humidity"] = new_data.get("humidity", data["humidity"])
        data["timestamp"] = time.time()  # Cập nhật thời gian

        # Lưu lịch sử
        history_data.append({
            "temperature": data["temperature"],
            "humidity": data["humidity"],
            "timestamp": data["timestamp"],
        })

        # Giới hạn số lượng lịch sử nếu cần
        if len(history_data) > 200:
            history_data.pop(0)

    except json.JSONDecodeError:
        print("JSON decode Error:", payload)
    except Exception as e:
        print("MQTT processing Error:", e)

def mqtt_thread():
    client = mqtt.Client()
    client.username_pw_set("khoa2605", "Khoa2605")  #thông tin HiveMQ Cloud
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    client.tls_set()  # Kích hoạt TLS/SSL mặc định
    client.connect("5ea4ea4499054653a5069edcfb38de4c.s1.eu.hivemq.cloud", 8883, 60)

    while True:
        try:
            client.loop_forever()
        except Exception as e:
            print("Error MQTT loop, try again after 5s:", e)
            time.sleep(5)

# Chạy MQTT ở luồng riêng
threading.Thread(target=mqtt_thread, daemon=True).start()

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    print(f"🌐 App running on port: {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port)
