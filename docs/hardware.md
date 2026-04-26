# Componentes de Hardware - JARVIS

## Visão Geral

O hardware do JARVIS consiste em microcontroladores programados em C/C++ que atuam como interface física entre o sistema inteligente e o mundo real, controlando sensores e atuadores diversos.

## Plataformas Suportadas

### 1. ESP32 (Recomendado)
- **Processador**: Dual-core Xtensa LX6 @ 240MHz
- **Memória**: 520KB SRAM, 4-16MB Flash
- **Conectividade**: Wi-Fi 802.11 b/g/n, Bluetooth 4.2
- **GPIO**: 34 pinos programáveis
- **Interfaces**: UART, SPI, I2C, I2S, ADC, DAC
- **Vantagens**: Wi-Fi integrado, maior poder de processamento

### 2. Arduino (Alternativa)
- **Processador**: ATmega328P @ 16MHz (Uno)
- **Memória**: 2KB SRAM, 32KB Flash
- **GPIO**: 14 pinos digitais, 6 pinos analógicos
- **Interfaces**: UART, SPI, I2C
- **Vantagens**: Simplicidade, baixo custo, vasta documentação

## Estrutura do Firmware

```
firmware/
├── src/
│   ├── main.cpp              # Ponto de entrada principal
│   ├── communication/
│   │   ├── serial_handler.cpp # Comunicação serial
│   │   ├── wifi_handler.cpp   # Comunicação Wi-Fi
│   │   └── protocol.cpp       # Protocolo de mensagens
│   ├── devices/
│   │   ├── relay_controller.cpp # Controle de relés
│   │   ├── led_controller.cpp   # Controle de LEDs
│   │   ├── motor_controller.cpp  # Controle de motores
│   │   └── sensor_manager.cpp    # Gerenciamento de sensores
│   ├── utils/
│   │   ├── json_parser.cpp   # Parser JSON
│   │   ├── timer.cpp          # Utilitários de tempo
│   │   └── logger.cpp         # Sistema de logging
│   └── config/
│       ├── pins.h            # Definição de pinos
│       └── settings.h        # Configurações do sistema
├── libraries/                # Bibliotecas personalizadas
├── platformio.ini            # Configuração PlatformIO
└── README.md                 # Documentação do firmware
```

## Componentes Principais

### 1. Gerenciador de Comunicação

#### Serial Handler (serial_handler.cpp)
```cpp
class SerialHandler {
private:
    HardwareSerial* serial;
    uint32_t baudrate;
    char buffer[512];
    int buffer_index;
    
public:
    SerialHandler(HardwareSerial* ser, uint32_t baud);
    void begin();
    bool send_message(const char* message);
    bool receive_message(char* message, int max_length);
    void process_incoming_data();
};
```

#### Wi-Fi Handler (wifi_handler.cpp)
```cpp
class WiFiHandler {
private:
    WiFiServer server;
    WiFiClient client;
    const char* ssid;
    const char* password;
    int port;
    
public:
    WiFiHandler(const char* ssid, const char* pwd, int port = 8080);
    bool connect_to_network();
    void start_server();
    bool send_message(const char* message);
    bool receive_message(char* message, int max_length);
    void handle_clients();
};
```

### 2. Controladores de Dispositivos

#### Relay Controller (relay_controller.cpp)
```cpp
class RelayController {
private:
    struct Relay {
        uint8_t pin;
        bool state;
        const char* name;
    };
    
    Relay relays[8];
    int relay_count;
    
public:
    RelayController();
    void add_relay(uint8_t pin, const char* name);
    bool set_relay_state(int relay_id, bool state);
    bool get_relay_state(int relay_id);
    void toggle_relay(int relay_id);
    void set_all_relays(bool state);
};
```

#### LED Controller (led_controller.cpp)
```cpp
class LEDController {
private:
    struct LED {
        uint8_t pin;
        uint8_t brightness;
        bool state;
        const char* name;
    };
    
    LED leds[16];
    int led_count;
    
public:
    LEDController();
    void add_led(uint8_t pin, const char* name);
    void set_led_brightness(int led_id, uint8_t brightness);
    void set_led_state(int led_id, bool state);
    void fade_led(int led_id, uint8_t from, uint8_t to, int duration);
    void blink_led(int led_id, int times, int on_duration, int off_duration);
};
```

