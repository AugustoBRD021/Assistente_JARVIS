#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NOVA - Assistente Virtual Inteligente
Ponto de entrada principal do sistema

Este arquivo contém a classe principal do assistente NOVA, responsável por:
- Inicializar todos os componentes do sistema
- Gerenciar os modos de operação (passivo, ativo, processamento)
- Controlar o loop principal do assistente
- Coordenar reconhecimento de voz e síntese de fala
"""

# Importações de bibliotecas padrão Python
import sys      # Para manipulação de argumentos de linha de comando e saída do sistema
import time     # Para controle de tempo e delays
import json     # Para decodificar os resultados do reconhecedor Vosk
import re       # Para casar a wake word como palavra inteira (evita falso positivo em "novamente")
import unicodedata  # Para normalizar acentos ao comparar comandos reconhecidos
import threading  # Para operações concorrentes (escuta contínua sem bloquear)
import queue    # Para fila de comandos entre threads
import asyncio  # Para operações assíncronas (edge-tts)
import subprocess  # Para executar comandos do sistema (ffmpeg)
import sounddevice as sd  # Para verificar o microfone
import edge_tts  # Para síntese de voz neural da Microsoft
import tempfile  # Para arquivos temporários
import os  # Para manipulação de arquivos
import shutil  # Para localizar o executável do ffmpeg no PATH
from datetime import datetime  # Para informar a data/hora atual nas respostas locais

# Importação de nossos módulos personalizados
from test_audio import VoskRecognizer  # Importa nossa classe de reconhecimento de voz já testada

# Nomes dos meses em pt-BR, independente da locale configurada no sistema
# (strftime("%B") cai para inglês quando a locale pt-BR não está instalada)
MESES_PT_BR = {
    1: 'janeiro', 2: 'fevereiro', 3: 'março', 4: 'abril',
    5: 'maio', 6: 'junho', 7: 'julho', 8: 'agosto',
    9: 'setembro', 10: 'outubro', 11: 'novembro', 12: 'dezembro',
}


def _padrao_palavras(*frases):
    """Compila um regex que casa qualquer uma das frases como palavra(s) inteira(s)"""
    return re.compile(r'\b(?:' + '|'.join(re.escape(f) for f in frases) + r')\b', re.IGNORECASE)


def remover_acentos(texto):
    """Remove acentos para tornar a comparação de comandos resistente a variações do Vosk"""
    return ''.join(c for c in unicodedata.normalize('NFKD', texto) if not unicodedata.combining(c))


# Padrões de reconhecimento de intenção usados em process_command (sem acentos,
# pois o texto reconhecido é normalizado antes de comparar)
PADRAO_SAUDACAO = _padrao_palavras('ola', 'oi', 'e ai', 'bom dia', 'boa tarde', 'boa noite')
PADRAO_HORAS = _padrao_palavras('que horas sao', 'que horas', 'horas', 'horario', 'hora atual')
PADRAO_DATA = _padrao_palavras('que dia e hoje', 'que dia', 'data de hoje', 'dia de hoje', 'data', 'dia', 'hoje')
PADRAO_ENCERRAR = _padrao_palavras('encerrar', 'pare', 'parar', 'desligar', 'sair', 'tchau')


class NovaAssistant:
    """
    Classe principal do assistente NOVA
    
    Responsabilidades:
    - Gerenciar o estado geral do sistema
    - Controlar os modos de operação
    - Coordenar todos os componentes (reconhecimento, síntese, hardware)
    - Implementar o loop principal do assistente
    """
    
    def __init__(self):
        """
        Construtor da classe NovaAssistant
        
        Inicializa os atributos básicos do sistema:
        - running: Controla se o sistema está ativo ou deve encerrar
        - wake_word: Palavra que ativa o assistente ("nova")
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
        self.speaking = threading.Event()   # Sinaliza quando a NOVA está falando (evita ouvir a si mesma)
        
        # Mensagens de inicialização para feedback ao usuário
        print("NOVA - Assistente Virtual Inteligente")
        print("Inicializando sistema...")
    
    def initialize_system(self):
        """
        Inicializar todos os componentes do sistema
        
        Implementação completa:
        - Carregar o modelo Vosk para reconhecimento de voz
        - Configurar o sintetizador de voz (edge-tts)
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
            
            # Selecionar o dispositivo de entrada padrão do sistema, se disponível;
            # caso contrário, cai para o primeiro dispositivo de entrada encontrado
            try:
                default_input_id = sd.default.device[0]
            except Exception:
                default_input_id = -1

            default_device = next(
                (d for d in self.audio_devices if d['id'] == default_input_id), None
            )
            selected = default_device or self.audio_devices[0]
            self.selected_device = selected['id']
            print(f"[OK] Dispositivo selecionado: {selected['name']}")
            
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
            print("      pip install vosk edge-tts sounddevice numpy")
            print("[INFO] Verifique se o ffmpeg está instalado e disponível no PATH")
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

        # Sinaliza que está falando para a thread de escuta pausar a captura
        # e não interpretar a própria voz da NOVA como um comando do usuário
        self.speaking.set()

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
            
            # Converte MP3 para WAV usando ffmpeg (localizado dinamicamente no PATH)
            wav_path = tmp_path.replace(".mp3", ".wav")
            ffmpeg_path = shutil.which("ffmpeg")

            def fallback_playback(motivo):
                # Player padrão do Windows: startfile() é assíncrono, não há como saber
                # quando termina de tocar, então não apagamos o mp3 temporário aqui
                # (evita apagar o arquivo enquanto ainda está sendo reproduzido).
                print(f"[INFO] {motivo}, usando player padrão")
                os.startfile(tmp_path)

            if ffmpeg_path:
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
                    fallback_playback("ffmpeg falhou")
            else:
                fallback_playback("ffmpeg não encontrado no PATH")
            
        except Exception as e:
            print(f"[ERRO] Falha na síntese de voz: {e}")
        finally:
            self.speaking.clear()

    def listen_for_wake_word(self):
        """
        Escuta continuamente pela wake word usando um stream de áudio contínuo

        Ao contrário de gravar em blocos fixos com pausas entre eles (o que corta
        palavras faladas bem na borda de um bloco), aqui o microfone fica sempre
        aberto e o áudio é processado em tempo real pelo Vosk. A wake word e o
        comando seguinte são reconhecidos como frases completas assim que o Vosk
        detecta uma pausa na fala (fim de utterance).

        Funciona em loop contínuo enquanto self.running = True
        """
        print("[INFO] Iniciando escuta contínua pela wake word...")

        # Variações fonéticas da wake word
        WAKE_VARIATIONS = ['nova', 'nóva', 'nôva', 'nôba', 'nóba']
        # \b garante casar a palavra inteira (evita disparo falso em "novamente", "renovar" etc.)
        WAKE_PATTERN = re.compile(
            r'\b(?:' + '|'.join(re.escape(w) for w in WAKE_VARIATIONS) + r')\b',
            re.IGNORECASE
        )
        sample_rate = 16000
        # Bloco pequeno (125ms) em vez dos 500ms originais: medido em teste offline que isso
        # não piora a precisão do Vosk, mas deixa a extensão do prazo de comando (abaixo)
        # reagir bem mais rápido à fala em andamento
        TAMANHO_BLOCO = 2000
        TIMEOUT_COMANDO = 8  # segundos de silêncio tolerados antes de desistir do comando

        # Eventos vindos do callback de áudio (thread separada, gerenciada pelo PortAudio):
        # ('final', texto) quando o Vosk fecha uma frase, ('parcial', None) enquanto ainda
        # há fala em andamento (usado só para estender o prazo de espera do comando)
        eventos_audio = queue.Queue()

        def callback(indata, frames, time_info, status):
            if self.speaking.is_set():
                return  # não alimenta o reconhecedor com a própria voz da NOVA
            try:
                raw = bytes(indata)
                if self.vosk_recognizer.recognizer.AcceptWaveform(raw):
                    result = json.loads(self.vosk_recognizer.recognizer.Result())
                    texto = result.get('text', '').strip()
                    if texto:
                        eventos_audio.put(('final', texto))
                else:
                    parcial = json.loads(self.vosk_recognizer.recognizer.PartialResult())
                    if parcial.get('partial', '').strip():
                        eventos_audio.put(('parcial', None))
            except Exception as e:
                print(f"[ERRO] Falha ao processar áudio: {e}")

        aguardando_comando = False
        prazo_comando = 0.0

        # Loop externo: se o stream de áudio cair (ex: microfone desconectado),
        # tenta reabrir em vez de encerrar a escuta permanentemente
        while self.running:
            try:
                with sd.RawInputStream(samplerate=sample_rate, blocksize=TAMANHO_BLOCO, dtype='int16',
                                        channels=1, device=self.selected_device, callback=callback):
                    while self.running:
                        if aguardando_comando and time.time() > prazo_comando:
                            aguardando_comando = False
                            self.speak("Não ouvi nada. Pode repetir?")
                            continue

                        try:
                            tipo, texto = eventos_audio.get(timeout=0.1)
                        except queue.Empty:
                            continue

                        if tipo == 'parcial':
                            # Ainda há fala em andamento: estende o prazo em vez de
                            # deixar o timeout estourar no meio da frase do usuário
                            if aguardando_comando:
                                prazo_comando = time.time() + TIMEOUT_COMANDO
                            continue

                        print(f"[DEBUG] Ouvido: '{texto}'")

                        if not aguardando_comando:
                            if not WAKE_PATTERN.search(texto):
                                continue  # Não foi a wake word, ignora

                            print("[INFO] Wake word detectada!")
                            self.speak("Sim?")
                            aguardando_comando = True
                            prazo_comando = time.time() + TIMEOUT_COMANDO
                            print("[INFO] Aguardando comando...")
                        else:
                            # Remove a wake word do texto caso tenha vindo junto (só palavra inteira)
                            comando = WAKE_PATTERN.sub('', texto.lower()).strip()
                            aguardando_comando = False

                            if not comando:
                                self.speak("Não ouvi o comando. O que deseja?")
                                continue

                            print(f"[INFO] Comando capturado: '{comando}'")
                            self.command_queue.put(comando)
            except Exception as e:
                print(f"[ERRO] Falha na escuta contínua: {e}")
                time.sleep(1)
    
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
        command_lower = remover_acentos(command.lower().strip())

        if PADRAO_SAUDACAO.search(command_lower):
            self.speak("Olá! Como posso ajudar?")
        elif PADRAO_HORAS.search(command_lower):
            hora = datetime.now().strftime("%H:%M")
            self.speak(f"Agora são {hora}")
        elif PADRAO_DATA.search(command_lower):
            agora = datetime.now()
            mes = MESES_PT_BR[agora.month]
            self.speak(f"Hoje é {agora.day} de {mes} de {agora.year}")
        elif PADRAO_ENCERRAR.search(command_lower):
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
        print("[INFO] Iniciando loop principal do NOVA...")
        
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
    1. Cria uma instância do NovaAssistant
    2. Inicializa o sistema
    3. Inicia o loop principal
    4. Trata interrupções do usuário (Ctrl+C)
    5. Trata erros fatais de forma segura
    
    Returns:
        None: O programa encerra com código de saída apropriado
    """
    try:
        # Criar instância do assistente
        nova = NovaAssistant()
        
        # Inicializar componentes do sistema
        if not nova.initialize_system():
            print("[FATAL] Inicialização falhou. Encerrando.")
            sys.exit(1)
        
        # Iniciar loop principal do assistente
        nova.run()
        
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
