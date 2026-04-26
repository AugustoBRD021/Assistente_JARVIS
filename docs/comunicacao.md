# Protocolos de Comunicação - JARVIS

## Visão Geral

O sistema JARVIS utiliza múltiplos protocolos de comunicação para garantir interação eficiente e confiável entre os componentes de software e hardware. A arquitetura suporta comunicação serial, Wi-Fi e Bluetooth, com diferentes níveis de abstração para facilitar o desenvolvimento.

## Arquitetura de Comunicação

```
┌─────────────────────────────────────────────────────────────────┐
│                    Camada de Aplicação                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   JARVIS    │  │  Web UI     │  │  Mobile     │             │
│  │   Core      │  │  Interface  │  │   App       │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Camada de Protocolos                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │    HTTP     │  │   WebSockets│  │   MQTT      │             │
│  │   (REST)    │  │             │  │             │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Camada de Transporte                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │     TCP     │  │     UDP     │  │   Serial    │             │
│  │             │  │             │  │   (USB)     │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Camada Física                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Ethernet  │  │     Wi-Fi   │  │     USB     │             │
│  │             │  │             │  │             │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

## Protocolos Suportados

### 1. Comunicação Serial (USB)

#### Especificações
- **Velocidade**: 115200 bps (configurável)
- **Formato**: 8N1 (8 bits, sem paridade, 1 stop bit)
- **Controle de fluxo**: Software (XON/XOFF)
- **Timeout**: 5 segundos
- **Buffer**: 512 bytes

#### Protocolo de Mensagens
```
Formato: JSON + Newline
Estrutura:
{
  "type": "command|response|sensor_data|status|error",
  "id": "unique_message_id",
  "timestamp": 1640995200,
  "source": "python|esp32",
  "destination": "esp32|python",
  "payload": {
    "device": "device_name",
    "action": "action_name",
    "parameters": {},
    "data": {}
  }
}
```

#### Implementação Python
```python
import serial
import json
import time
import threading
from queue import Queue

class SerialCommunicator:
    def __init__(self, port=None, baudrate=115200, timeout=5):
        self.port = port or self.auto_detect_port()
        self.baudrate = baudrate
        self.timeout = timeout
        self.connection = None
        self.message_queue = Queue()
        self.response_handlers = {}
        self.running = False
        
    def connect(self):
        try:
            self.connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            self.running = True
            self.start_listener()
            return True
        except Exception as e:
            print(f"Erro de conexão serial: {e}")
            return False
    
    def send_message(self, message_type, payload, message_id=None):
        if not self.connection:
            return False
            
        message = {
            "type": message_type,
            "id": message_id or self.generate_id(),
            "timestamp": int(time.time()),
            "source": "python",
            "destination": "esp32",
            "payload": payload
        }
        
        try:
            message_str = json.dumps(message) + "\n"
            self.connection.write(message_str.encode())
            return True
        except Exception as e:
            print(f"Erro ao enviar mensagem: {e}")
            return False
    
    def start_listener(self):
        def listener():
            buffer = ""
            while self.running:
                if self.connection.in_waiting > 0:
                    data = self.connection.read(self.connection.in_waiting).decode()
                    buffer += data
                    
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        if line.strip():
                            self.process_message(line.strip())
                
                time.sleep(0.01)
        
        thread = threading.Thread(target=listener, daemon=True)
        thread.start()
    
    def process_message(self, message_str):
        try:
            message = json.loads(message_str)
            self.message_queue.put(message)
            
            # Processar resposta específica
            if message.get("type") == "response":
                message_id = message.get("id")
                if message_id in self.response_handlers:
                    self.response_handlers[message_id](message)
                    del self.response_handlers[message_id]
                    
        except json.JSONDecodeError as e:
            print(f"Erro ao decodificar JSON: {e}")
```

#### Implementação C++ (ESP32)
```cpp
#include <ArduinoJson.h>
#include <HardwareSerial.h>

class SerialCommunicator {
private:
    HardwareSerial* serial;
    char buffer[512];
    int buffer_index;
    unsigned long last_message_time;
    
public:
    SerialCommunicator(HardwareSerial* ser) : serial(ser), buffer_index(0) {}
    
    void begin(long baudrate) {
        serial->begin(baudrate);
        last_message_time = millis();
    }
    
