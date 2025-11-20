# 📐 Arquitetura

> **Detalhes técnicos da implementação do Real Selection**

---

## 📑 Índice

- [Visão Geral](#visão-geral)
- [Fluxo de Execução](#fluxo-de-execução)
- [Componentes Principais](#componentes-principais)
- [Threading e Concorrência](#threading-e-concorrência)
- [Pipeline de Áudio](#pipeline-de-Áudio)
- [Logging e Debugging](#logging-e-debugging)
- [Dependências](#dependências)

---

## 🎯 Visão Geral

O **Real Selection** utiliza uma arquitetura **producer-consumer** multi-threaded para minimizar latência entre geração e reprodução de áudio.

```
┌─────────────────┐
│  Usuário        │
│  (seleciona     │
│   texto)        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ wl-paste        │  ← Captura seleção primária (Wayland)
│ --primary       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Limpeza de      │  ← Remove quebras indesejadas, normaliza espaços
│ Texto           │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Producer        │  ← Thread 1: Gera chunks via Kokoro-82M
│ Thread          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Queue           │  ← Buffer de até 10 chunks (FIFO)
│ (maxsize=10)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Consumer        │  ← Thread 2: Reproduz chunks via PyAudio
│ Thread          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Alto-falantes   │  ← Saída de áudio
└─────────────────┘
```

---

## 🔄 Fluxo de Execução

### 1. **Captura de Seleção**

```python
# src/real_selection/main.py (função obter_selecao_primaria)
subprocess.check_output(["wl-paste", "--primary"], timeout=2)
```

- Usa `wl-clipboard` para acessar seleção primária do Wayland
- Timeout de 2s previne travamentos
- Retorna `None` em caso de erro, string vazia se nada selecionado

### 2. **Limpeza de Texto**

```python
# Regex para manter parágrafos mas juntar linhas
texto_limpo = re.sub(r'(?<!\n)\n(?!\n)', ' ', texto)
```

- **Problema**: PDFs e terminais inserem `\n` indesejados
- **Solução**: Substitui `\n` isolado por espaço, mantém `\n\n` (parágrafos)
- Remove espaços múltiplos

### 3. **Inicialização do Pipeline**

```python
pipeline = KPipeline(
    lang_code='p',              # Português BR
    repo_id='hexgrad/Kokoro-82M',
    device='cuda'               # GPU (fallback: CPU)
)
pipeline.load_voice('pf_dora')  # Pré-carrega voz
```

- Pipeline é **global** e reutilizado entre chamadas (evita recarregar modelo)
- Detecção automática de CUDA via `torch.cuda.is_available()`

### 4. **Threading**

```python
# Consumer inicia PRIMEIRO (evita perda de chunks iniciais)
consumer.start()
time.sleep(0.1)  # Garante stream pronto
producer.start()

# Aguarda ambas finalizarem
producer.join()
consumer.join()
```

---

## 🧩 Componentes Principais

### `main.py`

| Componente | Responsabilidade |
|------------|------------------|
| `configurar_logging()` | Setup do Loguru (console + arquivo) |
| `obter_selecao_primaria()` | Captura texto via wl-paste |
| `limpar_texto_para_tts()` | Normaliza texto para síntese |
| `inicializar_pipeline()` | Carrega modelo Kokoro |
| `processar_tts()` | Orquestra threads producer/consumer |
| `AudioProducerThread` | Thread de geração de áudio |
| `AudioConsumerThread` | Thread de reprodução de áudio |

### `tts_wrapper.sh`

| Responsabilidade |
|------------------|
| Executa `main.py` em background (não bloqueia terminal) |
| Previne múltiplas instâncias (lock file em `/tmp`) |
| Notificações visuais via `notify-send` |
| Filtra warnings do ALSA dos logs |
| Monitora processo e faz cleanup automático |

### `tts_kill.sh`

| Responsabilidade |
|------------------|
| Busca PID via lock file ou `pgrep` |
| Mata processo graciosamente (`SIGTERM`) |
| Força término se necessário (`SIGKILL` após 2s) |
| Remove lock file |

---

## 🧵 Threading e Concorrência

### Arquitetura Producer-Consumer

```python
# Queue thread-safe com limite de 10 chunks
audio_queue = queue.Queue(maxsize=10)
```

#### Producer Thread

```python
for result in pipeline(texto, voice='pf_dora', speed=1.0):
    if result.audio:
        chunk = result.audio.cpu().numpy().astype(np.float32)
        audio_queue.put(chunk)  # Bloqueia se fila cheia (backpressure)
        
audio_queue.put(None)  # Sinaliza fim
```

- Gera chunks via Kokoro (GPU/CPU)
- Converte `torch.Tensor` → `numpy.float32`
- Enfileira chunks conforme são gerados
- **Backpressure**: Se fila cheia (10 chunks), producer aguarda consumer consumir

#### Consumer Thread

```python
stream = pyaudio_instance.open(
    format=pyaudio.paFloat32,
    channels=1,
    rate=24000,
    output=True,
    output_device_index=9  # FIXME: hardcoded
)

while True:
    chunk = audio_queue.get()  # Bloqueia se fila vazia
    if chunk is None:
        break
    stream.write(chunk.tobytes())
```

- Abre stream PyAudio (24kHz, mono, float32)
- Desenfileira e reproduz chunks em loop
- **Bloqueia** se fila vazia (aguarda producer gerar)
- Termina ao receber `None`

### Por que Consumer Inicia Primeiro?

```python
consumer.start()
time.sleep(0.1)  # Delay estratégico
producer.start()
```

**Motivo**: Garante que stream de áudio esteja **pronto** antes do primeiro chunk ser gerado. Sem isso, chunks iniciais podem ser perdidos.

---

## 🎵 Pipeline de Áudio

### Kokoro-82M

```
Texto → Tokenização → Modelo Neural (82M params) → Mel Spectrogram → Vocoder → Áudio PCM
```

- **Entrada**: String UTF-8
- **Saída**: `torch.Tensor` de shape `(samples,)` a 24kHz
- **Formato**: Float32, mono, range [-1.0, 1.0]

### PyAudio / PortAudio

```python
# Configuração do stream
format=pyaudio.paFloat32  # 32-bit float
channels=1                # Mono
rate=24000                # 24kHz (taxa nativa do Kokoro)
frames_per_buffer=2048    # Tamanho do buffer interno
```

**Device Index (FIXME)**:
```python
output_device_index=9  # Hardcoded para ambiente de dev
```

> **🚧 TODO**: Tornar configurável ou usar device padrão do sistema.

---

## 📊 Logging e Debugging

### Loguru (dois níveis)

#### Console (INFO)
```python
logger.add(sys.stderr, level="INFO", colorize=True)
```

- Mensagens relevantes para usuário final
- Output limpo (sem stack traces excessivos)

#### Arquivo (DEBUG)
```python
logger.add(
    "logs/tts_debug.log",
    level="DEBUG",
    rotation="10 MB",
    retention=5,
    compression="zip"
)
```

- Tudo é registrado (troubleshooting)
- Rotação automática (10 MB por arquivo)
- Mantém últimos 5 arquivos compactados

### Exemplo de logs

```
[10:23:45] INFO     | Capturando seleção primária...
[10:23:45] DEBUG    | Executando wl-paste --primary
[10:23:45] DEBUG    | Texto capturado: 142 caracteres
[10:23:45] INFO     | Texto capturado: 142 caracteres
[10:23:45] INFO     | Limpando texto...
[10:23:45] DEBUG    | Original: 142 chars, 8 quebras
[10:23:45] DEBUG    | Limpo: 135 chars, 2 quebras
[10:23:46] INFO     | Pipeline pronto (device: cuda)
[10:23:46] DEBUG    | [Producer] Thread iniciada
[10:23:46] DEBUG    | [Consumer] Thread iniciada
[10:23:47] INFO     | Chunk 1 gerado (0.89s)
[10:23:47] DEBUG    | [Consumer] Tocando chunk 1 (0.89s)
...
```

---

## 📦 Dependências

### Core

| Biblioteca | Versão | Propósito |
|------------|--------|-----------|
| `kokoro` | ≥0.9.4 | TTS engine (modelo Kokoro-82M) |
| `pyaudio` | ≥0.2.13 | Interface Python para PortAudio |
| `torch` | *(via kokoro)* | Inferência do modelo neural |
| `numpy` | *(via torch)* | Manipulação de arrays de áudio |
| `loguru` | *(via kokoro)* | Sistema de logging |

### Sistema

| Ferramenta | Propósito |
|------------|-----------|
| `wl-clipboard` | Captura seleção primária do Wayland |
| `portaudio` | Backend de áudio multiplataforma |
| `CUDA` *(opcional)* | Aceleração GPU |
| `notify-send` | Notificações visuais (Hyprland) |

### Instalação

```bash
# Arch Linux
sudo pacman -S python python-pip portaudio wl-clipboard cuda

# Python deps
uv sync  # ou pip install -e .
```

---

## ⚡ Performance

### Latência típica

| Etapa | Tempo |
|-------|-------|
| Captura de seleção | ~10-50 ms |
| Limpeza de texto | ~1-5 ms |
| Primeiro chunk (GPU) | ~100-300 ms |
| Primeiro chunk (CPU) | ~500-1500 ms |
| Chunks subsequentes | ~50-200 ms |

**Latência total (GPU)**: ~150-400 ms do SUPER+T até primeiro áudio  
**Latência total (CPU)**: ~600-2000 ms

### Uso de memória

- **Pipeline Kokoro**: ~500 MB RAM
- **Queue (10 chunks)**: ~10-20 MB
- **PyAudio buffers**: ~1 MB
- **Total**: ~550-600 MB

### GPU vs CPU

```
┌──────────────┬──────────┬──────────┐
│ Texto        │ GPU      │ CPU      │
├──────────────┼──────────┼──────────┤
│ 100 chars    │ 0.3s     │ 1.2s     │
│ 500 chars    │ 1.2s     │ 5.8s     │
│ 1000 chars   │ 2.5s     │ 12.3s    │
└──────────────┴──────────┴──────────┘
```

> **💡 Dica**: Use GPU sempre que possível para latência mínima.

---

## 🔐 Segurança e Privacidade

- ✅ **Processamento local**: Nenhum dado enviado para servidores externos
- ✅ **Sem persistência**: Texto não é salvo em disco (exceto logs de debug)
- ✅ **Lock files**: Previne race conditions entre múltiplas instâncias
- ⚠️ **Logs**: Contêm texto processado (verifique sensibilidade antes de compartilhar)

---

## 🐛 Debugging

### Problema: Sem áudio

**Checklist**:
1. Verifique device de áudio: `python -c "import pyaudio; p = pyaudio.PyAudio(); [print(i, p.get_device_info_by_index(i)['name']) for i in range(p.get_device_count())]"`
2. Ajuste `output_device_index` em `main.py`
3. Teste com `speaker-test -c 1` (verifica ALSA/PulseAudio)

### Problema: Latência alta

**Causas**:
- CPU em vez de GPU
- Device de áudio com buffer grande
- Sistema sobrecarregado

**Soluções**:
- Instale CUDA
- Reduza `frames_per_buffer` (cuidado com audio glitches)
- Feche aplicativos pesados

### Problema: Chunks perdidos

**Sintomas**: Áudio picotado, logs mostram chunks gerados ≠ chunks tocados

**Causa**: Consumer não consegue acompanhar producer

**Solução**: Aumente `maxsize` da queue (linha ~380)

---

## 🚀 Melhorias Futuras

- [ ] **Configuração via CLI/env**: Remover hardcoded `output_device_index`
- [ ] **Suporte a múltiplas vozes**: Seleção dinâmica via atalho
- [ ] **Cache de pipeline**: Reutilizar entre processos (atualmente só em memória)
- [ ] **API REST**: Expor TTS via HTTP (uso remoto)
- [ ] **Fallback a outros TTS**: Se Kokoro falhar (e.g., Piper, Coqui)

---

<div align="center">

**[⬆ Voltar ao README](../README.md)** | **[🎤 Vozes](VOZES.md)** | **[⚙️ Configuração](CONFIGURACAO.md)**

---

**Real Selection** — Copyright (C) 2025 Renato Barros  
Licenciado sob GNU GPL v3.0+

</div>
