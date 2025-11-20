# TTS de Seleção Primária - Kokoro Streaming

Script que lê texto da seleção primária do Wayland e realiza síntese de voz em português do Brasil com streaming em tempo real.

## ✨ Características

- 🎯 **Captura automática** da seleção primária (texto selecionado)
- 🧹 **Limpeza inteligente** de texto (remove quebras de PDFs)
- 🇧🇷 **Português do Brasil** com voz natural (pf_dora)
- 🚀 **GPU acelerada** (CUDA) para inferência rápida
- ⚡ **Streaming real** com latência mínima (~300ms até primeiro som)
- 📊 **Logging dual** (INFO no console, DEBUG em arquivo)
- 🔧 **Robusto** com tratamento de erros e cleanup adequado

## 📋 Requisitos

### Sistema
- **OS**: Arch Linux (ou qualquer distribuição com Wayland)
- **Compositor**: Hyprland (ou qualquer compositor Wayland)
- **GPU**: NVIDIA com suporte CUDA (opcional, funciona em CPU)

### Pacotes do Sistema
```bash
sudo pacman -S wl-clipboard espeak-ng portaudio
```

### Dependências Python
```bash
# Dentro do virtualenv do projeto
uv pip install pyaudio loguru
# kokoro, torch, etc. já devem estar instalados
```

## 🚀 Uso Básico

### 1. Selecione um texto

Em **qualquer aplicativo** (browser, PDF, terminal, editor), selecione o texto que deseja ouvir.

**NÃO** use Ctrl+C - apenas selecione com o mouse!

### 2. Execute o script

```bash
.venv/bin/python examples/ler_selecao_tts.py
```

### 3. Ouça o áudio

O áudio começará a tocar automaticamente em alguns segundos.

## 📖 Exemplos

### Exemplo 1: Ler artigo do browser
1. Abra um artigo no navegador
2. Selecione um parágrafo
3. Execute: `.venv/bin/python examples/ler_selecao_tts.py`
4. O parágrafo será lido em voz alta

### Exemplo 2: Ler PDF
1. Abra um PDF
2. Selecione várias páginas de texto
3. Execute o script
4. O texto será limpo automaticamente (quebras de linha removidas) e lido

### Exemplo 3: Ler terminal
1. Selecione saída de um comando
2. Execute o script
3. O texto será lido

## 🔧 Configuração Avançada

### Alterar voz

Edite o arquivo `ler_selecao_tts.py` e modifique:

```python
# Linha ~362
producer = AudioProducerThread(
    ...
    voz='pf_dora',  # ← Altere aqui
    ...
)
```

Vozes disponíveis em português:
- `pf_dora`
- `pm_marcos`
- Veja lista completa em: https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md

### Alterar velocidade

```python
# Linha ~363
producer = AudioProducerThread(
    ...
    speed=1.0,  # ← 1.0 = normal, 0.8 = mais lento, 1.2 = mais rápido
    ...
)
```

### Desabilitar GPU (forçar CPU)

```python
# Linha ~324
pipeline = KPipeline(
    lang_code='p',
    repo_id='hexgrad/Kokoro-82M',
    device='cpu'  # ← Altere de 'cuda' para 'cpu'
)
```

## 📊 Logging

### Console (INFO)
Mensagens importantes são exibidas no console durante execução:
```
[12:34:56] INFO     | Capturando seleção primária...
[12:34:56] INFO     | Texto capturado: 139 caracteres
[12:34:57] INFO     | Pipeline pronto (device: cuda)
[12:34:58] INFO     | Chunk 1 gerado (8.07s)
[12:35:06] INFO     | Concluído com sucesso!
```

### Arquivo (DEBUG)
Log completo salvo em `logs/tts_debug.log`:
```
2025-11-20 12:34:56.123 | DEBUG | __main__:95 | Executando wl-paste --primary
2025-11-20 12:34:56.456 | DEBUG | __main__:206 | [Producer] Chunk 1: 193800 samples (8.07s)
...
```

- **Rotação**: 10 MB por arquivo
- **Retenção**: últimos 5 arquivos (comprimidos em .zip)

## 🐛 Troubleshooting

### Erro: "wl-clipboard não está instalado"

**Solução**:
```bash
sudo pacman -S wl-clipboard
```

### Erro: "CUDA não disponível"

**Comportamento**: Script funciona em CPU (mais lento)

