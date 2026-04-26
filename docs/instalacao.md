# Guia de Instalação e Configuração - JARVIS

## Pré-requisitos

### Sistema Operacional
- **Windows 10/11** (Recomendado)
- **macOS 10.15+**
- **Linux Ubuntu 18.04+**

### Hardware Mínimo
- **Processador**: Dual-core 2.0GHz
- **Memória RAM**: 4GB (8GB recomendado)
- **Armazenamento**: 2GB livres
- **Microfone**: Integrado ou USB
- **Porta USB**: Para conexão com microcontrolador

### Hardware Opcional
- **ESP32 Development Board** (Recomendado)
- **Arduino Uno/Nano** (Alternativa)
- **Sensores e atuadores** conforme aplicação

## Instalação do Software

### 1. Instalação do Python

#### Windows
1. Baixe o Python 3.9+ de [python.org](https://python.org)
2. Execute o instalador
3. **Importante**: Marque "Add Python to PATH"
4. Verifique instalação:
```cmd
python --version
pip --version
```

#### macOS
```bash
# Usando Homebrew
brew install python3

# Verificar instalação
python3 --version
pip3 --version
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv

# Verificar instalação
python3 --version
pip3 --version
```

### 2. Criação do Ambiente Virtual

```bash
# Criar diretório do projeto
mkdir jarvis-assistant
cd jarvis-assistant

# Criar ambiente virtual
python -m venv jarvis-env

# Ativar ambiente virtual
# Windows
jarvis-env\Scripts\activate

# macOS/Linux
source jarvis-env/bin/activate
```

### 3. Clonagem do Projeto

```bash
# Clonar repositório (se disponível)
git clone https://github.com/usuario/jarvis-assistant.git .

# Ou criar estrutura manualmente
mkdir src config docs tests
```

### 4. Instalação de Dependências

#### requirements.txt
```txt
# Reconhecimento de voz
speechrecognition==3.10.0
pyaudio==0.2.11
pydub==0.25.1

# Síntese de voz
gtts==2.3.2
pyttsx3==2.90

# Inteligência Artificial
openai==1.3.0
langchain==0.0.340
transformers==4.35.0

# Comunicação
pyserial==3.5
requests==2.31.0
websockets==11.0.3

# Automação
pyautogui==0.9.54
psutil==5.9.6
schedule==1.2.0

# Utilitários
numpy==1.24.3
scipy==1.11.4
matplotlib==3.7.2
pandas==2.1.3

# Configuração
python-dotenv==1.0.0
pyyaml==6.0.1

# Logging
colorlog==6.7.0
```

#### Instalação
```bash
pip install -r requirements.txt
```

### 5. Configuração das Chaves de API

#### Criação do arquivo .env
```bash
# Criar arquivo de ambiente
touch .env
```

#### .env
```env
# OpenAI API Key
OPENAI_API_KEY=sk-your-openai-api-key-here

# Configurações de voz
VOICE_LANGUAGE=pt-BR
VOICE_ENGINE=google
WAKE_WORD=jarvis

# Configurações de hardware
SERIAL_PORT=auto
BAUDRATE=115200
WIFI_PORT=8080

# Configurações de sistema
LOG_LEVEL=INFO
MAX_CONCURRENT_TASKS=5
```

### 6. Configuração do Microfone

#### Teste de Microfone (Python)
```python
# test_microphone.py
import speech_recognition as sr

def test_microphone():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    with microphone as source:
        print("Ajustando ao ruído ambiente...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Fale algo...")
        audio = recognizer.listen(source)
    
    try:
        text = recognizer.recognize_google(audio, language="pt-BR")
        print(f"Você disse: {text}")
    except sr.UnknownValueError:
        print("Não foi possível entender o áudio")
    except sr.RequestError as e:
        print(f"Erro no serviço: {e}")

if __name__ == "__main__":
    test_microphone()
```

## Configuração do Hardware

### 1. Instalação do ESP32

#### Preparação do Ambiente

##### PlatformIO (Recomendado)
1. Instale [Visual Studio Code](https://code.visualstudio.com/)
2. Instale a extensão PlatformIO IDE
3. Crie novo projeto PlatformIO
4. Selecione placa "ESP32 Dev Module"

##### Arduino IDE (Alternativa)
1. Baixe [Arduino IDE 2.0+](https://www.arduino.cc/en/software)
2. Abra Arduino IDE
3. Vá em File → Preferences
4. Adicione URL em Additional Boards Manager:
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
5. Vá em Tools → Board → Boards Manager
6. Procure por "ESP32" e instale
7. Selecione placa: Tools → Board → ESP32 Arduino → ESP32 Dev Module

#### Configuração da Placa
```
Board: ESP32 Dev Module
Upload Speed: 921600
CPU Frequency: 240MHz (WiFi/BT)
Flash Frequency: 80MHz
Flash Mode: QIO
Flash Size: 4MB (32Mb)
Partition Scheme: Default 4MB with spiffs (1.2MB APP/1.5MB SPIFFS)
Core Debug Level: None
PSRAM: Enabled
```

### 2. Conexão Física

#### USB Serial
```
ESP32 → Computador
3V3 → (não conectar)
GND → GND
TX  → RX (USB-TTL)
RX  → TX (USB-TTL)
```

#### Alimentação
```
ESP32 → Fonte 5V
VIN  → 5V
GND  → GND
```

### 3. Upload do Firmware

#### Usando PlatformIO
```bash
# No diretório do firmware
pio run --target upload
pio device monitor
```

#### Usando Arduino IDE
1. Abra o arquivo .ino do firmware
2. Selecione a porta COM correta
3. Clique em Upload (seta)
4. Abra Serial Monitor para debug

## Configuração de Rede

### 1. Configuração Wi-Fi do ESP32

#### Código de Conexão
```cpp
#include <WiFi.h>

const char* ssid = "SUA_REDE_WIFI";
const char* password = "SUA_SENHA";

void setup_wifi() {
    delay(10);
    Serial.println();
    Serial.print("Conectando a ");
    Serial.println(ssid);
    
    WiFi.begin(ssid, password);
    
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    
    Serial.println("");
    Serial.println("WiFi conectado");
    Serial.println("Endereço IP: ");
    Serial.println(WiFi.localIP());
}
```

### 2. Configuração de Rede do Computador

#### Descoberta Automática
```python
# network_scanner.py
import socket
import threading

def scan_network(port=8080):
    """Escaneia rede em busca de dispositivos JARVIS"""
    devices = []
    
    def check_host(ip):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((ip, port))
            if result == 0:
                devices.append(ip)
            sock.close()
        except:
            pass
    
    # Varredura da rede local
    for i in range(1, 255):
        ip = f"192.168.1.{i}"
        thread = threading.Thread(target=check_host, args=(ip,))
        thread.start()
    
    return devices

if __name__ == "__main__":
    devices = scan_network()
    print(f"Dispositivos encontrados: {devices}")
```

## Teste do Sistema

### 1. Teste Básico de Voz

#### test_voice.py
```python
import speech_recognition as sr
from gtts import gTTS
import os

def test_voice_system():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    print("Teste do sistema de voz")
    print("========================")
    
    # Teste de reconhecimento
    with microphone as source:
        print("1. Teste de reconhecimento - Fale 'teste'")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    
    try:
        text = recognizer.recognize_google(audio, language="pt-BR")
        print(f"Reconhecido: {text}")
        
        if "teste" in text.lower():
            print("✅ Reconhecimento funcionando!")
        else:
            print("❌ Reconhecimento com problemas")
    except:
        print("❌ Falha no reconhecimento")
    
    # Teste de síntese
    try:
        print("2. Teste de síntese de voz")
        tts = gTTS("Sistema de voz funcionando corretamente", lang="pt-BR")
        tts.save("test_output.mp3")
        
        # Reproduzir (Windows)
        if os.name == 'nt':
            os.system("start test_output.mp3")
        else:
            os.system("mpg321 test_output.mp3")
        
        print("✅ Síntese de voz funcionando!")
        os.remove("test_output.mp3")
    except:
        print("❌ Falha na síntese de voz")

if __name__ == "__main__":
    test_voice_system()
```

### 2. Teste de Comunicação Serial

#### test_serial.py
```python
import serial
import json
import time

def test_serial_communication(port=None, baudrate=115200):
    try:
        # Auto-detectar porta se não especificada
        if port is None:
            import serial.tools.list_ports
            ports = serial.tools.list_ports.comports()
            if ports:
                port = ports[0].device
            else:
                print("❌ Nenhuma porta serial encontrada")
                return
        
        print(f"Testando comunicação serial na porta {port}")
        
        # Conectar
        ser = serial.Serial(port, baudrate, timeout=5)
        time.sleep(2)  # Aguardar conexão
        
        # Enviar comando de teste
        test_command = {
            "type": "command",
            "id": "test_001",
            "device": "status",
            "action": "ping"
        }
        
        command_str = json.dumps(test_command) + "\n"
        ser.write(command_str.encode())
        
        # Aguardar resposta
        response = ser.readline().decode().strip()
        
        if response:
            print(f"✅ Resposta recebida: {response}")
        else:
            print("❌ Sem resposta do dispositivo")
        
        ser.close()
        
    except Exception as e:
        print(f"❌ Erro na comunicação serial: {e}")

if __name__ == "__main__":
    test_serial_communication()
```

### 3. Teste de Integração

#### test_integration.py
```python
import sys
import os
sys.path.append('src')

from core.voice_engine import VoiceEngine
from hardware.serial_comm import SerialCommunicator
from utils.logger import setup_logger

def test_full_integration():
    logger = setup_logger("test")
    
    print("Teste de Integração Completo")
    print("==========================")
    
    try:
        # Inicializar componentes
        voice_engine = VoiceEngine()
        serial_comm = SerialCommunicator()
        
        print("✅ Componentes inicializados")
        
        # Testar comunicação
        if serial_comm.connect():
            print("✅ Comunicação serial estabelecida")
        else:
            print("❌ Falha na comunicação serial")
            return
        
        # Testar reconhecimento de voz
        print("Diga 'ligar luz' para testar...")
        audio_data = voice_engine.listen_for_command(timeout=10)
        
        if audio_data:
            text = voice_engine.recognize(audio_data)
            print(f"Comando reconhecido: {text}")
            
            if "ligar" in text.lower() and "luz" in text.lower():
                # Enviar comando para hardware
                command = {
                    "type": "command",
                    "device": "led_1",
                    "action": "set_state",
                    "parameters": {"state": "on"}
                }
                
                if serial_comm.send_command(command):
                    print("✅ Comando enviado com sucesso")
                else:
                    print("❌ Falha ao enviar comando")
            else:
                print("Comando não reconhecido")
        else:
            print("❌ Nenhum áudio capturado")
        
        serial_comm.disconnect()
        print("✅ Teste concluído")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")

if __name__ == "__main__":
    test_full_integration()
```

## Configuração Avançada

### 1. Otimização de Performance

#### Configurações de Áudio
```python
# config/audio_config.py
AUDIO_CONFIG = {
    'sample_rate': 16000,
    'chunk_size': 1024,
    'channels': 1,
    'format': 'int16',
    'noise_reduction': True,
    'auto_gain': True,
    'vad_threshold': 0.5
}
```

#### Configurações de IA
```python
# config/ai_config.py
AI_CONFIG = {
    'model': 'gpt-3.5-turbo',
    'max_tokens': 100,
    'temperature': 0.7,
    'timeout': 30,
    'retry_attempts': 3,
    'cache_responses': True
}
```

### 2. Configuração de Segurança

#### Firewall
```bash
# Windows (PowerShell - Administrador)
New-NetFirewallRule -DisplayName "JARVIS" -Direction Inbound -Port 8080 -Protocol TCP -Action Allow

# Linux
sudo ufw allow 8080/tcp
sudo ufw reload
```

#### SSL/TLS
```python
# config/ssl_config.py
SSL_CONFIG = {
    'cert_file': 'certificates/server.crt',
    'key_file': 'certificates/server.key',
    'ca_file': 'certificates/ca.crt',
    'require_client_cert': False
}
```

### 3. Configuração de Logging

#### config/logging_config.py
```python
import logging
from logging.handlers import RotatingFileHandler
import colorlog

def setup_logger(name, level='INFO'):
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level))
    
    # Console handler com cores
    console_handler = colorlog.StreamHandler()
    console_formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # File handler com rotação
    file_handler = RotatingFileHandler(
        f'logs/{name}.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger
```

## Solução de Problemas

### Problemas Comuns

#### 1. Microfone não funciona
```bash
# Verificar dispositivos de áudio
# Windows
python -c "import speech_recognition as sr; print(sr.Microphone.list_microphone_names())"

# Linux
arecord -l
```

#### 2. Porta serial não encontrada
```bash
# Listar portas seriais
python -c "import serial.tools.list_ports; print([p.device for p in serial.tools.list_ports.comports()])"
```

#### 3. Erro de permissão (Linux)
```bash
# Adicionar usuário ao grupo dialout
sudo usermod -a -G dialout $USER
# Fazer logout e login novamente
```

#### 4. Conexão Wi-Fi falha
```cpp
// Reset de configurações WiFi
WiFi.disconnect(true);
delay(1000);
WiFi.begin(ssid, password);
```

### Logs e Debug

#### Ativar Debug Mode
```python
# Em config/settings.py
DEBUG = True
LOG_LEVEL = 'DEBUG'
```

#### Verificar Logs
```bash
# Ver logs em tempo real
tail -f logs/jarvis.log

# Filtrar erros
grep ERROR logs/jarvis.log
```

## Próximos Passos

1. **Executar testes completos** para verificar funcionamento
2. **Configurar automações** específicas para seu ambiente
3. **Adicionar dispositivos** conforme necessidade
4. **Personalizar respostas** e comportamentos
5. **Implementar segurança** adicional se necessário

## Suporte

- **Documentação**: [docs/](../docs/)
- **Issues**: GitHub Issues
- **Comunidade**: Fórum do projeto
- **Email**: support@jarvis-project.com