#### Motor Controller (motor_controller.cpp)
```cpp
class MotorController {
private:
    struct Motor {
        uint8_t pin1;
        uint8_t pin2;
        uint8_t enable_pin;
        int speed;
        bool direction;
        const char* name;
    };
    
    Motor motors[4];
    int motor_count;
    
public:
    MotorController();
    void add_motor(uint8_t pin1, uint8_t pin2, uint8_t enable, const char* name);
    void set_motor_speed(int motor_id, int speed);
    void set_motor_direction(int motor_id, bool forward);
    void stop_motor(int motor_id);
    void stop_all_motors();
};
```

### 3. Gerenciador de Sensores

#### Sensor Manager (sensor_manager.cpp)
```cpp
class SensorManager {
private:
    struct Sensor {
        uint8_t pin;
        uint8_t type;
        float value;
        uint32_t last_read;
        uint32_t read_interval;
        const char* name;
    };
    
    Sensor sensors[32];
    int sensor_count;
    
public:
    enum SensorType {
        TEMPERATURE_DHT22,
        HUMIDITY_DHT22,
        LIGHT_LDR,
        MOTION_PIR,
        DISTANCE_ULTRASONIC,
        DIGITAL_INPUT,
        ANALOG_INPUT
    };
    
    SensorManager();
    void add_sensor(uint8_t pin, SensorType type, const char* name, uint32_t interval = 1000);
    float read_sensor(int sensor_id);
    void update_all_sensors();
    float get_sensor_value(int sensor_id);
    const char* get_sensor_name(int sensor_id);
};
```

## Protocolo de Comunicação

### Formato de Mensagem JSON
```json
{
  "type": "command|response|sensor_data|status",
  "id": "unique_message_id",
  "timestamp": 1640995200,
  "device": "device_name",
  "action": "action_name",
  "parameters": {
    "param1": "value1",
    "param2": 123
  },
  "data": {
    "additional": "data"
  }
}
```

### Tipos de Mensagens

#### Comando de Controle
```json
{
  "type": "command",
  "id": "cmd_001",
  "timestamp": 1640995200,
  "device": "relay_1",
  "action": "set_state",
  "parameters": {
    "state": "on"
  }
}
```

#### Resposta de Status
```json
{
  "type": "response",
  "id": "resp_001",
  "timestamp": 1640995201,
  "device": "relay_1",
  "action": "set_state",
  "parameters": {
    "state": "on",
    "success": true
  }
}
```

#### Dados de Sensor
```json
{
  "type": "sensor_data",
  "id": "sensor_001",
  "timestamp": 1640995202,
  "device": "temperature_sensor",
  "action": "read_value",
  "data": {
    "value": 25.5,
    "unit": "celsius"
  }
}
```

## Configurações

### pins.h (ESP32)
```cpp
#ifndef PINS_H
#define PINS_H

// Relés
#define RELAY_1_PIN    23
#define RELAY_2_PIN    22
#define RELAY_3_PIN    21
#define RELAY_4_PIN    19

// LEDs
#define LED_STATUS_PIN 2
#define LED_1_PIN      18
#define LED_2_PIN      5
#define LED_3_PIN      17

// Motores
#define MOTOR1_PIN1    16
#define MOTOR1_PIN2    4
#define MOTOR1_EN      0

// Sensores
#define DHT22_PIN      15
#define LDR_PIN        34
#define PIR_PIN        35
#define ULTRASONIC_TRIG 32
#define ULTRASONIC_ECHO 33

// Comunicação
#define SERIAL_TX_PIN  1
#define SERIAL_RX_PIN  3

#endif
```

### settings.h
```cpp
#ifndef SETTINGS_H
#define SETTINGS_H

// Configurações de comunicação
#define SERIAL_BAUDRATE      115200
#define WIFI_PORT            8080
#define MAX_MESSAGE_LENGTH   512
#define MESSAGE_TIMEOUT      5000

// Configurações de sensores
#define SENSOR_READ_INTERVAL 1000
#define DHT22_TYPE           DHT22
#define MAX_SENSORS          32

// Configurações de dispositivos
#define MAX_RELAYS           8
#define MAX_LEDS             16
#define MAX_MOTORS           4

// Configurações do sistema
#define SYSTEM_CHECK_INTERVAL 100
#define WATCHDOG_TIMEOUT      10000
#define LOG_LEVEL             INFO

#endif
```

