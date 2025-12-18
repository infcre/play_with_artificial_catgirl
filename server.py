import paho.mqtt.client as mqtt
from openai import OpenAI
import json
from datetime import datetime

class AIServer:
    def __init__(self):
        # OpenAI配置
        self.ai_client = OpenAI(
            api_key="sk-xxxxxxxxxxx",
            base_url="https://api.deepseek.com"
        )
        
        # 对话记忆
        self.conversation_memory = []
        self.max_memory = 12  # 保留6轮对话
        
        # MQTT客户端
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        
        # 日志文件
        self.log_file = "server.log"
        
        # 系统提示
        self.system_prompt = "你是一个猫娘，说话简洁可爱，喜欢用表情符号。"
    
    def log_raw_data(self, data):
        """记录原始数据到日志文件"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {data}\n")
    
    def on_connect(self, client, userdata, flags, rc):
        print(f"MQTT连接成功: {rc}")
        client.subscribe("esp32/input")
    
    def on_message(self, client, userdata, msg):
        try:
            # 接收原始数据
            raw_data = msg.payload.decode('utf-8')
            self.log_raw_data(f"收到: {raw_data}")
            
            # 解析消息
            try:
                data = json.loads(raw_data)
                if data.get("action") == "connect":
                    # 设备连接信息
                    self.log_raw_data(f"设备连接: {data['device_id']}")
                    self.conversation_memory.clear()  # 新连接，清空记忆
                    return
                
                user_message = data.get("message", "")
            except:
                user_message = raw_data
            
            if not user_message:
                return
            
            # 添加到对话记忆
            self.conversation_memory.append({"role": "user", "content": user_message})
            
            # 限制记忆长度
            if len(self.conversation_memory) > self.max_memory:
                self.conversation_memory = self.conversation_memory[-self.max_memory:]
            
            # 构建AI消息
            messages = [{"role": "system", "content": self.system_prompt}]
            messages.extend(self.conversation_memory)
            
            # 调用AI
            response = self.ai_client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                max_tokens=150,
                temperature=0.7
            )
            
            ai_reply = response.choices[0].message.content
            self.log_raw_data(f"AI回复: {ai_reply}")
            
            # 添加到记忆
            self.conversation_memory.append({"role": "assistant", "content": ai_reply})
            
            # 发送回复
            client.publish("esp32/output", ai_reply)
            
        except Exception as e:
            error_msg = f"错误: {str(e)}"
            self.log_raw_data(error_msg)
            client.publish("esp32/output", error_msg)
    
    def start(self):
        print("启动AI服务器...")
        self.mqtt_client.connect("localhost", 1883, 60)
        self.mqtt_client.loop_forever()

if __name__ == "__main__":
    server = AIServer()
    server.start()
