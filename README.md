# 🎙️ Real Selection

> **Síntese de voz em tempo real a partir de texto selecionado no Wayland**

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Kokoro TTS](https://img.shields.io/badge/TTS-Kokoro--82M-green.svg)](https://github.com/hexgrad/kokoro)
[![Wayland](https://img.shields.io/badge/Wayland-only-orange.svg)](https://wayland.freedesktop.org/)

---

## 📋 Sobre

**Real Selection** é uma ferramenta que transforma texto selecionado em áudio usando síntese de voz neural em português brasileiro. Basta selecionar um texto em qualquer aplicativo e pressionar um atalho — o áudio é gerado e reproduzido instantaneamente com streaming em tempo real.

### ✨ Características

- 🎯 **Captura automática** via seleção primária do Wayland
- 🚀 **Streaming em tempo real** com latência mínima (threading)
- 🔊 **Voz natural** em português BR (Kokoro-82M, voz `pf_dora`)
- ⚡ **Aceleração GPU** via CUDA (fallback para CPU)
- 🎨 **Integração Hyprland** com atalhos de teclado personalizados
- 🔇 **Controle total** — inicia e interrompe a qualquer momento

---

## 🚀 Instalação

### Requisitos

- **Sistema**: Linux com Wayland (testado no Arch + Hyprland)
- **Python**: 3.10 a 3.13
- **GPU** (opcional): NVIDIA com CUDA para aceleração

### Dependências do sistema

```bash
# Arch Linux
sudo pacman -S python python-pip portaudio wl-clipboard

# Debian/Ubuntu
sudo apt install python3 python3-pip portaudio19-dev wl-clipboard
```

### Instalação do projeto

```bash
# Clone o repositório
git clone https://github.com/renatobarros-ai/real_selection.git
cd real_selection

# Instale dependências (recomendado: uv)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync

# Ou via pip
pip install -e .
```

---

## 📖 Uso Rápido

### 1️⃣ Modo CLI

```bash
# Selecione um texto em qualquer aplicativo
# Execute:
uv run python src/real_selection/main.py

# Ou, se instalado via pip:
real_selection
```

### 2️⃣ Integração com Hyprland

Adicione ao seu `~/.config/hypr/hyprland.conf`:

```conf
# Iniciar TTS
bind = SUPER, T, exec, /caminho/para/scripts/tts_wrapper.sh

# Interromper TTS
bind = SUPER SHIFT, T, exec, /caminho/para/scripts/tts_kill.sh
```

**Uso:**
1. Selecione texto com o mouse
2. Pressione `SUPER + T` → áudio é reproduzido
3. Pressione `SUPER + SHIFT + T` → interrompe reprodução

---

## 📚 Documentação

| Documento | Descrição |
|-----------|-----------|
| [📐 Arquitetura](docs/ARQUITETURA.md) | Detalhes técnicos do sistema (threads, pipeline, streaming) |
| [⚙️ Configuração](docs/CONFIGURACAO.md) | Setup completo para Hyprland, troubleshooting |
| [🎤 Vozes e Idiomas](docs/VOZES.md) | Como configurar vozes, idiomas e velocidade |
| [👩‍💻 Desenvolvimento](docs/DESENVOLVIMENTO.md) | Setup dev, testes, contribuições |

---

## 🎤 Vozes Disponíveis

O projeto usa **Kokoro-82M** (modelo neural de 82 milhões de parâmetros). Por padrão, está configurado para:

- **Idioma**: Português Brasileiro (`lang_code='p'`)
- **Voz**: `pf_dora` (voz feminina natural)
- **Velocidade**: 1.0 (normal)

### Recursos Kokoro

- 📦 **Modelo no HuggingFace**: [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)
- 🎭 **Lista completa de vozes**: [VOICES.md](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md)
- 💻 **Repositório oficial**: [github.com/hexgrad/Kokoro](https://github.com/hexgrad/Kokoro)
- 📚 **Guia de uso completo**: [Asimov Academy](https://github.com/asimov-academy/Kokoro-TTS---Guia-de-uso)

Para configurar outras vozes e idiomas no Real Selection, consulte **[docs/VOZES.md](docs/VOZES.md)**.

---

## 🛠️ Tecnologias

- **[Kokoro-82M](https://github.com/hexgrad/kokoro)** — TTS neural de alta qualidade
- **[PyAudio](https://people.csail.mit.edu/hubert/pyaudio/)** — Reprodução de áudio via PortAudio
- **[PyTorch](https://pytorch.org/)** — Inferência do modelo (GPU/CPU)
- **[wl-clipboard](https://github.com/bugaevc/wl-clipboard)** — Captura de seleção no Wayland
- **[Loguru](https://github.com/Delgan/loguru)** — Sistema de logging

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Veja **[docs/DESENVOLVIMENTO.md](docs/DESENVOLVIMENTO.md)** para:

- Setup do ambiente de desenvolvimento
- Convenções de código
- Como reportar bugs ou sugerir features

---

## 📜 Licença

**Real Selection** é software livre licenciado sob **GNU General Public License v3.0 ou posterior**.

```
Real Selection - Síntese de voz em tempo real a partir de texto selecionado
Copyright (C) 2025 Renato Barros

Este programa é software livre: você pode redistribuí-lo e/ou modificá-lo
sob os termos da GNU General Public License conforme publicada pela
Free Software Foundation, versão 3 da Licença, ou (a seu critério)
qualquer versão posterior.
```

Veja o arquivo [LICENSE](LICENSE) para detalhes completos.

---

## 👤 Autor

**Renato Barros**  
📧 falecomrenatobarros@gmail.com  
🐙 [github.com/renatobarros-ai](https://github.com/renatobarros-ai)

---

## 🙏 Agradecimentos

- **[hexgrad/Kokoro](https://github.com/hexgrad/Kokoro)** — por disponibilizar modelo TTS de alta qualidade open source
- **[Asimov Academy](https://github.com/asimov-academy)** — pelo excelente guia de uso do Kokoro TTS
- **Comunidade Wayland/Hyprland** — por ferramentas e suporte

---

<div align="center">

**[⬆ Voltar ao topo](#-real-selection)**

Feito com ❤️ por [Renato Barros](https://github.com/renatobarros-ai)

</div>