## Exemplo de Implementação Completa

### main.cpp
```cpp
#include <Arduino.h>
#include <WiFi.h>
#include <ArduinoJson.h>
#include "communication/serial_handler.h"
#include "communication/wifi_handler.h"
#include "devices/relay_controller.h"
#include "devices/led_controller.h"
#include "devices/sensor_manager.h"
#include "config/pins.h"
#include "config/settings.h"

// Instâncias globais
SerialHandler serialHandler(&Serial, SERIAL_BAUDRATE);
WiFiHandler wifiHandler("JARVIS_Network", "password123", WIFI_PORT);
RelayController relayController;
LEDController ledController;
SensorManager sensorManager;

unsigned long last_sensor_update = 0;
unsigned long last_system_check = 0;

void setup() {
    Serial.begin(SERIAL_BAUDRATE);
    
    // Inicializa dispositivos
    initialize_devices();
    
    // Conecta Wi-Fi
    wifiHandler.connect_to_network();
    wifiHandler.start_server();
    
    // Configura LED de status
    pinMode(LED_STATUS_PIN, OUTPUT);
    digitalWrite(LED_STATUS_PIN, HIGH);
    
    Serial.println("JARVIS Hardware Controller v1.0");
}

void loop() {
    // Processa comunicação serial
    serialHandler.process_incoming_data();
    
    // Processa comunicação Wi-Fi
    wifiHandler.handle_clients();
    
    // Atualiza sensores
    if (millis() - last_sensor_update > SENSOR_READ_INTERVAL) {
        sensorManager.update_all_sensors();
        send_sensor_data();
        last_sensor_update = millis();
    }
    
    // Verificação do sistema
    if (millis() - last_system_check > SYSTEM_CHECK_INTERVAL) {
        system_health_check();
        last_system_check = millis();
    }
    
    delay(10);
}

void initialize_devices() {
    // Adiciona relés
    relayController.add_relay(RELAY_1_PIN, "relay_1");
    relayController.add_relay(RELAY_2_PIN, "relay_2");
    relayController.add_relay(RELAY_3_PIN, "relay_3");
    relayController.add_relay(RELAY_4_PIN, "relay_4");
    
    // Adiciona LEDs
    ledController.add_led(LED_STATUS_PIN, "status_led");
    ledController.add_led(LED_1_PIN, "led_1");
    ledController.add_led(LED_2_PIN, "led_2");
    ledController.add_led(LED_3_PIN, "led_3");
    
    // Adiciona sensores
    sensorManager.add_sensor(DHT22_PIN, SensorManager::TEMPERATURE_DHT22, "temperature");
    sensorManager.add_sensor(DHT22_PIN, SensorManager::HUMIDITY_DHT22, "humidity");
    sensorManager.add_sensor(LDR_PIN, SensorManager::LIGHT_LDR, "light");
    sensorManager.add_sensor(PIR_PIN, SensorManager::MOTION_PIR, "motion");
}

void process_command(char* command) {
    DynamicJsonDocument doc(512);
    DeserializationError error = deserializeJson(doc, command);
    
    if (error) {
        Serial.println("JSON parse error");
        return;
    }
    
    String device = doc["device"];
    String action = doc["action"];
    
    if (device.startsWith("relay")) {
        handle_relay_command(device, action, doc);
    } else if (device.startsWith("led")) {
        handle_led_command(device, action, doc);
    } else if (device.startsWith("motor")) {
        handle_motor_command(device, action, doc);
    }
}

void handle_relay_command(String device, String action, JsonDocument& doc) {
    int relay_id = device.substring(5).toInt() - 1;
    
    if (action == "set_state") {
        bool state = doc["parameters"]["state"] == "on";
        relayController.set_relay_state(relay_id, state);
        send_response(device, action, state);
    } else if (action == "toggle") {
        relayController.toggle_relay(relay_id);
        send_response(device, action, relayController.get_relay_state(relay_id));
    }
}

void send_sensor_data() {
    for (int i = 0; i < sensorManager.get_sensor_count(); i++) {
        float value = sensorManager.get_sensor_value(i);
        const char* name = sensorManager.get_sensor_name(i);
        
        DynamicJsonDocument doc(256);
        doc["type"] = "sensor_data";
        doc["device"] = name;
        doc["data"]["value"] = value;
        
        String message;
        serializeJson(doc, message);
        
        serialHandler.send_message(message.c_str());
    }
}
```