**Para habilitar CUDA**:
1. Instale drivers NVIDIA
2. Instale CUDA Toolkit
3. Verifique: `nvidia-smi`

### Erro: "PyAudio não instalado"

**Solução**:
```bash
uv pip install pyaudio
```

Se falhar, pode precisar de portaudio:
```bash
sudo pacman -S portaudio
uv pip install pyaudio
```

### Aviso: "ALSA lib pcm.c:..."

**Comportamento**: Avisos podem aparecer mas são normais

**Causa**: Dispositivos de áudio virtuais que não existem no sistema

**Solução**: Ignore os avisos ou redirecione stderr:
```bash
.venv/bin/python examples/ler_selecao_tts.py 2>&1 | grep -v "^ALSA"
```

### Problema: Nenhum áudio toca

**Diagnóstico**:
1. Verifique dispositivos: `.venv/bin/python examples/test_04_pyaudio_stream.py`
2. Teste tom puro primeiro
3. Verifique volume do sistema
4. Verifique se PipeWire/PulseAudio está rodando

### Problema: Áudio picotado/cortado

**Causas possíveis**:
- CPU/GPU sobrecarregada
- Buffer PyAudio muito pequeno

**Solução**: Aumente buffer em `ler_selecao_tts.py`:
```python
# Linha ~254
stream = self.pyaudio_instance.open(
    ...
    frames_per_buffer=4096  # ← Aumente de 2048 para 4096
)
```

### Problema: Script trava/não termina

**Diagnóstico**:
1. Verifique logs: `tail -f logs/tts_debug.log`
2. Interrompa com Ctrl+C (cleanup automático)
3. Verifique threads: `ps aux | grep python`

## 🧪 Testes

### Validar ambiente
```bash
.venv/bin/python examples/test_01_dependencias.py
```

### Testar componentes individuais
```bash
# Seleção primária
.venv/bin/python examples/test_02_selecao.py

# Pipeline + GPU
.venv/bin/python examples/test_03_pipeline_gpu.py

# PyAudio
.venv/bin/python examples/test_04_pyaudio_stream.py

# Threading
.venv/bin/python examples/test_05_threading.py

# Casos extremos
.venv/bin/python examples/test_07_edge_cases.py
```

## ⚙️ Integração com Waybar (Futuro)

O script foi projetado para fácil integração com Waybar:

```json
{
    "custom/tts": {
        "format": "🔊",
        "on-click": "~/.aur/kokoro/.venv/bin/python ~/.aur/kokoro/examples/ler_selecao_tts.py",
        "tooltip": "Ler seleção primária"
    }
}
```

## 📈 Performance

### Hardware de Referência
- **CPU**: Ryzen 7 4800H (8C/16T)
- **RAM**: 32GB DDR4
- **GPU**: GTX 1650 (4GB VRAM)

### Métricas Observadas
- **Inicialização**: ~1.5s (primeira vez), ~0ms (reutilizando pipeline)
- **Latência até primeiro som**: ~300-500ms
- **RTF (Real-Time Factor)**: 0.097 (10.3x mais rápido que tempo real)
- **Uso de VRAM**: ~328 MB
- **Uso de RAM**: ~200-300 MB

### Comparação CPU vs GPU

| Métrica | GPU (CUDA) | CPU |
|---------|------------|-----|
| Inicialização | 1.5s | 2-3s |
| RTF (6s de áudio) | 0.097 | 0.4-0.6 |
| Tempo de geração | 597ms | 2-3s |
| Uso de memória | 328MB VRAM + 200MB RAM | 500MB RAM |

## 🔐 Segurança

- ✅ Script NÃO salva áudio em disco (streaming direto)
- ✅ Logs NÃO contêm texto capturado completo (apenas primeiros 100 chars)
- ✅ Seleção primária é volátil (desaparece ao selecionar outro texto)

## 📝 Licença

Este script segue a mesma licença do projeto Kokoro (Apache 2.0).

## 👥 Créditos

- **Kokoro-82M**: [hexgrad](https://huggingface.co/hexgrad/Kokoro-82M)

## 🆘 Suporte

Para problemas ou dúvidas:
1. Verifique os logs: `logs/tts_debug.log`
2. Execute testes de diagnóstico (seção Testes acima)
3. Abra issue no repositório do Kokoro

---

**Versão**: 1.0.0
**Última atualização**: 2025-11-20
