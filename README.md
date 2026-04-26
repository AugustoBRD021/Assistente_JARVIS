# JARVIS - Assistente Virtual Inteligente

## Visão Geral

JARVIS é um assistente virtual completo que combina software e hardware para criar uma interface inteligente entre humanos e máquinas. O sistema utiliza Python como núcleo principal de processamento e microcontroladores para interação física com o ambiente.

## Características Principais

### 🎯 Reconhecimento de Voz
- Captura de áudio através de microfone
- Processamento e interpretação de comandos em linguagem natural
- Respostas inteligentes com integração de IA (Claude)

### 🖥️ Automação de Software
- Execução de comandos no sistema operacional
- Abertura automática de programas
- Automação de tarefas repetitivas

### 🔗 Integração Hardware
- Controle de dispositivos eletrônicos (relés, motores, LEDs)
- Leitura de sensores diversos
- Comunicação via USB serial ou Wi-Fi

### 🧠 Inteligência Artificial
- Processamento de linguagem natural
- Tomada de decisão autônoma
- Aprendizado contínuo

## Arquitetura do Sistema

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Entrada de    │    │   Processamento │    │   Saída de      │
│     Voz         │───▶│    Python       │───▶│   Áudio/Visual  │
│   (Microfone)   │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  Inteligência   │
                       │  Artificial     │
                       │   (Claude)      │
                       └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  Comunicação    │
                       │ Serial/Wi-Fi    │
                       └─────────────────┘
                              │
                              ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Sensores      │    │  Microcontrola- │    │   Atuadores     │
│   (Entrada)     │◀───│     dor         │───▶│   (Saída)       │
│                 │    │   (ESP32/Arduino)│    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Componentes

### Software (Python)
- **Reconhecimento de Voz**: Bibliotecas como SpeechRecognition
- **Processamento de IA**: Integração com Claude API
- **Automação**: Bibliotecas de sistema operacional
- **Comunicação**: Protocolos serial e rede

### Hardware (C/C++)
- **Microcontrolador**: ESP32 ou Arduino
- **Sensores**: Diversos tipos conforme necessidade
- **Atuadores**: Relés, motores, LEDs, etc.
- **Comunicação**: USB serial ou Wi-Fi

## Fluxo de Funcionamento

1. **Captura**: Usuário emite comando por voz
2. **Processamento**: Python interpreta o áudio
3. **IA**: Sistema analisa a intenção do comando
4. **Decisão**: Define ação necessária
5. **Execução**: Envia instrução ao hardware
6. **Resposta**: Fornece feedback ao usuário

## Aplicações

### Doméstica
- Automação residencial
- Controle de iluminação
- Gerenciamento de climatização

### Profissional
- Automação de escritório
- Monitoramento industrial
- Assistência técnica

### Educacional
- Plataforma de aprendizado
- Projetos interdisciplinares
- Pesquisa acadêmica

## Tecnologias Utilizadas

### Software
- **Python**: Linguagem principal
- **anthropic**: Processamento de linguagem com Claude
- **SpeechRecognition**: Reconhecimento de voz
- **PySerial**: Comunicação serial
- **Socket**: Comunicação rede

### Hardware
- **ESP32**: Microcontrolador principal
- **Arduino**: Alternativa de baixo custo
- **Sensores**: Diversos tipos
- **Atuadores**: Componentes eletrônicos

## Requisitos

### Sistema
- Python 3.8+
- Microfone funcional
- Porta USB ou rede Wi-Fi

### Hardware
- ESP32 ou Arduino
- Sensores e atuadores específicos
- Fonte de alimentação

## Documentação

- [Arquitetura do Sistema](docs/arquitetura.md)
- [Guia de Instalação](docs/instalacao.md)
- [Componentes de Software](docs/software.md)
- [Componentes de Hardware](docs/hardware.md)
- [Protocolos de Comunicação](docs/comunicacao.md)

## Fluxo de Trabalho Git

### Branches Principais

- **main**: Branch principal estável (produção)
  - Contém código testado e funcional
  - PASSO 2 completo: inicialização do sistema
  - Sistema 100% funcional com Vosk e pyttsx3

- **feature/escuta-continua**: Branch de desenvolvimento
  - Desenvolvimento do PASSO 3 (escuta contínua)
  - Alterações experimentais não afetam o main
  - Quando pronto, será mergeado para main

### Como Trabalhar com Branches

#### Criar nova branch de desenvolvimento:
```bash
git checkout -b feature/nome-da-feature
```

#### Ver branch atual:
```bash
git branch --show-current
```

#### Listar todas as branches:
```bash
git branch
```

#### Trocar de branch:
```bash
git checkout nome-da-branch
```

#### Deletar branch:
```bash
git branch -d nome-da-branch
```

### Fluxo de Desenvolvimento

1. **Criar branch** a partir de main
2. **Implementar** novas funcionalidades
3. **Testar** completamente
4. **Commit** alterações
5. **Push** para GitHub
6. **Merge** para main (quando aprovado)

### Status Atual do Projeto

- ✅ **PASSO 1**: Estrutura básica do main.py
- ✅ **PASSO 2**: Inicialização completa do sistema (main)
- 🔄 **PASSO 3**: Escuta contínua (feature/escuta-continua - em desenvolvimento)

## Licença

Este projeto está sob licença MIT. Consulte o arquivo LICENSE para mais detalhes.

## Contribuição

Contribuições são bem-vindas! Por favor, leia o guia de contribuição antes de enviar pull requests.

## Contato

Para dúvidas ou sugestões, entre em contato através das issues do projeto.