## Bibliotecas Necessárias

### PlatformIO (platformio.ini)
```ini
[env:esp32dev]
platform = espressif32
board = esp32dev
framework = arduino
monitor_speed = 115200

lib_deps = 
    bblanchon/ArduinoJson@6.19.4
    adafruit/DHT sensor library@1.4.3
    adafruit/Adafruit Unified Sensor@1.1.9
    WiFi
    HTTPClient
```

### Bibliotecas Arduino
- `ArduinoJson` - Processamento JSON
- `DHT sensor library` - Sensores DHT22
- `WiFi` - Conectividade Wi-Fi
- `HTTPClient` - Cliente HTTP
- `Servo` - Controle de servomotores
- `Stepper` - Controle de motores de passo

## Considerações de Hardware

### Especificações Elétricas
- **Tensão de operação**: 3.3V (ESP32) / 5V (Arduino)
- **Corrente máxima**: 40mA por pino GPIO
- **Níveis lógicos**: 3.3V/5V (verificar compatibilidade)
- **Proteção**: Diodos e resistores quando necessário

### Conexões Típicas

#### Relé
```
ESP32 GPIO → Resistor 1K → Transistor BC547 Base
Transistor Emissor → GND
Transistor Coletor → Relé Coil
Relé Coil → VCC (5V/12V)
Diodo 1N4007 em paralelo com relé (polaridade reversa)
```

#### Sensor DHT22
```
DHT22 VCC → 3.3V
DHT22 GND → GND
DHT22 Data → ESP32 GPIO + Resistor 10K para 3.3V
```

#### Motor DC
```
ESP32 PWM → Driver L298N Enable
ESP32 GPIO1 → Driver L298N Input1
ESP32 GPIO2 → Driver L298N Input2
Driver L298N → Motor DC
```

## Debug e Testes

### Serial Debug
```cpp
#define DEBUG 1

#if DEBUG
  #define DEBUG_PRINT(x)     Serial.print (x)
  #define DEBUG_PRINTDEC(x)     Serial.print (x, DEC)
  #define DEBUG_PRINTLN(x)  Serial.println (x)
#else
  #define DEBUG_PRINT(x)
  #define DEBUG_PRINTDEC(x)
  #define DEBUG_PRINTLN(x)
#endif
```

### Teste de Componentes
```cpp
void test_all_components() {
    DEBUG_PRINTLN("Testing components...");
    
    // Testa relés
    for (int i = 0; i < 4; i++) {
        relayController.set_relay_state(i, true);
        delay(500);
        relayController.set_relay_state(i, false);
        delay(500);
    }
    
    // Testa LEDs
    for (int i = 0; i < 4; i++) {
        ledController.set_led_state(i, true);
        delay(200);
        ledController.set_led_state(i, false);
    }
    
    DEBUG_PRINTLN("Component test completed");
}
```

## Segurança e Confiabilidade

### Watchdog Timer
```cpp
void setup_watchdog() {
    esp_task_wdt_init(WATCHDOG_TIMEOUT, true);
    esp_task_wdt_add(NULL);
}

void feed_watchdog() {
    esp_task_wdt_reset();
}
```

### Tratamento de Erros
```cpp
void handle_error(const char* error_message) {
    DEBUG_PRINT("ERROR: ");
    DEBUG_PRINTLN(error_message);
    
    // Pisca LED de status rapidamente
    for (int i = 0; i < 10; i++) {
        digitalWrite(LED_STATUS_PIN, HIGH);
        delay(100);
        digitalWrite(LED_STATUS_PIN, LOW);
        delay(100);
    }
    
    // Reinicia sistema
    ESP.restart();
}
```

## Performance e Otimização

### Uso de Memória
- **RAM**: Monitorar uso com `ESP.getFreeHeap()`
- **Flash**: Otimizar strings constantes
- **Buffers**: Tamanhos mínimos necessários

### Latência
- **Comunicação**: <10ms para mensagens locais
- **Sensores**: <100ms para leitura
- **Atuadores**: <50ms para resposta

### Consumo de Energia
- **Deep Sleep**: Para operações em bateria
- **Clock scaling**: Reduz frequência quando ocioso
- **Power management**: Desligar periféricos não utilizados
