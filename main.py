from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Cho phép trang web khác gọi API (ví dụ: cafe.fuvitech.vn)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dữ liệu mẫu (sau này bạn sẽ cập nhật từ MQTT)
data = {
    "temperature": 28.5,
    "humidity": 60
}

@app.get("/api/data")
def get_data():
    return data
