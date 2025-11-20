# 👩‍💻 Desenvolvimento

> **Guia para contribuidores e desenvolvedores do Real Selection**

---

## 📑 Índice

- [Setup do Ambiente](#setup-do-ambiente)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Convenções de Código](#convenções-de-código)
- [Testes](#testes)
- [Debugging](#debugging)
- [Como Contribuir](#como-contribuir)
- [Roadmap](#roadmap)

---

## 🛠️ Setup do Ambiente

### Pré-requisitos

- Python 3.10+
- Git
- wl-clipboard
- PortAudio
- *(Opcional)* CUDA para desenvolvimento com GPU

### 1. Fork e clone

```bash
# Fork no GitHub: https://github.com/renatobarros-ai/real_selection

# Clone seu fork
git clone https://github.com/SEU_USUARIO/real_selection.git
cd real_selection

# Adicione upstream
git remote add upstream https://github.com/renatobarros-ai/real_selection.git
```

### 2. Instale uv (gerenciador recomendado)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. Instale dependências

```bash
# Cria venv e instala deps
uv sync

# Instale dependências de desenvolvimento
uv pip install pytest black ruff mypy
```

### 4. Configure pre-commit (opcional)

```bash
# Instale pre-commit
uv pip install pre-commit

# Configure hooks
pre-commit install
```

---

## 📂 Estrutura do Projeto

```
real_selection/
├── docs/                     # Documentação
│   ├── ARQUITETURA.md
│   ├── CONFIGURACAO.md
│   ├── VOZES.md
│   └── DESENVOLVIMENTO.md
├── integrations/
│   └── hyprland_binds.conf   # Exemplo de config Hyprland
├── logs/                     # Logs gerados (git ignored)
│   └── tts_debug.log
├── scripts/
│   ├── tts_wrapper.sh        # Wrapper de execução
│   └── tts_kill.sh           # Script de interrupção
├── src/
│   └── real_selection/
│       ├── __init__.py
│       └── main.py           # Código principal
├── tests/                    # Testes unitários (TODO)
│   └── test_main.py
├── .gitignore
├── LICENSE                   # GPL v3
├── pyproject.toml            # Configuração do projeto
├── README.md
└── uv.lock                   # Lock file do uv
```

---

## 📝 Convenções de Código

### Style Guide

Seguimos **[PEP 8](https://peps.python.org/pep-0008/)** com algumas exceções:

- **Linha máxima**: 100 caracteres (não 79)
- **Strings**: Preferencialmente aspas duplas `"texto"` (exceto f-strings simples)
- **Docstrings**: Google style

### Formatação automática

```bash
# Black (formatação)
black src/ tests/

# Ruff (linting)
ruff check src/ tests/ --fix

# MyPy (type checking)
mypy src/
```

### Exemplo de código bem formatado

```python
"""
Módulo de exemplo.

Este módulo demonstra convenções de código do projeto.
"""

from typing import Optional


def processar_texto(
    texto: str, 
    max_length: Optional[int] = None
) -> str:
    """
    Processa texto para TTS.
    
    Args:
        texto: Texto bruto a processar
        max_length: Limite de caracteres (None = sem limite)
    
    Returns:
        Texto processado e limpo
    
    Raises:
        ValueError: Se texto vazio
    """
    if not texto:
        raise ValueError("Texto não pode ser vazio")
    
    texto_limpo = texto.strip()
    
    if max_length and len(texto_limpo) > max_length:
        texto_limpo = texto_limpo[:max_length]
    
    return texto_limpo
```

### Comentários

- **Docstrings**: Todas as funções públicas devem ter
- **Inline comments**: Use com moderação, explique "porquê" não "o quê"
- **TODOs**: Format `# TODO: Descrição`
- **FIXMEs**: Format `# FIXME: Problema a corrigir`

```python
# ❌ Ruim (explica o óbvio)
x = x + 1  # Incrementa x

# ✅ Bom (explica razão)
x = x + 1  # Compensa offset do header WAVE
```

---

## 🧪 Testes

### Estrutura de testes

```
tests/
├── __init__.py
├── test_main.py           # Testes do main.py
├── test_audio.py          # Testes de áudio
└── fixtures/
    └── sample_text.txt    # Dados de teste
```

### Executar testes

```bash
# Todos os testes
pytest

# Teste específico
pytest tests/test_main.py::test_limpar_texto

# Com cobertura
pytest --cov=src/real_selection --cov-report=html
```

### Exemplo de teste

```python
"""Testes para funções de limpeza de texto."""

import pytest
from real_selection.main import limpar_texto_para_tts


def test_limpar_quebras_simples():
    """Remove quebras simples mas mantém parágrafos."""
    texto = "Linha 1\nLinha 2\n\nParágrafo 2"
    esperado = "Linha 1 Linha 2\n\nParágrafo 2"
    
    resultado = limpar_texto_para_tts(texto)
    
    assert resultado == esperado


def test_limpar_texto_vazio():
    """Retorna None para texto vazio."""
    assert limpar_texto_para_tts("") is None
    assert limpar_texto_para_tts("   ") is None


@pytest.mark.parametrize("entrada,esperado", [
    ("a  b", "a b"),           # Múltiplos espaços
    ("a\t\tb", "a b"),         # Tabs
    ("  a b  ", "a b"),        # Espaços nas bordas
])
def test_limpar_espacos(entrada, esperado):
    """Remove espaços múltiplos e nas bordas."""
    assert limpar_texto_para_tts(entrada) == esperado
```

---

## 🐛 Debugging

### Logs de desenvolvimento

```python
# Habilite DEBUG em todo lugar (temporário)
import logging
logging.basicConfig(level=logging.DEBUG)

# Ou use loguru diretamente
from loguru import logger
logger.debug("Mensagem de debug detalhada")
```

### Debug interativo

```bash
# IPython para REPL avançado
uv pip install ipython

# Execute script no modo debug
python -m pdb src/real_selection/main.py
```

### Comandos úteis do pdb

```python
# Breakpoint
import pdb; pdb.set_trace()

# Comandos
(Pdb) n          # Next line
(Pdb) s          # Step into
(Pdb) c          # Continue
(Pdb) p var      # Print variable
(Pdb) l          # List code
(Pdb) h          # Help
```

### Debug de áudio

```python
# Salvar chunks para análise
import soundfile as sf

for i, chunk in enumerate(audio_chunks):
    sf.write(f"debug_chunk_{i}.wav", chunk, 24000)
```

---

## 🤝 Como Contribuir

### 1. Issues

Antes de contribuir, verifique se já existe uma [issue](https://github.com/renatobarros-ai/real_selection/issues) relacionada.

**Reportar bug**:
```markdown
### Descrição do bug
TTS não funciona ao selecionar texto no Firefox.

### Passos para reproduzir
1. Abrir Firefox
2. Selecionar texto
3. Pressionar SUPER+T

### Comportamento esperado
Áudio deve ser reproduzido.

### Comportamento atual
Nenhum áudio, erro nos logs: "..."

### Ambiente
- OS: Arch Linux
- Hyprland: 0.35.0
- Python: 3.11.6
- CUDA: N/A (CPU)

### Logs
```
[ERROR] ...
```
```

**Sugerir feature**:
```markdown
### Descrição
Adicionar suporte a múltiplas vozes via atalhos diferentes.

### Proposta
- SUPER+T: voz feminina
- SUPER+SHIFT+T: voz masculina
- SUPER+ALT+T: voz alternativa

### Motivação
Facilita testar vozes sem editar código.
```

### 2. Pull Requests

#### Fluxo de trabalho

```bash
# 1. Sincronize com upstream
git checkout main
git fetch upstream
git merge upstream/main

# 2. Crie branch para feature/fix
git checkout -b feature/nova-funcionalidade

# 3. Desenvolva e commite
git add .
git commit -m "feat: adiciona suporte a múltiplas vozes"

# 4. Formate código
black src/ tests/
ruff check src/ tests/ --fix

# 5. Execute testes
pytest

# 6. Push para seu fork
git push origin feature/nova-funcionalidade

# 7. Abra PR no GitHub
```

#### Convenções de commit

Seguimos **[Conventional Commits](https://www.conventionalcommits.org/)**:

```
tipo(escopo): descrição curta

Descrição detalhada (opcional).

Refs: #123
```

**Tipos**:
- `feat`: Nova funcionalidade
- `fix`: Correção de bug
- `docs`: Apenas documentação
- `style`: Formatação (sem mudança de lógica)
- `refactor`: Refatoração de código
- `test`: Adiciona/corrige testes
- `chore`: Manutenção (deps, config)

**Exemplos**:
```bash
feat(audio): adiciona suporte a device configurável
fix(cleanup): corrige regex de limpeza de texto
docs(readme): atualiza instruções de instalação
refactor(threads): simplifica lógica de producer
test(main): adiciona testes para limpar_texto_para_tts
```

#### Checklist do PR

- [ ] Código formatado (black, ruff)
- [ ] Testes passando (`pytest`)
- [ ] Documentação atualizada (se necessário)
- [ ] Commit messages seguem Conventional Commits
- [ ] PR descreve mudanças claramente

---

## 🗺️ Roadmap

### 🚀 v0.2.0 (Próximo release)

- [ ] **Configuração via CLI/env** — Remover hardcoded `output_device_index`
- [ ] **Testes unitários** — Cobertura de 80%+
- [ ] **CI/CD** — GitHub Actions (testes, linting)
- [ ] **Package PyPI** — `pip install real-selection`

### 🔮 v0.3.0 (Futuro)

- [ ] **Seleção de voz via atalho** — Múltiplas vozes sem editar código
- [ ] **Suporte a X11** — Fallback para `xclip`
- [ ] **GUI simples** — Painel de controle (Qt/GTK)
- [ ] **Cache de pipeline** — Reutilizar entre processos

### 💡 Ideias abertas

- [ ] **API REST** — TTS via HTTP (uso remoto)
- [ ] **Suporte a outros TTS** — Fallback para Piper, Coqui
- [ ] **Streaming para arquivo** — Salvar áudio em vez de reproduzir
- [ ] **Integração com Neovim/Emacs** — Ler buffer do editor

**Quer trabalhar em algo?** Comente na [issue correspondente](https://github.com/renatobarros-ai/real_selection/issues) ou abra uma nova!

---

## 📚 Recursos Úteis

### Documentação Kokoro

- **Repositório GitHub**: [github.com/hexgrad/Kokoro](https://github.com/hexgrad/Kokoro)
- **Modelo HuggingFace**: [huggingface.co/hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)
- **Lista de vozes**: [VOICES.md](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md)
- **Guia de uso (Asimov Academy)**: [Kokoro-TTS - Guia de uso](https://github.com/asimov-academy/Kokoro-TTS---Guia-de-uso)

### Documentação externa

- **PyAudio**: [people.csail.mit.edu/hubert/pyaudio/docs/](https://people.csail.mit.edu/hubert/pyaudio/docs/)
- **PyTorch**: [pytorch.org/docs/](https://pytorch.org/docs/)
- **Wayland protocols**: [wayland.freedesktop.org/docs/html/](https://wayland.freedesktop.org/docs/html/)

### Ferramentas

- **uv**: [astral.sh/uv](https://astral.sh/uv)
- **Black**: [black.readthedocs.io](https://black.readthedocs.io)
- **Ruff**: [docs.astral.sh/ruff/](https://docs.astral.sh/ruff/)
- **Pytest**: [docs.pytest.org](https://docs.pytest.org)

---

## 💬 Comunidade

- **GitHub Discussions**: [github.com/renatobarros-ai/real_selection/discussions](https://github.com/renatobarros-ai/real_selection/discussions)
- **Issues**: [github.com/renatobarros-ai/real_selection/issues](https://github.com/renatobarros-ai/real_selection/issues)
- **Email**: falecomrenatobarros@gmail.com

---

## 🙏 Agradecimentos

Obrigado por considerar contribuir com o **Real Selection**!

Toda contribuição é valorizada, seja:
- 🐛 Reportar bugs
- 💡 Sugerir features
- 📝 Melhorar documentação
- 🔧 Corrigir código
- ⭐ Dar star no repositório

---

<div align="center">

**[⬆ Voltar ao README](../README.md)** | **[📐 Arquitetura](ARQUITETURA.md)** | **[⚙️ Configuração](CONFIGURACAO.md)**

---

**Real Selection** — Copyright (C) 2025 Renato Barros  
Licenciado sob GNU GPL v3.0+

</div>
