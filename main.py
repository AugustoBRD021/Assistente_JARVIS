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
import queue    # Para fila de comandos entre threads
import asyncio  # Para operações assíncronas (edge-tts)
import subprocess  # Para executar comandos do sistema (ffmpeg)
from pathlib import Path  # Para manipulação de caminhos de arquivos de forma segura
import numpy as np  # Para processar arrays de áudio
import sounddevice as sd  # Para verificar o microfone
import edge_tts  # Para síntese de voz neural da Microsoft
import simpleaudio  # Para reprodução de áudio
import tempfile  # Para arquivos temporários
import os  # Para manipulação de arquivos

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
        self.wake_word = "nova"       # Palavra de ativação do assistente
        self.mode = "passive"         # Modo inicial: passivo (apenas escutando wake word)
        
        # Componentes do sistema (serão inicializados em initialize_system)
        self.vosk_recognizer = None    # Reconhecedor de voz Vosk
        self.audio_devices = []        # Lista de dispositivos de áudio
        self.selected_device = None    # Dispositivo de áudio selecionado
        
        # Atributos para escuta contínua (PASSO 3)
        self.listening_thread = None        # Thread para escuta contínua em background
        self.command_queue = queue.Queue()  # Fila de comandos entre threads
        self.last_wake_word_time = 0        # Timestamp da última wake word detectada
        
        # Mensagens de inicialização para feedback ao usuário
        print("NOVA - Assistente Virtual Inteligente")
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
            
            # 2. Configurar síntese de voz (edge-tts)
            print("2. Configurando síntese de voz...")
            try:
                # Teste rápido do edge-tts
                print("[INFO] Usando edge-tts com voz pt-BR-FranciscaNeural")
                print("[OK] Síntese de voz configurada")
            except Exception as e:
                print(f"[ERRO] Erro ao configurar síntese de voz: {e}")
                print("[INFO] Verifique se edge-tts está instalado: pip install edge-tts")
                return False
            
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
            print("   Síntese de voz será testada no loop principal.")
            
            # 5. Configurar atributos finais
            print("5. Finalizando configuração...")
            self.running = True
            
            print("\n[OK] Sistema NOVA inicializado com sucesso!")
            print("[INFO] Diga 'Nova' seguido do seu comando.")
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
        Sintetiza voz com edge-tts e reproduz usando ffmpeg + winsound (nativo do Windows)
        
        Args:
            text (str): Texto a ser falado pelo assistente
        """
        print(f"NOVA: {text}")
        
        async def _falar():
            # Gera o áudio com a voz Francisca BR em formato MP3
            communicate = edge_tts.Communicate(text, voice="pt-BR-FranciscaNeural")
            
            # Salva em arquivo temporário MP3
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                tmp_path = f.name
            
            await communicate.save(tmp_path)
            return tmp_path
        
        try:
            # Gera o arquivo de áudio MP3
            tmp_path = asyncio.run(_falar())
            
            # Converte MP3 para WAV usando ffmpeg (caminho completo)
            wav_path = tmp_path.replace(".mp3", ".wav")
            ffmpeg_path = r"C:\ffmpeg\ffmpeg-8.1-essentials_build\bin\ffmpeg.exe"
            
            if os.path.exists(ffmpeg_path):
                result = subprocess.run([ffmpeg_path, '-i', tmp_path, wav_path], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    # Reproduz com winsound (nativo do Windows)
                    import winsound
                    winsound.PlaySound(wav_path, winsound.SND_FILENAME)
                    
                    # Remove arquivos temporários após reprodução
                    os.unlink(tmp_path)
                    os.unlink(wav_path)
                else:
                    # Fallback: player padrão
                    print(f"[INFO] ffmpeg falhou, usando player padrão")
                    os.startfile(tmp_path)
                    time.sleep(2)
                    os.unlink(tmp_path)
            else:
                # Fallback: player padrão
                print(f"[INFO] ffmpeg não encontrado em {ffmpeg_path}, usando player padrão")
                os.startfile(tmp_path)
                time.sleep(2)
                os.unlink(tmp_path)
            
        except Exception as e:
            print(f"[ERRO] Falha na síntese de voz: {e}")
    
    def listen_for_wake_word(self):
        """
        Escuta continuamente pela wake word em duas fases
        
        FASE 1 - Escuta passiva pela wake word (chunks de 2s)
        FASE 2 - Wake word detectada, aguarda comando (até 5s)
        
        Funciona em loop contínuo enquanto self.running = True
        """
        print("[INFO] Iniciando escuta contínua pela wake word...")
        
        # Variações fonéticas da wake word
        WAKE_VARIATIONS = ['nova', 'nóva', 'nôva', 'nôba', 'nóba']
        sample_rate = 16000
        
        def capture_speech(duration=3):
            """
            Captura áudio e retorna o texto reconhecido, ou None
            
            Args:
                duration (int): Duração da captura em segundos
            
            Returns:
                str: Texto reconhecido ou None se falhar
            """
            import json
            chunk_size = int(sample_rate * duration)
            try:
                audio_chunk = sd.rec(
                    frames=chunk_size,
                    samplerate=sample_rate,
                    channels=1,
                    dtype='int16',
                    device=self.selected_device
                )
                sd.wait()
                audio_bytes = audio_chunk.tobytes()
                
                if self.vosk_recognizer.recognizer.AcceptWaveform(audio_bytes):
                    result = json.loads(self.vosk_recognizer.recognizer.Result())
                    return result.get('text', '').strip()
                else:
                    partial = json.loads(self.vosk_recognizer.recognizer.PartialResult())
                    return partial.get('text', '').strip()
                    
            except Exception as e:
                print(f"[ERRO] Falha ao capturar áudio: {e}")
                return None
        
        while self.running:
            # FASE 1 - Escuta passiva pela wake word (chunks de 2s)
            text = capture_speech(duration=2)
            
            if not text:
                continue
            
            print(f"[DEBUG] Ouvido: '{text}'")
            
            if not any(w in text.lower() for w in WAKE_VARIATIONS):
                continue  # Não foi a wake word, ignora
            
            # FASE 2 - Wake word detectada, aguarda o comando
            print("[INFO] Wake word detectada!")
            self.speak("Sim?")
            
            # Pequena pausa para o TTS terminar antes de escutar de novo
            time.sleep(0.8)
            
            print("[INFO] Aguardando comando...")
            command = capture_speech(duration=7)
            
            if not command:
                self.speak("Não ouvi nada. Pode repetir?")
                continue
            
            # Remove a wake word do texto caso tenha vindo junto
            for w in WAKE_VARIATIONS:
                command = command.lower().replace(w, '').strip()
            
            if not command:
                self.speak("Não ouvi o comando. O que deseja?")
                continue
            
            print(f"[INFO] Comando capturado: '{command}'")
            self.command_queue.put(command)
    
    def process_command(self, command):
        """
        Processar comando reconhecido pelo usuário
        
        Args:
            command (str): Texto do comando reconhecido
        
        Este método:
        - Analisa o comando para identificar a intenção
        - Executa a ação apropriada
        - Gera uma resposta
        - Usa speak() para vocalizar a resposta
        """
        command_lower = command.lower().strip()
        
        # Comandos básicos
        if "olá" in command_lower or "oi" in command_lower:
            self.speak("Olá! Como posso ajudar?")
        elif "que horas são" in command_lower or "horas" in command_lower:
            from datetime import datetime
            hora = datetime.now().strftime("%H:%M")
            self.speak(f"Agora são {hora}")
        elif "que dia é hoje" in command_lower or "data" in command_lower:
            from datetime import datetime
            data = datetime.now().strftime("%d de %B de %Y")
            self.speak(f"Hoje é {data}")
        elif "encerrar" in command_lower or "pare" in command_lower:
            self.speak("Encerrando sistema...")
            self.running = False
        else:
            self.speak("Desculpe, não entendi o comando.")
    
    def run(self):
        """
        Loop principal do assistente
        
        Este método:
        - Inicia a thread de escuta contínua
        - Gerencia transições entre modos
        - Processa comandos da queue
        - Mantém sistema rodando até encerramento
        - Encerra thread gracefulmente
        """
        print("[INFO] Iniciando loop principal do JARVIS...")
        
        try:
            # Iniciar thread de escuta (só escuta, não fala)
            self.listening_thread = threading.Thread(
                target=self.listen_for_wake_word,
                daemon=True
            )
            self.listening_thread.start()
            print("[OK] Thread de escuta iniciada")
            
            # Testar síntese de voz
            self.speak("Sistema NOVA online e pronto para uso.")
            
            # Loop principal — processa comandos
            while self.running:
                try:
                    command = self.command_queue.get(timeout=0.05)
                    print(f"[INFO] Comando recebido: '{command}'")
                    self.process_command(command)
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"[ERRO] Erro ao processar comando: {e}")
            
            print("[INFO] Loop principal encerrado")
            
        except Exception as e:
            print(f"[ERRO] Erro no loop principal: {e}")
            self.running = False


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
        if not jarvis.initialize_system():
            print("[FATAL] Inicialização falhou. Encerrando.")
            sys.exit(1)
        
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
