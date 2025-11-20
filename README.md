# Real Selection

A tool to read selected text using Kokoro TTS with real-time streaming and GPU acceleration.

## Features

- 🎯 Captures Wayland primary selection (highlighted text, no Ctrl+C needed)
- 🇧🇷 Brazilian Portuguese TTS with natural voice (pf_dora)
- ⚡ Real-time audio streaming with ~300-500ms latency
- 🚀 GPU (CUDA) accelerated with automatic CPU fallback
- 🔧 Hyprland keyboard shortcuts integration
- 📊 Dual logging system (INFO console, DEBUG file)

## Requirements

### System Dependencies (Arch Linux)

```bash
sudo pacman -S wl-clipboard espeak-ng portaudio
```

### Python

- Python >= 3.13
- UV package manager

## Installation

### 1. Install UV (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and Install Real Selection

```bash
git clone https://github.com/renatobarros-ai/real_selection.git
cd real_selection
uv sync
```

This will:
- Create a virtual environment
- Install all dependencies (including Kokoro)
- Make the `real_selection` command available

### 3. Verify Installation

```bash
# Run dependency tests
uv run python tests/test_dependencies.py

# Test the tool (select some text first)
uv run real_selection
```

## Usage

### Basic Usage

1. **Select text** in any application (browser, PDF viewer, terminal)
2. Run: `uv run real_selection`
3. The audio will start playing automatically

### Using Scripts (Recommended)

For background execution with notifications:

```bash
# Make scripts executable
chmod +x scripts/tts_wrapper.sh scripts/tts_kill.sh

# Run TTS
./scripts/tts_wrapper.sh

# Stop TTS
./scripts/tts_kill.sh
```

### Hyprland Integration

Add to your `~/.config/hypr/hyprland.conf`:

```conf
# Read selected text
bind = SUPER, T, exec, /path/to/real_selection/scripts/tts_wrapper.sh

# Stop TTS
bind = SUPER SHIFT, T, exec, /path/to/real_selection/scripts/tts_kill.sh
```

Then reload Hyprland: `hyprctl reload`

## Development

### Running Tests

```bash
# All tests
uv run pytest tests/

# Specific tests
uv run python tests/test_dependencies.py
uv run python tests/test_selection.py
uv run python tests/test_gpu_pipeline.py
```

### Project Structure

```
real_selection/
├── src/real_selection/
│   ├── main.py          # Main TTS engine
│   └── clipboard.py     # Primary selection capture
├── scripts/             # Integration scripts
├── tests/               # Test suite
├── docs/                # Documentation
└── pyproject.toml       # Project configuration
```

## Troubleshooting

See [docs/README_LER_SELECAO.md](docs/README_LER_SELECAO.md) for detailed troubleshooting guide.

## Security & Privacy

- 🔒 **No audio files saved**: Audio streams directly to speakers, never touches disk
- 🔒 **No text content logged**: Logs only show text length, never the actual content
- 🔒 **Volatile by design**: Primary selection cleared on new selection
- 🔒 **Offline operation**: No network requests after model download

## License

GPL-3.0-or-later

This project uses [Kokoro-82M](https://github.com/hexgrad/Kokoro-82M) as a library, which is licensed under Apache-2.0.