    void send_message(const char* type, const char* device, const char* action, JsonObject parameters = JsonObject()) {
        DynamicJsonDocument doc(512);
        
        doc["type"] = type;
        doc["id"] = generate_id();
        doc["timestamp"] = millis();
        doc["source"] = "esp32";
        doc["destination"] = "python";
        
        JsonObject payload = doc.createNestedObject("payload");
        payload["device"] = device;
        payload["action"] = action;
        
        if (!parameters.isNull()) {
            payload["parameters"] = parameters;
        }
        
        serializeJson(doc, *serial);
        serial->println();
    }
    
    void process_incoming() {
        while (serial->available()) {
            char c = serial->read();
            
            if (c == '\n') {
                buffer[buffer_index] = '\0';
                process_message(buffer);
                buffer_index = 0;
            } else if (buffer_index < 511) {
                buffer[buffer_index++] = c;
            }
        }
    }
    
private:
    String generate_id() {
        return "esp_" + String(millis());
    }
    
    void process_message(const char* message_str) {
        DynamicJsonDocument doc(512);
        DeserializationError error = deserializeJson(doc, message_str);
        
        if (error) {
            Serial.println("JSON parse error");
            return;
        }
        
        String type = doc["type"];
        String device = doc["payload"]["device"];
        String action = doc["payload"]["action"];
        
        // Processar mensagem baseado no tipo
        if (type == "command") {
            handle_command(doc);
        }
    }
};
```

### 2. Comunicação Wi-Fi (TCP/IP)

#### Especificações
- **Protocolo**: TCP/IP
- **Porta**: 8080 (configurável)
- **Timeout**: 30 segundos
- **Máximo de clientes**: 5
- **Segurança**: TLS opcional

#### Servidor TCP (Python)
```python
import socket
import threading
import json
import ssl
from queue import Queue

class WiFiServer:
    def __init__(self, host='0.0.0.0', port=8080, use_ssl=False):
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        self.socket = None
        self.clients = {}
        self.running = False
        self.message_handlers = {}
        
    def start(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            
            if self.use_ssl:
                context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                context.load_cert_chain('server.crt', 'server.key')
                self.socket = context.wrap_socket(self.socket, server_side=True)
            
            self.running = True
            print(f"Servidor iniciado em {self.host}:{self.port}")
            
            # Thread para aceitar conexões
            accept_thread = threading.Thread(target=self.accept_connections)
            accept_thread.daemon = True
            accept_thread.start()
            
            return True
            
        except Exception as e:
            print(f"Erro ao iniciar servidor: {e}")
            return False
    
    def accept_connections(self):
        while self.running:
            try:
                client_socket, address = self.socket.accept()
                client_id = f"{address[0]}:{address[1]}"
                
                self.clients[client_id] = {
                    'socket': client_socket,
                    'address': address,
                    'authenticated': False
                }
                
                print(f"Cliente conectado: {client_id}")
                
                # Thread para handle do cliente
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_id,)
                )
                client_thread.daemon = True
                client_thread.start()
                
            except Exception as e:
                if self.running:
                    print(f"Erro ao aceitar conexão: {e}")
    
    def handle_client(self, client_id):
        client = self.clients[client_id]
        socket = client['socket']
        buffer = ""
        
        while self.running and client_id in self.clients:
            try:
                data = socket.recv(1024).decode()
                if not data:
                    break
                
                buffer += data
                
                # Processar mensagens completas
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        self.process_client_message(client_id, line.strip())
                        
            except Exception as e:
                print(f"Erro no cliente {client_id}: {e}")
                break
        
        # Limpar conexão
        if client_id in self.clients:
            del self.clients[client_id]
            socket.close()
            print(f"Cliente desconectado: {client_id}")
    
    def send_to_client(self, client_id, message):
        if client_id in self.clients:
            try:
                socket = self.clients[client_id]['socket']
                message_str = json.dumps(message) + "\n"
                socket.send(message_str.encode())
                return True
            except Exception as e:
                print(f"Erro ao enviar para {client_id}: {e}")
                return False
        return False
    
    def broadcast(self, message):
        sent_count = 0
        for client_id in list(self.clients.keys()):
            if self.send_to_client(client_id, message):
                sent_count += 1
        return sent_count
```

#### Cliente Wi-Fi (ESP32)
```cpp
#include <WiFi.h>
#include <WiFiClient.h>
#include <ArduinoJson.h>

