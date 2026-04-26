#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JARVIS - Assistente Virtual Inteligente
Ponto de entrada principal do sistema

Este arquivo contém a classe principal do assistente JARVIS, responsável por:
- Inicializar todos os componentes do sistema
- Gerenciar os modos de operação (passivo, ativo, processamento)
- Controlar o loop principal do assistente
- Coordenar reconhecimento de voz e síntese de fala
"""

# Importações de bibliotecas padrão Python
import sys      # Para manipulação de argumentos de linha de comando e saída do sistema
import time     # Para controle de tempo e delays
import threading  # Para operações concorrentes (escuta contínua sem bloquear)
from pathlib import Path  # Para manipulação de caminhos de arquivos de forma segura
import pyttsx3          # Para o JARVIS falar
import sounddevice as sd  # Para verificar o microfone

# Importação de nossos módulos personalizados
from test_audio import VoskRecognizer  # Importa nossa classe de reconhecimento de voz já testada


class JarvisAssistant:
    """
    Classe principal do assistente JARVIS
    
    Responsabilidades:
    - Gerenciar o estado geral do sistema
    - Controlar os modos de operação
    - Coordenar todos os componentes (reconhecimento, síntese, hardware)
    - Implementar o loop principal do assistente
    """
    
    def __init__(self):
        """
        Construtor da classe JarvisAssistant
        
        Inicializa os atributos básicos do sistema:
        - running: Controla se o sistema está ativo ou deve encerrar
        - wake_word: Palavra que ativa o assistente ("jarvis")
        - mode: Modo atual de operação ("passive", "active", "processing")
        """
        # Atributos de controle do sistema
        self.running = False          # Flag para controlar se o sistema está rodando
        self.wake_word = "jarvis"     # Palavra de ativação do assistente
        self.mode = "passive"         # Modo inicial: passivo (apenas escutando wake word)
        
        # Componentes do sistema (serão inicializados em initialize_system)
        self.vosk_recognizer = None    # Reconhecedor de voz Vosk
        self.voice_engine = None       # Sintetizador de voz pyttsx3
        self.audio_devices = []        # Lista de dispositivos de áudio
        self.selected_device = None    # Dispositivo de áudio selecionado
        
        # Mensagens de inicialização para feedback ao usuário
        print("JARVIS - Assistente Virtual Inteligente")
        print("Inicializando sistema...")
    
    def initialize_system(self):
        """
        Inicializar todos os componentes do sistema
        
        Implementação completa:
        - Carregar o modelo Vosk para reconhecimento de voz
        - Configurar o sintetizador de voz (pyttsx3)
        - Verificar dispositivos de áudio disponíveis
        - Preparar comunicação com hardware (se disponível)
        - Configurar parâmetros iniciais do sistema
        
        Returns:
            bool: True se sistema inicializado com sucesso, False caso contrário
        """
        print("Inicializando componentes do sistema...")
        
        try:
            # 1. Inicializar o reconhecedor de voz Vosk
            print("1. Configurando reconhecimento de voz...")
            try:
                self.vosk_recognizer = VoskRecognizer()
                
                if not self.vosk_recognizer.load_model():
                    print("[ERRO] Falha ao carregar modelo Vosk")
                    print("[INFO] Verifique se o modelo está em: models/vosk-model-small-pt-0.3/")
                    print("[INFO] Certifique-se de que o modelo foi baixado e extraído corretamente")
                    return False
            except FileNotFoundError:
                print("[ERRO] Modelo Vosk não encontrado!")
                print("[INFO] O modelo deve estar em: models/vosk-model-small-pt-0.3/")
                print("[INFO] Baixe o modelo em: https://alphacephei.com/vosk/models")
                return False
            except Exception as e:
                print(f"[ERRO] Erro ao inicializar Vosk: {e}")
                print("[INFO] Verifique se a biblioteca vosk está instalada: pip install vosk")
                return False
            
            print("[OK] Reconhecimento de voz configurado")
            
            # 2. Configurar o sintetizador de voz
            print("2. Configurando síntese de voz...")
            try:
                self.voice_engine = pyttsx3.init()
            except Exception as e:
                print(f"[ERRO] Erro ao inicializar pyttsx3: {e}")
                print("[INFO] Verifique se a biblioteca pyttsx3 está instalada: pip install pyttsx3")
                print("[INFO] No Windows, pode ser necessário instalar drivers de áudio adicionais")
                return False
            
            # Configurar voz em português se disponível
            voices = self.voice_engine.getProperty('voices')
            portuguese_voice_found = False
            
            for voice in voices:
                try:
                    lang = getattr(voice, 'languages', [getattr(voice, 'lang', 'unknown')])[0] if hasattr(voice, 'languages') else getattr(voice, 'lang', 'unknown')
                    if 'pt' in str(lang).lower() or 'brazil' in voice.name.lower():
                        self.voice_engine.setProperty('voice', voice.id)
                        print(f"[OK] Voz selecionada: {voice.name}")
                        portuguese_voice_found = True
                        break
                except:
                    continue
            
            if not portuguese_voice_found:
                print("[AVISO] Voz em português não encontrada, usando padrão")
            
            # Configurar velocidade e volume
            self.voice_engine.setProperty('rate', 200)  # Velocidade normal
            self.voice_engine.setProperty('volume', 0.9)  # Volume alto
            
            print("[OK] Síntese de voz configurada")
            
            # 3. Verificar dispositivos de áudio
            print("3. Verificando dispositivos de áudio...")
            try:
                devices = sd.query_devices()
            except Exception as e:
                print(f"[ERRO] Erro ao acessar dispositivos de áudio: {e}")
                print("[INFO] Verifique se a biblioteca sounddevice está instalada: pip install sounddevice")
                print("[INFO] Certifique-se de que o microfone está conectado e funcionando")
                print("[INFO] No Windows, pode ser necessário instalar PortAudio")
                return False
            
            # Listar dispositivos de entrada (microfones)
            input_devices = []
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    input_devices.append({
                        'id': i,
                        'name': device['name'],
                        'channels': device['max_input_channels']
                    })
            
            self.audio_devices = input_devices
            
            if not self.audio_devices:
                print("[ERRO] Nenhum dispositivo de entrada encontrado")
                return False
            
            print(f"[OK] Encontrados {len(self.audio_devices)} dispositivos de entrada:")
            for device in self.audio_devices:
                print(f"   - {device['name']} (ID: {device['id']})")
            
            # Selecionar automaticamente o primeiro dispositivo
            self.selected_device = self.audio_devices[0]['id']
            print(f"[OK] Dispositivo selecionado: {self.audio_devices[0]['name']}")
            
            # 4. Testar componentes
            print("4. Testando componentes...")
            
            # Testar síntese de voz
            print("   Testando síntese de voz...")
            self.speak("Sistema JARVIS online e pronto para uso.")
            
            # 5. Configurar atributos finais
            print("5. Finalizando configuração...")
            self.running = True
            
            print("\n[OK] Sistema JARVIS inicializado com sucesso!")
            print("[INFO] Diga 'Jarvis' seguido do seu comando.")
            print("[INFO] Pressione Ctrl+C para encerrar.")
            print("-" * 50)
            
            return True
            
        except Exception as e:
            print(f"[ERRO] Falha na inicialização: {e}")
            print("[INFO] Verifique se todas as dependências estão instaladas:")
            print("      pip install vosk pyttsx3 sounddevice numpy")
            print("[INFO] Verifique se o modelo Vosk está no local correto")
            print("[INFO] Verifique se o microfone está conectado")
            return False
    
    def speak(self, text):
        """
        Sintetizar resposta em voz
        
        Args:
            text (str): Texto a ser falado pelo assistente
        """
        try:
            if self.voice_engine:
                print(f"JARVIS: {text}")
                self.voice_engine.say(text)
                self.voice_engine.runAndWait()
            else:
                print(f"[ERRO] Motor de voz não inicializado: {text}")
        except Exception as e:
            print(f"[ERRO] Falha na síntese de voz: {e}")
    
    def run(self):
        """
        Loop principal do assistente
        
        Este método será implementado nos próximos passos para:
        - Manter o sistema em execução contínua
        - Gerenciar transições entre modos (passive → active → processing → passive)
        - Processar comandos reconhecidos
        - Executar ações e gerar respostas
        - Tratar exceções e erros gracefulmente
        """
        print("Sistema JARVIS iniciado!")
        # Implementar nos próximos passos
        pass


def main():
    """
    Função principal de entrada do programa
    
    Fluxo de execução:
    1. Cria uma instância do JarvisAssistant
    2. Inicializa o sistema
    3. Inicia o loop principal
    4. Trata interrupções do usuário (Ctrl+C)
    5. Trata erros fatais de forma segura
    
    Returns:
        None: O programa encerra com código de saída apropriado
    """
    try:
        # Criar instância do assistente
        jarvis = JarvisAssistant()
        
        # Inicializar componentes do sistema
        jarvis.initialize_system()
        
        # Iniciar loop principal do assistente
        jarvis.run()
        
    except KeyboardInterrupt:
        # Trata interrupção do usuário (Ctrl+C)
        print("\nInterrupção do usuário")
        print("Encerrando sistema...")
        
    except Exception as e:
        # Trata erros fatais inesperados
        print(f"Erro fatal: {e}")
        # Encerra o programa com código de erro 1
        sys.exit(1)


if __name__ == "__main__":
    """
    Ponto de entrada do script
    
    Este bloco garante que o código só será executado quando:
    - O script for chamado diretamente: python main.py
    - O script for executável: ./main.py
    - Não será executado quando importado como módulo
    """
    main()
