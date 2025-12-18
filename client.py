import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime

class ESP32Client:
    def __init__(self, device_id="ESP32_SIMULATOR"):
        self.device_id = device_id
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.connected = False
    
    def on_connect(self, client, userdata, flags, rc):
        print(f"连接MQTT服务器: {rc}")
        self.connected = True
        client.subscribe("esp32/output")
        
        # 发送设备连接信息
        connect_msg = {
            "device_id": self.device_id,
            "action": "connect",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        client.publish("esp32/input", json.dumps(connect_msg))
        print(f"发送连接信息: {connect_msg}")
    
    def on_message(self, client, userdata, msg):
        ai_reply = msg.payload.decode('utf-8')
        print(f"\nAI: {ai_reply}")
        print("ESP32> ", end="", flush=True)
    
    def send_message(self, message):
        if not self.connected:
            print("未连接到服务器")
            return
        
        msg_data = {
            "device_id": self.device_id,
            "message": message,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.client.publish("esp32/input", json.dumps(msg_data, ensure_ascii=False))
    
    def start(self):
        print("启动ESP32客户端...")
        self.client.connect("localhost", 1883, 60)
        
        # 启动后台线程
        self.client.loop_start()
        
        # 等待连接
        while not self.connected:
            time.sleep(0.1)
        
        # 交互界面
        print("\n输入消息 (输入 'quit' 退出):")
        while True:
            try:
                user_input = input("ESP32> ").strip()
                if user_input.lower() == 'quit':
                    break
                if user_input:
                    self.send_message(user_input)
            except KeyboardInterrupt:
                break
        
        self.client.loop_stop()
        self.client.disconnect()

if __name__ == "__main__":
    client = ESP32Client()
    client.start()
