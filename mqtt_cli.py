import network
import time
from umqtt.simple import MQTTClient
import ujson
from machine import RTC
import ntptime

class ESP32Client:
    def __init__(self, device_id="ESP32_DEVICE"):
        # WiFi配置
        self.wifi_ssid = "swu-wifi(2.4G)"
        self.wifi_password = ""  # 请填写你的WiFi密码
        
        # MQTT服务器配置
        self.server_ip = "10.65.132.129"
        self.mqtt_port = 1883
        self.device_id = device_id
        
        # 主题配置
        self.input_topic = b"esp32/input"
        self.output_topic = b"esp32/output"
        
        self.client = None
        self.connected = False
        self.rtc = RTC()
        
        # 设置NTP服务器为您的服务器IP
        ntptime.host = "10.65.132.129"
        
    def connect_wifi(self):
        """连接WiFi"""
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        
        if not wlan.isconnected():
            print("Connecting to WiFi: ", self.wifi_ssid)
            wlan.connect(self.wifi_ssid, self.wifi_password)
            
            # 等待连接
            for i in range(20):
                if wlan.isconnected():
                    break
                time.sleep(1)
            
        if wlan.isconnected():
            print("WiFi connected! IP: ", wlan.ifconfig()[0])
            return True
        else:
            print("WiFi connection failed!")
            return False
    
    def sync_time(self, retries=3):
        """同步NTP时间"""
        for i in range(retries):
            try:
                print(f"Attempting NTP sync (attempt {i+1}/{retries})...")
                ntptime.settime()
                # 获取当前UTC时间并调整为东八区（+8小时）
                t = time.localtime()
                # 转换为秒数，加上8小时（28800秒）
                t_seconds = time.mktime(t) + 28800
                # 将调整后的秒数转换为时间元组
                t_adjusted = time.localtime(t_seconds)
                self.rtc.datetime((t_adjusted[0], t_adjusted[1], t_adjusted[2], 
                              t_adjusted[6], t_adjusted[3], t_adjusted[4], 
                              t_adjusted[5], 0))
                print("Time synchronized successfully!")
                return True
            except Exception as e:
                print(f"NTP sync failed: {e}")
                if i < retries - 1:
                    print("Retrying in 2 seconds...")
                    time.sleep(2)
        
        print("All NTP sync attempts failed, using local RTC")
        # 如果NTP同步失败，设置一个合理的时间（当前年份）
        t = time.localtime()
        self.rtc.datetime((t[0], t[1], t[2], t[6], t[3], t[4], t[5], 0))
        return False
    
    def get_formatted_time(self):
        """获取格式化的时间字符串"""
        # 获取RTC时间
        t = self.rtc.datetime()
        # 格式化为: YYYY-MM-DD HH:MM:SS
        return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(t[0], t[1], t[2], t[4], t[5], t[6])
    
    def mqtt_callback(self, topic, msg):
        """MQTT消息回调函数 - 服务器发送的是纯文本，不是JSON"""
        try:
            # 直接解码消息为文本
            message = msg.decode('utf-8')
            print("\nAI: ", message)
            print("ESP32> ", end="")
        except Exception as e:
            print("Message processing error: ", e)
            print("ESP32> ", end="")
    
    def connect_mqtt(self):
        """连接MQTT服务器"""
        try:
            self.client = MQTTClient(self.device_id, self.server_ip, self.mqtt_port)
            self.client.set_callback(self.mqtt_callback)
            self.client.connect()
            self.client.subscribe(self.output_topic)
            self.connected = True
            print("MQTT connected successfully!")
            
            # 发送设备连接信息
            self.send_connect_message()
            return True
            
        except Exception as e:
            print("MQTT connection failed: ", e)
            return False
    
    def send_connect_message(self):
        """发送设备连接消息"""
        connect_msg = {
            "device_id": self.device_id,
            "action": "connect",
            "timestamp": self.get_formatted_time()
        }
        try:
            self.client.publish(self.input_topic, ujson.dumps(connect_msg))
            print("Device connection message sent")
        except Exception as e:
            print("Failed to send connection message: ", e)
    
    def send_message(self, message):
        """发送消息到MQTT服务器"""
        if not self.connected or not self.client:
            print("Not connected to MQTT server")
            return False
        
        try:
            # 更新RTC时间为当前实际时间
            t = time.localtime()
            self.rtc.datetime((t[0], t[1], t[2], t[6], t[3], t[4], t[5], 0))
            
            msg_data = {
                "device_id": self.device_id,
                "message": message,
                "timestamp": self.get_formatted_time()
            }
            
            json_msg = ujson.dumps(msg_data)
            self.client.publish(self.input_topic, json_msg)
            print("Message sent: ", message)
            return True
        except Exception as e:
            print("Failed to send message: ", e)
            return False
    
    def wait_for_response(self, timeout=10):
        """等待AI回复"""
        if not self.connected or not self.client:
            return False
        
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            try:
                # 检查是否有新消息（非阻塞）
                self.client.check_msg()
                # 短暂延迟
                time.sleep(0.1)
            except Exception as e:
                print("Error checking messages: ", e)
                break
        
        return True
    
    def start(self):
        """启动客户端"""
        print("Starting ESP32 client...")
        
        # 连接WiFi
        if not self.connect_wifi():
            return
        
        # 同步时间
        self.sync_time()
        print("Current time: ", self.get_formatted_time())
        
        # 连接MQTT
        if not self.connect_mqtt():
            return
        
        print("\nEnter message (type 'quit' to exit):")
        print("ESP32> ", end="")
        
        while True:
            try:
                # 等待用户输入
                user_input = input().strip()
                
                if user_input.lower() == 'quit':
                    break
                    
                if user_input:
                    # 发送用户消息
                    if self.send_message(user_input):
                        # 等待AI回复
                        print("Waiting for AI reply...")
                        self.wait_for_response()
                    print("ESP32> ", end="")
                            
            except KeyboardInterrupt:
                print("\nProgram interrupted by user")
                break
            except Exception as e:
                print("Error: ", e)
                time.sleep(1)
                print("ESP32> ", end="")
        
        # 清理资源
        if self.client:
            self.client.disconnect()
        print("Client closed")

# 使用示例
if __name__ == "__main__":
    client = ESP32Client("ESP32_001")
    client.start()