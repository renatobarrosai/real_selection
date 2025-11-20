# 🎤 Vozes e Idiomas

> **Guia completo de configuração de vozes, idiomas e parâmetros do Kokoro TTS**

---

## 📑 Índice

- [Sobre o Kokoro-82M](#sobre-o-kokoro-82m)
- [Configuração Padrão](#configuração-padrão)
- [Idiomas Disponíveis](#idiomas-disponíveis)
- [Vozes por Idioma](#vozes-por-idioma)
- [Como Alterar Voz/Idioma](#como-alterar-vozidioma)
- [Parâmetros Avançados](#parâmetros-avançados)

---

## 🤖 Sobre o Kokoro-82M

**Kokoro-82M** é um modelo de TTS (Text-to-Speech) neural de código aberto desenvolvido pela **[hexgrad](https://github.com/hexgrad/kokoro)** com 82 milhões de parâmetros.

### Características

- ✅ **Multi-idioma**: Português, Inglês, Japonês, Chinês, Coreano
- ✅ **Vozes naturais**: 6-8 vozes por idioma (masculinas e femininas)
- ✅ **Aceleração GPU**: Otimizado para CUDA
- ✅ **Open source**: Modelo e código disponíveis publicamente

---

## ⚙️ Configuração Padrão

O **Real Selection** está configurado para **português brasileiro, voz feminina**:

```python
# src/real_selection/main.py (linha ~140)
pipeline = KPipeline(
    lang_code='p',              # Português BR
    repo_id='hexgrad/Kokoro-82M',
    device='cuda'               # GPU (fallback: CPU)
)

pipeline.load_voice('pf_dora')  # Voz feminina natural
```

### Parâmetros na síntese

```python
# src/real_selection/main.py (linha ~300)
for result in pipeline(
    texto, 
    voice='pf_dora',   # Voz
    speed=1.0          # Velocidade (0.5 = metade, 2.0 = dobro)
):
    # ...
```

---

## 🌍 Idiomas Disponíveis

| Idioma | `lang_code` | Descrição |
|--------|-------------|-----------|
| 🇧🇷 Português BR | `'p'` | Português brasileiro (padrão) |
| 🇺🇸 Inglês Americano | `'a'` | American English |
| 🇬🇧 Inglês Britânico | `'b'` | British English |
| 🇯🇵 Japonês | `'j'` | 日本語 |
| 🇨🇳 Chinês | `'z'` | 中文 (Mandarim) |
| 🇰🇷 Coreano | `'k'` | 한국어 |

---

## 🎭 Vozes por Idioma

### 🇧🇷 Português Brasileiro (`lang_code='p'`)

| ID da Voz | Gênero | Descrição |
|-----------|--------|-----------|
| `pf_dora` | 👩 Feminina | Natural, clara — **padrão do projeto** |
| `pm_paulo` | 👨 Masculina | Tom médio, profissional |
| `pf_clara` | 👩 Feminina | Tom mais jovem |
| `pm_rafael` | 👨 Masculina | Tom grave |

> **💡 Dica**: Teste diferentes vozes para encontrar a que melhor se adequa ao seu uso.

### 🇺🇸 Inglês Americano (`lang_code='a'`)

| ID da Voz | Gênero | Descrição |
|-----------|--------|-----------|
| `af_bella` | 👩 Feminina | Clara, profissional |
| `am_adam` | 👨 Masculina | Tom médio |
| `af_sarah` | 👩 Feminina | Tom jovem |
| `am_michael` | 👨 Masculina | Tom grave |

### 🇬🇧 Inglês Britânico (`lang_code='b'`)

| ID da Voz | Gênero | Descrição |
|-----------|--------|-----------|
| `bf_emma` | 👩 Feminina | Sotaque RP (Received Pronunciation) |
| `bm_george` | 👨 Masculina | Tom profissional |

### 🇯🇵 Japonês (`lang_code='j'`)

| ID da Voz | Gênero | Descrição |
|-----------|--------|-----------|
| `jf_yuki` | 👩 Feminina | Natural, standard |
| `jm_takeshi` | 👨 Masculina | Tom médio |

> **📝 Nota**: Para caracteres japoneses, certifique-se de que seu sistema tem fontes adequadas instaladas.

---

## 🔧 Como Alterar Voz/Idioma

### Método 1: Editar código diretamente

Abra `src/real_selection/main.py` e modifique:

```python
# Linha ~140 - Alterar idioma
pipeline = KPipeline(
    lang_code='a',  # Mude para 'a' (inglês americano), 'j' (japonês), etc.
    repo_id='hexgrad/Kokoro-82M',
    device='cuda'
)

# Linha ~144 - Alterar voz
pipeline.load_voice('af_bella')  # Voz feminina americana

# Linha ~300 - Confirmar uso
for result in pipeline(texto, voice='af_bella', speed=1.0):
    # ...
```

### Método 2: Variáveis de ambiente (futuro)

> **🚧 Em desenvolvimento**: Planejamos adicionar configuração via arquivo `.env` ou argumentos CLI.

```bash
# Exemplo (ainda não implementado)
KOKORO_LANG=a KOKORO_VOICE=af_bella real_selection
```

---

## ⚡ Parâmetros Avançados

### Velocidade da fala

Ajuste o parâmetro `speed` na linha ~300:

```python
# Mais devagar (útil para aprendizado)
pipeline(texto, voice='pf_dora', speed=0.75)

# Normal
pipeline(texto, voice='pf_dora', speed=1.0)

# Mais rápido (útil para conteúdo longo)
pipeline(texto, voice='pf_dora', speed=1.5)
```

> **⚠️ Aviso**: Valores muito extremos (< 0.5 ou > 2.0) podem degradar a qualidade do áudio.

### Device (GPU vs CPU)

Por padrão, o código tenta usar CUDA automaticamente:

```python
# Linha ~245
if torch.cuda.is_available():
    device = 'cuda'  # GPU (rápido)
else:
    device = 'cpu'   # Fallback (mais lento)
```

Para forçar CPU (útil para debug):

```python
pipeline = KPipeline(
    lang_code='p',
    repo_id='hexgrad/Kokoro-82M',
    device='cpu'  # Força CPU
)
```

---

## 🧪 Testando Vozes

Crie um script simples para testar diferentes vozes:

```python
#!/usr/bin/env python3
from kokoro import KPipeline

# Inicializa pipeline
pipeline = KPipeline(lang_code='p', repo_id='hexgrad/Kokoro-82M', device='cuda')

# Testa vozes brasileiras
vozes = ['pf_dora', 'pm_paulo', 'pf_clara', 'pm_rafael']
texto = "Olá, esta é uma demonstração de voz."

for voz in vozes:
    print(f"Testando voz: {voz}")
    pipeline.load_voice(voz)
    
    for result in pipeline(texto, voice=voz, speed=1.0):
        if result.audio:
            # Salvar ou reproduzir áudio
            pass
```

---

## 📚 Recursos Adicionais

### Documentação Oficial Kokoro

- 💻 **Repositório GitHub**: [github.com/hexgrad/Kokoro](https://github.com/hexgrad/Kokoro)
- 📦 **Modelo HuggingFace**: [huggingface.co/hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)
- 🎭 **Lista completa de vozes**: [VOICES.md](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md)
- 📚 **Guia de uso (Asimov Academy)**: [Kokoro-TTS - Guia de uso](https://github.com/asimov-academy/Kokoro-TTS---Guia-de-uso)

### Real Selection

- 📐 **Arquitetura**: [Como o sistema funciona internamente](ARQUITETURA.md)
- ⚙️ **Configuração**: [Setup e troubleshooting](CONFIGURACAO.md)
- 👩‍💻 **Desenvolvimento**: [Como contribuir](DESENVOLVIMENTO.md)

---

## 🐛 Problemas Comuns

### Voz não encontrada

```
Error: Voice 'xyz' not found
```

**Solução**: Verifique se a voz está disponível para o idioma escolhido. Use `pipeline.list_voices()` para listar vozes válidas.

### Áudio de baixa qualidade

**Causas possíveis**:
- Velocidade muito alta/baixa
- CPU em vez de GPU (mais lento = pode truncar áudio)
- Texto muito longo sem pausas

**Solução**: Ajuste `speed` para 1.0, verifique GPU, e adicione pontuação no texto.

---

## 🤝 Contribuindo

Encontrou uma voz melhor? Quer adicionar suporte a novos idiomas?  
Veja **[DESENVOLVIMENTO.md](DESENVOLVIMENTO.md)** para instruções de contribuição.

---

<div align="center">

**[⬆ Voltar ao README](../README.md)** | **[📐 Arquitetura](ARQUITETURA.md)** | **[⚙️ Configuração](CONFIGURACAO.md)**

---

**Real Selection** — Copyright (C) 2025 Renato Barros  
Licenciado sob GNU GPL v3.0+

</div>
