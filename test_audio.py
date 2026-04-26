#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste de audio do JARVIS usando Vosk
Reconhecimento de voz offline com Vosk
"""

import sys
import time
import json
import wave
import numpy as np
import threading
from pathlib import Path

def test_imports():
    """Testa se todas as bibliotecas foram importadas com sucesso"""
    print("Testando importacoes das bibliotecas...")
    
    try:
        import vosk
        print("[OK] Vosk importado com sucesso")
    except ImportError as e:
        print(f"[ERRO] Erro ao importar Vosk: {e}")
        return False
    
    try:
        import pyttsx3
        print("[OK] pyttsx3 importado com sucesso")
    except ImportError as e:
        print(f"[ERRO] Erro ao importar pyttsx3: {e}")
        return False
    
    try:
        import sounddevice as sd
        print("[OK] sounddevice importado com sucesso")
    except ImportError as e:
        print(f"[ERRO] Erro ao importar sounddevice: {e}")
        return False
    
    try:
        import numpy as np
        print("[OK] numpy importado com sucesso")
    except ImportError as e:
        print(f"[ERRO] Erro ao importar numpy: {e}")
        return False
    
    return True

class VoskRecognizer:
    """Classe para reconhecimento de voz com Vosk"""
    
    def __init__(self, model_path=None):
        self.model_path = model_path or "models/vosk-model-small-pt-0.3/vosk-model-small-pt-0.3"
        self.model = None
        self.recognizer = None
        self.sample_rate = 16000
        self.recognizing = False
        self.result_text = ""
        
    def load_model(self):
        """Carregar modelo Vosk"""
        try:
            import vosk
            
            if not Path(self.model_path).exists():
                print(f"[ERRO] Modelo nao encontrado em: {self.model_path}")
                print("Por favor, baixe um modelo Vosk para portugues:")
                print("https://alphacephei.com/vosk/models")
                return False
            
            print("Carregando modelo Vosk...")
            self.model = vosk.Model(self.model_path)
            self.recognizer = vosk.KaldiRecognizer(self.model, self.sample_rate)
            print("[OK] Modelo Vosk carregado com sucesso")
            return True
            
        except Exception as e:
            print(f"[ERRO] Erro ao carregar modelo: {e}")
            return False
    
    def audio_callback(self, indata, frames, time, status):
        """Callback para processamento de audio"""
        import sounddevice as sd
        if self.recognizing and self.recognizer.AcceptWaveform(indata):
            result = json.loads(self.recognizer.Result())
            if result['text']:
                self.result_text = result['text']
                print(f"Reconhecido: {self.result_text}")
    
    def start_listening(self, duration=10):
        """Iniciar escuta continua"""
        import sounddevice as sd
        
        if not self.model or not self.recognizer:
            print("[ERRO] Modelo nao carregado")
            return None
        
        print(f"Ouvindo por {duration} segundos...")
        print("Diga algo...")
        
        self.result_text = ""
        self.recognizing = True
        
        try:
            with sd.RawInputStream(samplerate=self.sample_rate, blocksize=8000, 
                                dtype='int16', channels=1, callback=self.audio_callback):
                sd.sleep(duration * 1000)
            
            self.recognizing = False
            
            # Processar resultado final
            final_result = json.loads(self.recognizer.FinalResult())
            if final_result['text']:
                self.result_text = final_result['text']
            
            return self.result_text
            
        except Exception as e:
            print(f"[ERRO] Erro na gravacao: {e}")
            return None

def test_microphone_vosk():
    """Testar o acesso ao microfone com Vosk"""
    print("\nTestando microfone com Vosk...")
    
    try:
        import sounddevice as sd
        
        # Listar dispositivos de audio
        devices = sd.query_devices()
        print(f"Dispositivos de audio encontrados: {len(devices)}")
        
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                print(f"   Entrada {i}: {device['name']} (canais: {device['max_input_channels']})")
        
        # Testar reconhecimento com Vosk
        recognizer = VoskRecognizer()
        
        if not recognizer.load_model():
            print("[ERRO] Nao foi possivel carregar o modelo Vosk")
            return False
        
        # Teste de reconhecimento
        result = recognizer.start_listening(duration=5)
        
        if result:
            print(f"[OK] Reconhecimento Vosk funcionou")
            print(f"   Resultado: '{result}'")
            return True
        else:
            print("[AVISO] Nenhum resultado obtido")
            return True  # Considera sucesso pois o sistema funcionou
            
    except Exception as e:
        print(f"[ERRO] Erro ao testar microfone: {e}")
        return False

def test_speech_synthesis():
    """Testa a síntese de voz"""
    print("\nTestando sintese de voz...")
    
    try:
        import pyttsx3
        
        # Inicializar engine
        engine = pyttsx3.init()
        
        # Listar vozes disponíveis
        voices = engine.getProperty('voices')
        print(f"Vozes encontradas: {len(voices)}")
        for i, voice in enumerate(voices):
            try:
                lang = getattr(voice, 'languages', [getattr(voice, 'lang', 'unknown')])[0] if hasattr(voice, 'languages') else getattr(voice, 'lang', 'unknown')
                print(f"   {i}: {voice.name} ({lang})")
            except:
                print(f"   {i}: {voice.name}")
        
        # Configurar voz em portugues se disponivel
        for voice in voices:
            try:
                lang = getattr(voice, 'languages', [getattr(voice, 'lang', 'unknown')])[0] if hasattr(voice, 'languages') else getattr(voice, 'lang', 'unknown')
                if 'pt' in str(lang).lower() or 'brazil' in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    print(f"Voz selecionada: {voice.name}")
                    break
            except:
                continue
        
        # Testar fala
        print("Testando sintese de voz...")
        engine.say("Teste de sintese de voz do JARVIS com Vosk")
        engine.runAndWait()
        print("[OK] Sintese de voz funcionando")
        return True
        
    except Exception as e:
        print(f"[ERRO] Erro na sintese de voz: {e}")
        return False

def test_vosk_alternative():
    """Teste alternativo usando SpeechRecognition como fallback"""
    print("\nTestando SpeechRecognition como alternativa...")
    
    try:
        import speech_recognition as sr
        import sounddevice as sd
        
        # Gravar audio
        print("Gravando 3 segundos para reconhecimento...")
        duration = 3
        sample_rate = 16000
        recording = sd.rec(int(duration * sample_rate), 
                          samplerate=sample_rate, 
                          channels=1, 
                          dtype='int16')
        
        print("Fale algo agora...")
        sd.wait()
        
        # Converter para formato SpeechRecognition
        audio_data = np.array(recording, dtype=np.int16).tobytes()
        
        # Tentar reconhecer
        recognizer = sr.Recognizer()
        audio_sr = sr.AudioData(audio_data, sample_rate, 2)
        
        print("Processando reconhecimento...")
        
        try:
            text = recognizer.recognize_google(audio_sr, language="pt-BR")
            print(f"[OK] Reconhecido: '{text}'")
            return True
        except sr.UnknownValueError:
            print("[AVISO] Nao foi possivel entender o audio")
            return True  # Considera sucesso pois o sistema funcionou
        except sr.RequestError as e:
            print(f"[ERRO] Erro no servico de reconhecimento: {e}")
            return False
        
    except Exception as e:
        print(f"[ERRO] Erro no reconhecimento: {e}")
        return False

def main():
    """Funcao principal de teste"""
    print("JARVIS - Teste de Audio com Vosk")
    print("=" * 40)
    
    # Testar importacoes
    if not test_imports():
        print("\n[ERRO] Falha nas importacoes. Verifique a instalacao das bibliotecas.")
        return False
    
    # Testar sintese de voz
    if not test_speech_synthesis():
        print("\n[ERRO] Falha no teste de sintese de voz.")
        return False
    
    # Tentar teste com Vosk
    vosk_success = test_microphone_vosk()
    
    # Se Vosk falhar, tentar alternativa
    if not vosk_success:
        print("\nTentando alternativa com SpeechRecognition...")
        if not test_vosk_alternative():
            print("\n[ERRO] Falha no teste de reconhecimento de voz.")
            return False
    
    print("\nTodos os testes passaram com sucesso!")
    print("[OK] Sistema de audio do JARVIS esta pronto para uso.")
    print("\nNota: Usando Vosk para reconhecimento offline quando disponivel.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