class WiFiClient {
private:
    WiFiClient client;
    const char* host;
    int port;
    char buffer[512];
    int buffer_index;
    bool connected;
    unsigned long last_reconnect_attempt;
    unsigned long last_heartbeat;
    
public:
    WiFiClient(const char* server_host, int server_port) 
        : host(server_host), port(server_port), buffer_index(0), connected(false) {}
    
    bool connect() {
        if (client.connect(host, port)) {
            connected = true;
            last_heartbeat = millis();
            Serial.println("Conectado ao servidor");
            return true;
        }
        return false;
    }
    
    void disconnect() {
        client.stop();
        connected = false;
    }
    
    bool send_message(const char* type, const char* device, const char* action, JsonObject parameters = JsonObject()) {
        if (!connected && !connect()) {
            return false;
        }
        
        DynamicJsonDocument doc(512);
        
        doc["type"] = type;
        doc["id"] = generate_id();
        doc["timestamp"] = millis();
        doc["source"] = "esp32";
        doc["destination"] = "python";
        
        JsonObject payload = doc.createNestedObject("payload");
        payload["device"] = device;
        payload["action"] = action;
        
        if (!parameters.isNull()) {
            payload["parameters"] = parameters;
        }
        
        String message;
        serializeJson(doc, message);
        message += "\n";
        
        return client.print(message) > 0;
    }
    
    void process_messages() {
        if (!connected) {
            // Tentar reconectar a cada 30 segundos
            if (millis() - last_reconnect_attempt > 30000) {
                connect();
                last_reconnect_attempt = millis();
            }
            return;
        }
        
        // Enviar heartbeat a cada 60 segundos
        if (millis() - last_heartbeat > 60000) {
            send_message("heartbeat", "system", "ping");
            last_heartbeat = millis();
        }
        
        while (client.available()) {
            char c = client.read();
            
            if (c == '\n') {
                buffer[buffer_index] = '\0';
                process_message(buffer);
                buffer_index = 0;
            } else if (buffer_index < 511) {
                buffer[buffer_index++] = c;
            }
        }
    }
    
private:
    String generate_id() {
        return "esp_" + String(millis());
    }
    
    void process_message(const char* message_str) {
        DynamicJsonDocument doc(512);
        DeserializationError error = deserializeJson(doc, message_str);
        
        if (error) {
            Serial.println("JSON parse error");
            return;
        }
        
        String type = doc["type"];
        
        if (type == "command") {
            handle_command(doc);
        } else if (type == "heartbeat_response") {
            Serial.println("Heartbeat recebido");
        }
    }
};
```

### 3. Comunicação MQTT

#### Especificações
- **Broker**: Mosquitto ou EMQX
- **Porta**: 1883 (insegura) / 8883 (TLS)
- **QoS**: 0 (at most once), 1 (at least once), 2 (exactly once)
- **Topics**: Hierárquicos

#### Estrutura de Topics
```
jarvis/
├── devices/
│   ├── {device_id}/
│   │   ├── command/
│   │   ├── status/
│   │   └── data/
├── system/
│   ├── heartbeat/
│   ├── logs/
│   └── alerts/
└── config/
    ├── devices/
    └── system/
```

#### Implementação MQTT (Python)
```python
import paho.mqtt.client as mqtt
import json
import time
import threading

class MQTTCommunicator:
    def __init__(self, broker_host, broker_port=1883, username=None, password=None):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.username = username
        self.password = password
        
        self.client = mqtt.Client()
        self.message_handlers = {}
        self.connected = False
        
        # Configurar callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
        if username and password:
            self.client.username_pw_set(username, password)
    
    def connect(self):
        try:
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            return True
        except Exception as e:
            print(f"Erro ao conectar MQTT: {e}")
            return False
    
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            print("Conectado ao broker MQTT")
            
            # Subscrever aos topics principais
            self.subscribe("jarvis/devices/+/command")
            self.subscribe("jarvis/system/+/response")
            
        else:
            print(f"Falha na conexão MQTT: {rc}")
    
    def on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            # Extrair device_id do topic
            topic_parts = topic.split('/')
            if len(topic_parts) >= 4:
                device_type = topic_parts[1]  # devices, system
                device_id = topic_parts[2]    # device_id
                message_type = topic_parts[3]  # command, status, data
                
                self.process_message(device_id, message_type, payload)
                
        except Exception as e:
            print(f"Erro ao processar mensagem MQTT: {e}")
    
    def publish(self, topic, payload, qos=1):
        if self.connected:
            message = json.dumps(payload)
            result = self.client.publish(topic, message, qos)
            return result.rc == mqtt.MQTT_ERR_SUCCESS
        return False
    
    def subscribe(self, topic, qos=1):
        if self.connected:
            result = self.client.subscribe(topic, qos)
            return result[0] == mqtt.MQTT_ERR_SUCCESS
        return False
    
    def send_device_command(self, device_id, command, parameters=None):
        topic = f"jarvis/devices/{device_id}/command"
        payload = {
            "command": command,
            "parameters": parameters or {},
            "timestamp": int(time.time())
        }
        return self.publish(topic, payload)
    
    def send_device_status(self, device_id, status, data=None):
        topic = f"jarvis/devices/{device_id}/status"
        payload = {
            "status": status,
            "data": data or {},
            "timestamp": int(time.time())
        }
        return self.publish(topic, payload)
