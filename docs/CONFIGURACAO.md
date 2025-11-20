# ⚙️ Configuração

> **Guia completo de instalação, configuração e troubleshooting do Real Selection**

---

## 📑 Índice

- [Requisitos do Sistema](#requisitos-do-sistema)
- [Instalação Passo a Passo](#instalação-passo-a-passo)
- [Configuração do Hyprland](#configuração-do-hyprland)
- [Configuração de Áudio](#configuração-de-Áudio)
- [Troubleshooting](#troubleshooting)
- [Desinstalação](#desinstalação)

---

## 💻 Requisitos do Sistema

### Sistema Operacional

| Item | Requisito |
|------|-----------|
| **SO** | Linux com Wayland compositor |
| **Testado em** | Arch Linux + Hyprland |
| **Compatível com** | Sway, KDE Wayland, GNOME Wayland |
| **Não suportado** | X11 (use `xclip` em vez de `wl-clipboard`) |

### Hardware

| Componente | Mínimo | Recomendado |
|------------|--------|-------------|
| **CPU** | 2 cores @ 2.0 GHz | 4+ cores @ 3.0 GHz |
| **RAM** | 2 GB livre | 4+ GB livre |
| **GPU** | Nenhuma (CPU fallback) | NVIDIA com CUDA |
| **Áudio** | Qualquer device ALSA/PulseAudio | - |

### Software

| Dependência | Versão | Instalação (Arch) |
|-------------|--------|-------------------|
| **Python** | 3.10 - 3.13 | `sudo pacman -S python` |
| **wl-clipboard** | Qualquer | `sudo pacman -S wl-clipboard` |
| **PortAudio** | Qualquer | `sudo pacman -S portaudio` |
| **CUDA** *(opcional)* | 11.8+ | `sudo pacman -S cuda` |
| **notify-send** | Qualquer | `sudo pacman -S libnotify` |

---

## 📦 Instalação Passo a Passo

### 1. Instalar dependências do sistema

#### Arch Linux

```bash
sudo pacman -S python python-pip portaudio wl-clipboard libnotify

# Opcional: CUDA para aceleração GPU
sudo pacman -S cuda
```

#### Debian/Ubuntu

```bash
sudo apt update
sudo apt install python3 python3-pip portaudio19-dev wl-clipboard libnotify-bin

# Opcional: CUDA (veja https://developer.nvidia.com/cuda-downloads)
```

#### Fedora

```bash
sudo dnf install python3 python3-pip portaudio-devel wl-clipboard libnotify

# Opcional: CUDA
sudo dnf install cuda
```

### 2. Clonar repositório

```bash
cd ~/projetos  # ou diretório de sua preferência
git clone https://github.com/renatobarros-ai/real_selection.git
cd real_selection
```

### 3. Instalar dependências Python

#### Opção A: uv (recomendado)

```bash
# Instalar uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Instalar dependências
uv sync
```

#### Opção B: pip

```bash
# Criar virtual environment (recomendado)
python -m venv .venv
source .venv/bin/activate

# Instalar
pip install -e .
```

### 4. Verificar instalação

```bash
# Testar captura de seleção
echo "teste" | wl-copy --primary
wl-paste --primary  # Deve mostrar "teste"

# Testar Python script
uv run python src/real_selection/main.py
# Ou: python src/real_selection/main.py (se usou pip)
```

---

## 🎨 Configuração do Hyprland

### 1. Criar scripts executáveis

Torne os scripts executáveis:

```bash
chmod +x scripts/tts_wrapper.sh scripts/tts_kill.sh
```

### 2. Adicionar binds ao Hyprland

Edite `~/.config/hypr/hyprland.conf`:

```conf
# ========================================
# Real Selection TTS - Atalhos
# ========================================

# Iniciar TTS (lê seleção primária)
bind = SUPER, T, exec, ~/projetos/real_selection/scripts/tts_wrapper.sh

# Interromper TTS
bind = SUPER SHIFT, T, exec, ~/projetos/real_selection/scripts/tts_kill.sh
```

> **💡 Dica**: Ajuste `~/projetos/real_selection` para o caminho onde você clonou o repositório.

### 3. Recarregar configuração

```bash
# Método 1: Recarregar Hyprland
hyprctl reload

# Método 2: Reiniciar Hyprland (logout/login)
```

### 4. Testar

1. Selecione algum texto em qualquer aplicativo (Firefox, terminal, etc.)
2. Pressione `SUPER + T` → deve ouvir o áudio
3. Pressione `SUPER + SHIFT + T` → áudio deve parar

---

## 🔊 Configuração de Áudio

### Identificar device de áudio

Execute o seguinte comando para listar devices disponíveis:

```bash
python -c "
import pyaudio
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if info['maxOutputChannels'] > 0:
        print(f'{i}: {info[\"name\"]}')
"
```

**Exemplo de saída**:

```
0: HDA Intel PCH: ALC295 Analog (hw:0,0)
1: HDA NVidia: HDMI 0 (hw:1,3)
5: pulse
9: default
```

### Configurar device no código

Edite `src/real_selection/main.py` (linha ~260):

```python
stream = self.pyaudio_instance.open(
    format=pyaudio.paFloat32,
    channels=1,
    rate=24000,
    output=True,
    output_device_index=9,  # ← Altere este número
    frames_per_buffer=2048
)
```

**Valores comuns**:
- `None` ou omitir parâmetro: usa device padrão do sistema (recomendado)
- `9`: device `default` (comum em sistemas PulseAudio)
- `5`: PulseAudio diretamente

### Testar áudio manualmente

```bash
# Teste básico
speaker-test -c 1 -t wav

# Se não funcionar, verifique PulseAudio/PipeWire
pactl list sinks short
```

---

## 🐛 Troubleshooting

### ❌ Problema: "wl-clipboard não está instalado"

**Erro**:
```
[ERROR] wl-clipboard não está instalado
[ERROR] Instale com: sudo pacman -S wl-clipboard
```

**Solução**:
```bash
sudo pacman -S wl-clipboard  # Arch
sudo apt install wl-clipboard  # Debian/Ubuntu
```

---

### ❌ Problema: "Nenhum texto selecionado"

**Erro**:
```
[WARNING] Nenhum texto selecionado
```

**Causas possíveis**:
1. Texto não foi selecionado (área primária vazia)
2. Aplicativo não suporta seleção primária do Wayland

**Solução**:
1. **Teste básico**: Selecione texto no terminal e execute `wl-paste --primary`
2. **Firefox/Chromium**: Alguns apps usam clipboard secundário. Tente copiar com `Ctrl+C` e modifique script para usar `wl-paste` (sem `--primary`)

---

### ❌ Problema: Sem áudio / "OSError: [Errno -9999]"

**Erro**:
```
OSError: [Errno -9999] Unanticipated host error
```

**Causas**:
1. Device de áudio incorreto
2. PortAudio não encontra device
3. Permissões de áudio

**Solução**:

1. **Liste devices** (veja [Configuração de Áudio](#configuração-de-áudio))
2. **Ajuste `output_device_index`** ou **remova o parâmetro** (usa default)
3. **Verifique permissões**:
   ```bash
   # Adicione usuário ao grupo audio
   sudo usermod -aG audio $USER
   
   # Logout/login para aplicar
   ```

4. **Teste PulseAudio**:
   ```bash
   pulseaudio --check
   pulseaudio --start
   ```

---

### ❌ Problema: Latência muito alta (>2s)

**Sintomas**: Demora muito até áudio começar

**Causas**:
1. Usando CPU em vez de GPU
2. Modelo sendo baixado pela primeira vez

**Solução**:

1. **Verifique CUDA**:
   ```bash
   python -c "import torch; print('CUDA:', torch.cuda.is_available())"
   ```
   
   Se `False`, instale CUDA:
   ```bash
   sudo pacman -S cuda  # Arch
   ```

2. **Primeira execução**: Modelo Kokoro-82M (~350 MB) é baixado. Aguarde o download completar.

3. **Logs**: Verifique `logs/tts_debug.log`:
   ```bash
   tail -f logs/tts_debug.log
   ```

---

### ❌ Problema: "Já existe uma instância rodando"

**Sintomas**: Notificação "Já existe uma instância rodando" ao pressionar `SUPER+T`

**Causa**: Lock file não foi removido (processo anterior travou)

**Solução**:

```bash
# Remova lock file manualmente
rm -f /tmp/kokoro_tts.lock

# Ou mate processo manualmente
pkill -f "python.*real_selection"
```

---

### ❌ Problema: Áudio picotado / chunks perdidos

**Sintomas**: Áudio com cortes, logs mostram chunks gerados ≠ chunks tocados

**Causa**: Consumer não acompanha producer (sistema lento ou buffer pequeno)

**Solução**:

1. **Aumente queue size** em `main.py` (linha ~380):
   ```python
   audio_queue = queue.Queue(maxsize=20)  # Era 10
   ```

2. **Aumente buffer do PyAudio** (linha ~260):
   ```python
   frames_per_buffer=4096  # Era 2048
   ```

3. **Feche aplicativos pesados** para liberar CPU

---

### ❌ Problema: Notificações não aparecem

**Sintomas**: TTS funciona mas não vê notificações visuais

**Causa**: `notify-send` não instalado ou servidor de notificações não rodando

**Solução**:

1. **Instale libnotify**:
   ```bash
   sudo pacman -S libnotify
   ```

2. **Verifique daemon de notificações** (Hyprland usa `mako` ou `dunst`):
   ```bash
   # Instale mako (recomendado para Hyprland)
   sudo pacman -S mako
   
   # Inicie mako
   mako &
   
   # Teste
   notify-send "Teste" "Funcionou!"
   ```

---

### ❌ Problema: Logs mostram "ALSA lib ... underrun occurred"

**Sintomas**: Warnings do ALSA nos logs

**Causa**: Avisos normais do ALSA, não afetam funcionamento

**Solução**: Ignorar (script já filtra automaticamente). Se incomodar, adicione ao `~/.asoundrc`:

```conf
pcm.!default {
    type plug
    slave.pcm "dmixer"
}

pcm.dmixer {
    type dmix
    ipc_key 1024
    slave {
        pcm "hw:0,0"
        period_time 0
        period_size 1024
        buffer_size 4096
        rate 48000
    }
}
```

---

## 🗑️ Desinstalação

### 1. Remover binds do Hyprland

Edite `~/.config/hypr/hyprland.conf` e remova as linhas:

```conf
bind = SUPER, T, exec, ...
bind = SUPER SHIFT, T, exec, ...
```

### 2. Remover diretório do projeto

```bash
rm -rf ~/projetos/real_selection
```

### 3. Remover lock file (se existir)

```bash
rm -f /tmp/kokoro_tts.lock
```

### 4. (Opcional) Remover dependências Python

```bash
# Se instalou via uv
rm -rf ~/.local/share/uv

# Se instalou via pip
pip uninstall kokoro pyaudio
```

---

## 📚 Recursos Adicionais

- **[Arquitetura](ARQUITETURA.md)** — Entenda como o sistema funciona internamente
- **[Vozes e Idiomas](VOZES.md)** — Configure outras vozes e idiomas
- **[Desenvolvimento](DESENVOLVIMENTO.md)** — Contribua com o projeto

---

## 💬 Suporte

Encontrou um problema não listado aqui?

1. **Verifique logs**: `cat logs/tts_debug.log`
2. **Issues no GitHub**: [github.com/renatobarros-ai/real_selection/issues](https://github.com/renatobarros-ai/real_selection/issues)
3. **Email**: falecomrenatobarros@gmail.com

---

<div align="center">

**[⬆ Voltar ao README](../README.md)** | **[📐 Arquitetura](ARQUITETURA.md)** | **[🎤 Vozes](VOZES.md)**

---

**Real Selection** — Copyright (C) 2025 Renato Barros  
Licenciado sob GNU GPL v3.0+

</div>
