# 🔍 Revisão do .gitignore

## ❌ Problemas Encontrados no Original

### 1. Duplicação
```gitignore
# Linha 24-26
logs/
*.log

# Linha 32-34 (DUPLICADO)
logs/
*.log
```

### 2. `.tool-versions` ignorado
```gitignore
# Linha 29
.tool-versions
```

**Problema**: Este arquivo **DEVERIA** ser versionado! Ele garante que todos os desenvolvedores usem as mesmas versões de Python/Node/etc.

### 3. Faltando itens essenciais
- ❌ Suporte ao `uv` (`.uv/`)
- ❌ Caches de teste (pytest, coverage)
- ❌ IDEs populares (VSCode, PyCharm completo)
- ❌ Arquivos temporários do TTS (`/tmp/kokoro_*`)
- ❌ Caches do PyTorch/Kokoro
- ❌ OS files (Windows, macOS completo)

---

## ✅ Novo .gitignore (173 linhas)

### Organização por Categorias

```
1. Arquivos de desenvolvimento pessoal
   ├── CLAUDE.md, GEMINI.md (mantidos)
   └── .dev_docs/rascunhos/

2. Python (completo)
   ├── Bytecode (__pycache__, *.pyc, *.pyo)
   ├── Build (dist/, *.egg-info)
   ├── Virtual envs (.venv, venv, ENV)
   ├── uv específico (.uv/)
   ├── Pytest (.pytest_cache/, .coverage)
   ├── MyPy (.mypy_cache/)
   └── Ruff (.ruff_cache/)

3. Logs e temporários
   ├── logs/ e *.log
   ├── /tmp/kokoro_tts* (lock files do TTS)
   └── Caches Kokoro/PyTorch

4. Secrets
   ├── .env e variações
   └── Exceção: !.env.example

5. IDEs
   ├── VSCode (.vscode/)
   ├── PyCharm (.idea/)
   ├── Vim (*.swp)
   ├── Emacs (*~)
   └── Sublime (*.sublime-*)

6. Sistema Operacional
   ├── macOS (.DS_Store, ._*)
   ├── Linux (*~, .directory)
   └── Windows (Thumbs.db, Desktop.ini)

7. Arquivos de áudio/modelos
   ├── debug_chunk_*.wav
   └── *.bin.tmp, *.safetensors.tmp

8. Outros
   ├── Backups (*.bak, *.old)
   ├── Compactados (*.zip, *.tar.gz)
   └── DBs locais (*.db, *.sqlite)
```

---

## 🎯 Decisões Importantes

### ✅ O que NÃO foi ignorado (e por quê)

```gitignore
# DEVEM ser versionados:
.tool-versions          # Garante versões consistentes
uv.lock                 # Lock de dependências (reprodutibilidade)
pyproject.toml          # Configuração do projeto
LICENSE                 # Licença GPL v3
```

### ⚠️ Patterns estratégicos

```gitignore
# Permite .env.example (documentação)
.env
.env.*
!.env.example

# Ignora todos os .zip EXCETO releases
*.zip
!releases/*.tar.gz

# Arquivos de debug temporários
debug_chunk_*.wav       # Chunks de áudio para debug
test_audio_*.wav        # Testes de áudio
```

---

## 📂 Arquivos .gitkeep Criados

Para manter diretórios vazios no Git:

```
logs/.gitkeep           # Pasta de logs (vazia inicialmente)
tests/.gitkeep          # Pasta de testes (a ser populada)
```

**Por quê?** Git não versiona diretórios vazios. O `.gitkeep` é uma convenção para forçar o versionamento da estrutura.

---

## 🔄 Como Aplicar

### 1. Backup do .gitignore atual

```bash
cp .gitignore .gitignore.backup
```

### 2. Substituir pelo novo

```bash
cp /caminho/outputs/.gitignore .gitignore
```

### 3. Criar .gitkeep

```bash
echo "# Este arquivo mantém o diretório no Git" > logs/.gitkeep
echo "# Este arquivo mantém o diretório no Git" > tests/.gitkeep
```

### 4. Limpar cache do Git (se necessário)

```bash
# Remove arquivos que AGORA estão no .gitignore mas já foram commitados
git rm -r --cached .
git add .
git commit -m "chore: atualiza .gitignore com patterns completos"
```

---

## 📊 Comparação

| Item | Antes | Depois |
|------|-------|--------|
| **Linhas** | 36 | 173 |
| **Categorias** | 6 | 8 |
| **Duplicatas** | ✅ Sim | ❌ Não |
| **uv support** | ❌ | ✅ |
| **IDEs completo** | ❌ | ✅ |
| **OS files completo** | ❌ | ✅ |
| **TTS temporários** | ❌ | ✅ |
| **Comentários** | Básicos | Organizados |

---

## 🎨 Melhorias Extras

### Header GPL v3

```gitignore
# Real Selection - .gitignore
# Copyright (C) 2025 Renato Barros
# Licenciado sob GNU General Public License v3.0 ou posterior.
```

### Comentários úteis

Cada seção tem comentários explicativos:
```gitignore
# ============================================================================
# PYTHON
# ============================================================================
```

---

## ⚙️ Configurações Recomendadas

### Para desenvolvedores

Adicione ao seu `.git/config` local (não commitado):

```ini
[core]
    excludesfile = ~/.gitignore_global
```

E crie `~/.gitignore_global` com seus ignores pessoais:
```gitignore
# Minhas notas pessoais
TODO.txt
NOTES.md

# Meu editor preferido
.vscode/settings.json
```

---

## ✅ Checklist de Aplicação

Antes de commitar:

- [ ] .gitignore substituído
- [ ] .gitkeep criado em logs/ e tests/
- [ ] .tool-versions REMOVIDO do .gitignore (se estava)
- [ ] `git status` para verificar arquivos não trackeados
- [ ] Limpar cache do Git se necessário
- [ ] Commit com mensagem descritiva

---

<div align="center">

**Real Selection** — Copyright (C) 2025 Renato Barros  
Licenciado sob GNU GPL v3.0+

</div>