```

## Protocolo de Mensagens Unificado

### Estrutura Base
```json
{
  "version": "1.0",
  "type": "command|response|event|error|heartbeat",
  "id": "uuid_v4",
  "timestamp": 1640995200,
  "source": {
    "type": "python|esp32|web|mobile",
    "id": "source_identifier",
    "version": "1.0.0"
  },
  "destination": {
    "type": "python|esp32|web|mobile|broadcast",
    "id": "destination_identifier"
  },
  "correlation_id": "original_message_id",
  "payload": {
    "device": "device_name",
    "action": "action_name",
    "parameters": {},
    "data": {},
    "metadata": {}
  },
  "priority": "low|normal|high|critical",
  "ttl": 30,
  "retry_count": 0,
  "max_retries": 3
}
```

### Tipos de Mensagens

#### 1. Comando (Command)
```json
{
  "type": "command",
  "payload": {
    "device": "relay_1",
    "action": "set_state",
    "parameters": {
      "state": "on",
      "duration": 5000
    },
    "metadata": {
      "user_id": "user_123",
      "source": "voice_command"
    }
  }
}
```

#### 2. Resposta (Response)
```json
{
  "type": "response",
  "correlation_id": "cmd_001",
  "payload": {
    "device": "relay_1",
    "action": "set_state",
    "data": {
      "success": true,
      "previous_state": "off",
      "current_state": "on",
      "execution_time": 125
    }
  }
}
```

#### 3. Evento (Event)
```json
{
  "type": "event",
  "payload": {
    "device": "motion_sensor_1",
    "action": "motion_detected",
    "data": {
      "timestamp": 1640995200,
      "sensitivity": 0.8,
      "location": "living_room"
    }
  }
}
```

#### 4. Erro (Error)
```json
{
  "type": "error",
  "correlation_id": "cmd_002",
  "payload": {
    "error_code": "DEVICE_NOT_FOUND",
    "error_message": "Dispositivo relay_5 não encontrado",
    "details": {
      "available_devices": ["relay_1", "relay_2", "relay_3", "relay_4"]
    }
  }
}
```

#### 5. Heartbeat
```json
{
  "type": "heartbeat",
  "payload": {
    "device": "esp32_001",
    "data": {
      "uptime": 3600,
      "free_memory": 234567,
      "cpu_usage": 15.2,
      "temperature": 42.5,
      "wifi_signal": -65
    }
  }
}
```

## Segurança na Comunicação

### 1. Criptografia

#### TLS/SSL para TCP
```python
import ssl

def create_ssl_context():
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain('server.crt', 'server.key')
    context.load_verify_locations('ca.crt')
    context.verify_mode = ssl.CERT_REQUIRED
    return context
```

#### Criptografia AES para Serial
```python
from Crypto.Cipher import AES
import base64

class AESEncryption:
    def __init__(self, key):
        self.key = key.encode('utf-8')
        self.cipher = AES.new(self.key, AES.MODE_ECB)
    
    def encrypt(self, message):
        message_bytes = message.encode('utf-8')
        padded = self._pad(message_bytes)
        encrypted = self.cipher.encrypt(padded)
        return base64.b64encode(encrypted).decode('utf-8')
    
    def decrypt(self, encrypted_message):
        encrypted_bytes = base64.b64decode(encrypted_message)
        decrypted = self.cipher.decrypt(encrypted_bytes)
        return self._unpad(decrypted).decode('utf-8')
    
    def _pad(self, data):
        pad_length = 16 - (len(data) % 16)
        return data + bytes([pad_length] * pad_length)
    
    def _unpad(self, data):
        pad_length = data[-1]
        return data[:-pad_length]
