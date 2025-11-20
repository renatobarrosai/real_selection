# 📋 Guia de Implementação

> **Checklist para aplicar a documentação no projeto Real Selection**

---

## ✅ Checklist de Implementação

### 1. Código Comentado

- [x] **main.py** — Header GPL v3 + comentários concisos
- [x] **tts_wrapper.sh** — Header GPL v3 + documentação
- [x] **tts_kill.sh** — Header GPL v3 + estratégia de kill
- [x] **pyproject.toml** — Header GPL v3 + comentários

### 2. Documentação Principal

- [x] **README.md** — Porta de entrada com badges, links, design rico

### 3. Documentação Detalhada (`docs/`)

- [x] **ARQUITETURA.md** — Detalhes técnicos (threading, pipeline, performance)
- [x] **CONFIGURACAO.md** — Instalação, setup Hyprland, troubleshooting
- [x] **VOZES.md** — Configuração de vozes, idiomas, parâmetros
- [x] **DESENVOLVIMENTO.md** — Setup dev, testes, contribuições, roadmap

### 4. Integrações

- [x] **hyprland_binds.conf** — Exemplo de configuração para copiar

---

## 📂 Como Aplicar no Projeto

### Passo 1: Backup do projeto atual

```bash
cd ~/seu-projeto-real-selection
tar -czf backup-$(date +%Y%m%d).tar.gz .
```

### Passo 2: Copiar arquivos comentados

```bash
# Copie os arquivos de /mnt/user-data/outputs/ para seu projeto:

# Código comentado
cp /caminho/outputs/src/real_selection/main.py src/real_selection/
cp /caminho/outputs/scripts/*.sh scripts/
cp /caminho/outputs/pyproject.toml .

# Torne scripts executáveis
chmod +x scripts/*.sh
```

### Passo 3: Adicionar documentação

```bash
# README principal
cp /caminho/outputs/README.md .

# Docs detalhadas
mkdir -p docs
cp /caminho/outputs/docs/*.md docs/

# Integração
mkdir -p integrations
cp /caminho/outputs/integrations/hyprland_binds.conf integrations/
```

### Passo 4: Ajustes específicos do seu ambiente

#### A. Device de áudio (main.py linha ~260)

```python
# Antes (hardcoded):
output_device_index=9

# Depois (use default do sistema):
# output_device_index=None  # OU REMOVA O PARÂMETRO
```

**Como descobrir seu device**:
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

#### B. Caminhos nos scripts Hyprland

Edite `integrations/hyprland_binds.conf`:

```conf
# Ajuste esta linha:
$REAL_SELECTION_PATH = ~/projetos/real_selection

# Para o caminho correto do seu projeto:
$REAL_SELECTION_PATH = /caminho/completo/para/seu/projeto
```

### Passo 5: Testar

```bash
# Teste Python script diretamente
uv run python src/real_selection/main.py

# Teste wrappers
./scripts/tts_wrapper.sh

# Adicione binds ao Hyprland (copie do hyprland_binds.conf)
# Recarregue: hyprctl reload
```

---

## 🎨 Personalizações Recomendadas

### 1. Adicione screenshot ao README

Crie uma pasta `assets/` e adicione imagem:

```markdown
# No README.md, após o título:

![Demo](assets/demo.gif)
```

### 2. Badges personalizados

No README.md, adicione badges relevantes:

```markdown
[![GitHub stars](https://img.shields.io/github/stars/renatobarros-ai/real_selection?style=social)](https://github.com/renatobarros-ai/real_selection)
[![GitHub issues](https://img.shields.io/github/issues/renatobarros-ai/real_selection)](https://github.com/renatobarros-ai/real_selection/issues)
```

### 3. Configure .gitignore

Certifique-se de ter:

```gitignore
# Logs
logs/
*.log

# Python
__pycache__/
*.pyc
.venv/
*.egg-info/

# Lock files
/tmp/
*.lock

# IDEs
.vscode/
.idea/
```

---

## 📝 Próximos Passos

### Imediato

1. ✅ Revisar código comentado
2. ✅ Revisar documentação
3. ⬜ Ajustar device de áudio (remover hardcode)
4. ⬜ Testar em ambiente local
5. ⬜ Commit no GitHub

### Curto prazo

1. ⬜ Adicionar screenshot/demo
2. ⬜ Criar GitHub Release v0.1.0
3. ⬜ Adicionar badges ao README
4. ⬜ Compartilhar no Reddit/HN/lobste.rs

### Médio prazo

1. ⬜ Implementar testes (docs/DESENVOLVIMENTO.md)
2. ⬜ CI/CD com GitHub Actions
3. ⬜ Publicar no PyPI
4. ⬜ Configuração via CLI/env (remover hardcodes)

---

## 🔍 Verificação Final

Antes de publicar, certifique-se:

- [ ] Todos os arquivos têm header GPL v3
- [ ] Seu nome/email estão corretos em todos os arquivos
- [ ] Links internos funcionam (README → docs → etc.)
- [ ] Código funciona sem erros
- [ ] Scripts têm permissão de execução (`chmod +x`)
- [ ] .gitignore está configurado
- [ ] Commit messages são descritivas

---

## 📞 Suporte

Encontrou algum problema na documentação?

- **Email**: falecomrenatobarros@gmail.com
- **Issues**: Abra uma issue no GitHub

---

## 🎉 Pronto!

Sua documentação está **completa, profissional e visualmente atraente**!

**Estrutura final**:
```
real_selection/
├── README.md                   (5.5K) ✨ Design rico com badges
├── docs/
│   ├── ARQUITETURA.md          (12K)  🔧 Detalhes técnicos
│   ├── CONFIGURACAO.md         (11K)  ⚙️ Setup e troubleshooting  
│   ├── VOZES.md                (7.0K) 🎤 Vozes e idiomas
│   └── DESENVOLVIMENTO.md      (11K)  👩‍💻 Contribuições
├── integrations/
│   └── hyprland_binds.conf     (2.0K) 📋 Exemplo de config
├── scripts/
│   ├── tts_wrapper.sh          (4.5K) 🎬 Wrapper comentado
│   └── tts_kill.sh             (3.0K) 🛑 Kill comentado
├── src/
│   └── real_selection/
│       └── main.py             (15K)  🐍 Código comentado
└── pyproject.toml              (2.5K) 📦 Config comentada
```

**Total**: ~72K de documentação profissional e código bem documentado! 🚀

---

<div align="center">

**Real Selection** — Copyright (C) 2025 Renato Barros  
Licenciado sob GNU GPL v3.0+

</div>