```

### 2. Autenticação

#### Token JWT
```python
import jwt
import time

class AuthManager:
    def __init__(self, secret_key):
        self.secret_key = secret_key
        self.tokens = {}
    
    def generate_token(self, client_id, expires_in=3600):
        payload = {
            'client_id': client_id,
            'exp': int(time.time()) + expires_in,
            'iat': int(time.time())
        }
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        self.tokens[token] = client_id
        return token
    
    def validate_token(self, token):
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            client_id = payload['client_id']
            
            if token in self.tokens and self.tokens[token] == client_id:
                return True, client_id
            return False, None
            
        except jwt.ExpiredSignatureError:
            return False, None
        except jwt.InvalidTokenError:
            return False, None
```

### 3. Rate Limiting

```python
import time
from collections import defaultdict

class RateLimiter:
    def __init__(self, max_requests=100, time_window=60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = defaultdict(list)
    
    def is_allowed(self, client_id):
        now = time.time()
        client_requests = self.requests[client_id]
        
        # Remover requests antigos
        client_requests[:] = [req_time for req_time in client_requests 
                             if now - req_time < self.time_window]
        
        if len(client_requests) < self.max_requests:
            client_requests.append(now)
            return True
        
        return False
```

## Monitoramento e Debug

### 1. Logging de Comunicação

```python
import logging
from functools import wraps

def log_communication(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger('communication')
        
        # Log antes da execução
        logger.info(f"Enviando mensagem via {func.__name__}: {args}")
        
        try:
            result = func(*args, **kwargs)
            logger.info(f"Mensagem enviada com sucesso: {result}")
            return result
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem: {e}")
            raise
    
    return wrapper
```

### 2. Métricas de Performance

```python
import time
from collections import deque

class CommunicationMetrics:
    def __init__(self, max_samples=1000):
        self.max_samples = max_samples
        self.latencies = deque(maxlen=max_samples)
        self.message_counts = defaultdict(int)
        self.error_counts = defaultdict(int)
    
    def record_latency(self, latency_ms):
        self.latencies.append(latency_ms)
    
    def record_message(self, message_type):
        self.message_counts[message_type] += 1
    
    def record_error(self, error_type):
        self.error_counts[error_type] += 1
    
    def get_stats(self):
        if not self.latencies:
            return {}
        
        return {
            'avg_latency': sum(self.latencies) / len(self.latencies),
            'min_latency': min(self.latencies),
            'max_latency': max(self.latencies),
            'total_messages': sum(self.message_counts.values()),
            'total_errors': sum(self.error_counts.values()),
            'message_types': dict(self.message_counts),
            'error_types': dict(self.error_counts)
        }
```

## Testes de Comunicação

### 1. Teste de Conectividade

```python
def test_connectivity(communicator, timeout=10):
    start_time = time.time()
    
    # Enviar heartbeat
    if communicator.send_message("heartbeat", {"ping": True}):
        # Aguardar resposta
        while time.time() - start_time < timeout:
            if not communicator.message_queue.empty():
                response = communicator.message_queue.get()
                if response.get("type") == "heartbeat_response":
                    return True
            time.sleep(0.1)
    
    return False
```

### 2. Teste de Latência

```python
def test_latency(communicator, num_tests=10):
    latencies = []
    
    for i in range(num_tests):
        start_time = time.time()
        
        # Enviar timestamp
        communicator.send_message("ping", {"timestamp": start_time})
        
        # Aguardar resposta
        while True:
            if not communicator.message_queue.empty():
                response = communicator.message_queue.get()
                if response.get("type") == "pong":
                    end_time = time.time()
                    latency = (end_time - start_time) * 1000  # ms
                    latencies.append(latency)
                    break
            time.sleep(0.01)
    
    return {
        'avg_latency': sum(latencies) / len(latencies),
        'min_latency': min(latencies),
        'max_latency': max(latencies)
    }
```

Este guia completo de protocolos de comunicação fornece uma base sólida para implementar comunicação confiável e segura entre todos os componentes do sistema JARVIS.
