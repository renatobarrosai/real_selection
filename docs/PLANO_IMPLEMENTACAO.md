# Plano de Implementação: TTS Seleção Primária com Streaming

## 📋 Objetivo

Criar script Python que lê texto da seleção primária do Wayland e faz TTS em streaming real usando Kokoro, português do Brasil, voz pf_dora, com arquitetura multi-threading para mínima latência.

---

## 🏗️ Arquitetura Final

```
┌─────────────────┐
│ Main Thread     │
│ - Init pipeline │
│ - Captura texto │
│ - Coordena exec │
└────────┬────────┘
         │
         ├──────────────────────┬─────────────────────┐
         ▼                      ▼                     ▼
┌─────────────────┐    ┌─────────────────┐   ┌──────────────┐
│ Thread Geração  │───▶│  Queue (FIFO)   │──▶│ Thread Audio │
│ - Processa TTS  │    │ - Thread-safe   │   │ - PyAudio    │
│ - GPU inference │    │ - Buffer chunks │   │ - Playback   │
└─────────────────┘    └─────────────────┘   └──────────────┘
```

---

## 📁 Estrutura de Arquivos

```
kokoro/
├── examples/
│   ├── ler_selecao_tts.py          # Script principal (NOVO)
│   ├── obter_selecao_primaria.py   # Já existe (reutilizar)
│   └── test_*.py                   # Scripts de teste (NOVOS)
└── logs/
    └── tts_debug.log                # Logs de debug (AUTO-CRIADO)
```

---

## 🔧 Etapas de Implementação

### **ETAPA 1: Validação de Dependências e Ambiente**

**Objetivo**: Garantir que todas as dependências estão instaladas e funcionando.

**Ações**:
1. Verificar `wl-clipboard` instalado (`wl-paste --version`)
2. Verificar `espeak-ng` instalado (`espeak-ng --version`)
3. Verificar `pyaudio` instalado e funcionando
4. Verificar PyTorch com CUDA disponível

**Teste de Validação**:
```bash
# Criar: examples/test_01_dependencias.py
python examples/test_01_dependencias.py
```

**Critério de Sucesso**:
- ✅ Todas as dependências reportam versões corretas
- ✅ CUDA disponível e detectado
- ✅ PyAudio lista dispositivos de áudio
- ✅ wl-paste executa sem erro

**Saída Esperada**:
```
✅ wl-clipboard: 2.x.x
✅ espeak-ng: 1.x
✅ pyaudio: 0.2.x
✅ CUDA: disponível (device 0: GeForce GTX 1650)
✅ Dispositivos de áudio: 3 encontrados
```

---

### **ETAPA 2: Teste de Captura de Seleção Primária**

**Objetivo**: Validar função de captura e limpeza de texto.

**Ações**:
1. Reutilizar código de `obter_selecao_primaria.py`
2. Criar teste isolado que:
   - Instrui usuário a selecionar texto
   - Captura seleção
   - Exibe texto bruto e limpo
   - Valida função `limpar_texto_para_tts()`

**Teste de Validação**:
```bash
# Criar: examples/test_02_selecao.py
# Usuário seleciona texto no browser/terminal
python examples/test_02_selecao.py
```

**Critério de Sucesso**:
- ✅ Captura texto selecionado corretamente
- ✅ Remove quebras de linha indesejadas
- ✅ Preserva parágrafos (quebras duplas)
- ✅ Retorna string limpa sem espaços múltiplos

**Saída Esperada**:
```
🔍 Selecione um texto e execute o script...
━━━ TEXTO BRUTO ━━━
"Este é um texto\ncom quebras\nde linha."

━━━ TEXTO LIMPO ━━━
"Este é um texto com quebras de linha."
✅ Limpeza bem-sucedida
```

---

### **ETAPA 3: Teste de Pipeline Kokoro + GPU**

**Objetivo**: Validar que pipeline carrega e gera áudio em português com voz pf_dora na GPU.

**Ações**:
1. Inicializar `KPipeline(lang_code='p', device='cuda')`
2. Pré-carregar voz `pf_dora`
3. Gerar áudio de teste curto
4. Salvar como WAV para validação manual
5. Medir tempo de inferência

**Teste de Validação**:
```bash
# Criar: examples/test_03_pipeline_gpu.py
python examples/test_03_pipeline_gpu.py
```

**Critério de Sucesso**:
- ✅ Pipeline inicializa na GPU sem erros
- ✅ Voz pf_dora carrega corretamente
- ✅ Áudio gerado tem qualidade esperada
- ✅ Tempo de inferência < 200ms para frase curta (~10 palavras)
- ✅ Arquivo WAV salvo e reproduzível

**Saída Esperada**:
```
🔧 Inicializando pipeline...
   Device: cuda (GeForce GTX 1650)
   Lang: pt-br (p)
   Repo: hexgrad/Kokoro-82M
✅ Pipeline carregado

🎤 Carregando voz pf_dora...
✅ Voz carregada (2.1 MB)

🔊 Gerando áudio de teste...
   Texto: "Olá, este é um teste rápido."
   Chunks gerados: 1
   Duração: 1.2s
   Tempo de inferência: 87ms
✅ Áudio salvo: test_output.wav

⚡ RTF (Real-Time Factor): 0.072 (14x mais rápido que tempo real)
```

---

### **ETAPA 4: Teste de PyAudio Streaming**

**Objetivo**: Validar playback em tempo real com PyAudio.

**Ações**:
1. Inicializar PyAudio stream (24kHz, Float32, mono)
2. Gerar áudio de teste com Kokoro
3. Tocar áudio diretamente via stream (sem salvar arquivo)
4. Validar que não há distorção/crackling

**Teste de Validação**:
```bash
# Criar: examples/test_04_pyaudio_stream.py
python examples/test_04_pyaudio_stream.py
```

**Critério de Sucesso**:
- ✅ Stream abre sem erros
- ✅ Áudio toca com qualidade esperada
- ✅ Sem buffer underruns (crackling)
- ✅ Latência perceptível < 500ms

**Saída Esperada**:
```
🔊 Inicializando PyAudio...
   Dispositivo: Built-in Audio (ID: 0)
   Rate: 24000 Hz
   Formato: Float32
   Canais: 1 (mono)
✅ Stream aberto

🎵 Gerando e tocando áudio...
   [▓▓▓▓▓▓▓▓▓▓] Chunk 1 tocando...
   [▓▓▓▓▓▓▓▓▓▓] Chunk 2 tocando...
✅ Playback concluído

🔧 Stream fechado
```

---

### **ETAPA 5: Teste de Threading com Queue**

**Objetivo**: Validar arquitetura multi-thread com fila thread-safe.

**Ações**:
1. Implementar `ProducerThread` (gera áudio → enfileira)
2. Implementar `ConsumerThread` (desenfileira → toca)
3. Usar `queue.Queue()` para comunicação
4. Usar `threading.Event()` para sinalização
5. Testar com texto médio (5-10 chunks)

**Teste de Validação**:
```bash
# Criar: examples/test_05_threading.py
python examples/test_05_threading.py
```

**Critério de Sucesso**:
- ✅ Threads iniciam e terminam corretamente
- ✅ Fila transfere dados sem perda
- ✅ Áudio toca continuamente sem gaps
- ✅ Thread de geração termina antes do playback final
- ✅ Sem race conditions ou deadlocks

**Saída Esperada**:
```
🧵 Iniciando threads...
   Producer: Thread-1 (geração de áudio)
   Consumer: Thread-2 (playback)
✅ Threads iniciadas

📊 Status da fila:
   [Producer] Chunk 1 → fila (size: 1)
   [Consumer] Chunk 1 ← fila (tocando...)
   [Producer] Chunk 2 → fila (size: 1)
   [Producer] Chunk 3 → fila (size: 2)
   [Consumer] Chunk 2 ← fila (tocando...)
   ...

✅ Producer finalizado
✅ Consumer finalizado
🔧 Threads encerradas com sucesso
```

---

### **ETAPA 6: Integração Completa com Logging**

**Objetivo**: Integrar todos os componentes com sistema de logging robusto.

**Ações**:
1. Configurar `loguru` para:
   - Console: nível INFO (mínimo)
   - Arquivo: nível DEBUG (`logs/tts_debug.log`)
   - Rotação: 10 MB por arquivo
   - Retenção: últimos 5 arquivos
2. Adicionar logs em pontos críticos:
   - Captura de seleção
   - Inicialização de pipeline
   - Início/fim de threads
   - Cada chunk gerado/tocado
   - Erros e exceções
3. Criar script integrado completo

**Teste de Validação**:
```bash
# Criar: examples/ler_selecao_tts.py (SCRIPT FINAL)
# Usuário seleciona texto
python examples/ler_selecao_tts.py
```

**Critério de Sucesso**:
- ✅ Captura seleção primária
- ✅ Limpa e valida texto
- ✅ Gera áudio em streaming
- ✅ Toca áudio sem interrupções
- ✅ Logs salvos em `logs/tts_debug.log`
- ✅ Tratamento de erros funcional
- ✅ Cleanup adequado (threads, streams, recursos)

**Saída Esperada (Console - INFO)**:
```
[12:34:56] INFO     Capturando seleção primária...
[12:34:56] INFO     Texto capturado: 145 caracteres
[12:34:56] INFO     Inicializando pipeline (GPU)...
[12:34:57] INFO     Pipeline carregado em 892ms
[12:34:57] INFO     Iniciando streaming...
[12:34:57] INFO     Thread de geração: iniciada
[12:34:57] INFO     Thread de playback: iniciada
[12:34:57] INFO     Chunk 1/3 gerado (1.2s)
[12:34:57] INFO     Chunk 1/3 tocando...
[12:34:58] INFO     Chunk 2/3 gerado (0.9s)
[12:34:58] INFO     Chunk 2/3 tocando...
[12:34:59] INFO     Chunk 3/3 gerado (1.1s)
[12:34:59] INFO     Chunk 3/3 tocando...
[12:35:01] INFO     Geração finalizada
[12:35:02] INFO     Playback finalizado
[12:35:02] INFO     Limpeza de recursos concluída
```

**Saída Esperada (Arquivo - DEBUG)**:
```
2025-11-20 12:34:56 | DEBUG | Executando wl-paste --primary
2025-11-20 12:34:56 | DEBUG | Texto bruto: "Este é um texto\ncom quebras..."
2025-11-20 12:34:56 | DEBUG | Texto limpo: "Este é um texto com quebras..."
2025-11-20 12:34:56 | DEBUG | Validando CUDA...
2025-11-20 12:34:56 | DEBUG | CUDA disponível: True (GTX 1650)
2025-11-20 12:34:56 | DEBUG | Carregando modelo hexgrad/Kokoro-82M
2025-11-20 12:34:57 | DEBUG | Modelo carregado: 328.4 MB VRAM
2025-11-20 12:34:57 | DEBUG | Carregando voz pf_dora
2025-11-20 12:34:57 | DEBUG | Voz carregada: 2.1 MB
2025-11-20 12:34:57 | DEBUG | Abrindo PyAudio stream (24kHz, Float32)
2025-11-20 12:34:57 | DEBUG | Stream aberto: device=0, latency=85ms
2025-11-20 12:34:57 | DEBUG | Iniciando ProducerThread
2025-11-20 12:34:57 | DEBUG | Iniciando ConsumerThread
2025-11-20 12:34:57 | DEBUG | [Producer] Processando chunk 1/3
2025-11-20 12:34:57 | DEBUG | [Producer] Inferência: 73ms, áudio: 28800 samples (1.2s)
2025-11-20 12:34:57 | DEBUG | [Producer] Chunk 1 → queue (size: 1)
2025-11-20 12:34:57 | DEBUG | [Consumer] Chunk 1 ← queue (size: 0)
2025-11-20 12:34:57 | DEBUG | [Consumer] Escrevendo 28800 samples no stream
...
```

---

### **ETAPA 7: Testes de Casos Extremos**

**Objetivo**: Validar robustez do script em cenários adversos.

**Ações**:
1. Testar com seleção vazia
2. Testar com texto muito longo (> 5000 chars)
3. Testar com caracteres especiais/emojis
4. Testar com GPU indisponível (forçar CPU)
5. Testar interrupção no meio (Ctrl+C)

**Teste de Validação**:
```bash
# Criar: examples/test_07_edge_cases.py
python examples/test_07_edge_cases.py
```

**Critérios de Sucesso**:
- ✅ Seleção vazia: sai graciosamente com mensagem clara
- ✅ Texto longo: trunca ou processa em partes sem crash
- ✅ Caracteres especiais: sanitiza ou pula sem erro
- ✅ GPU indisponível: fallback para CPU automaticamente
- ✅ Ctrl+C: cleanup adequado (threads, streams, recursos)

**Saída Esperada (seleção vazia)**:
```
[12:40:00] WARNING  Nenhum texto selecionado
[12:40:00] INFO     Encerrando...
```

**Saída Esperada (Ctrl+C)**:
```
[12:40:15] INFO     Chunk 2/5 tocando...
^C
[12:40:16] WARNING  Interrupção detectada (SIGINT)
[12:40:16] INFO     Parando threads...
[12:40:16] INFO     Fechando stream de áudio...
[12:40:16] INFO     Limpeza concluída
```

---

### **ETAPA 8: Documentação e Código Final**

**Objetivo**: Documentar código e criar README de uso.

**Ações**:
1. Adicionar docstrings em todas as funções/classes
2. Comentar blocos críticos do código
3. Criar README específico em `examples/README_LER_SELECAO.md`
4. Adicionar exemplos de uso
5. Documentar troubleshooting comum

**Teste de Validação**:
```bash
# Validar que README está completo
cat examples/README_LER_SELECAO.md

# Validar docstrings
python -c "import examples.ler_selecao_tts; help(examples.ler_selecao_tts)"
```

**Critério de Sucesso**:
- ✅ README com instalação, uso e troubleshooting
- ✅ Todas as funções com docstrings completas
- ✅ Código comentado em pontos não-óbvios
- ✅ Exemplos de uso claros

---

## 📊 Resumo de Deliverables

| # | Arquivo | Descrição |
|---|---------|-----------|
| 1 | `examples/test_01_dependencias.py` | Valida ambiente e deps |
| 2 | `examples/test_02_selecao.py` | Testa captura de seleção |
| 3 | `examples/test_03_pipeline_gpu.py` | Testa pipeline + GPU |
| 4 | `examples/test_04_pyaudio_stream.py` | Testa PyAudio streaming |
| 5 | `examples/test_05_threading.py` | Testa arquitetura multi-thread |
| 6 | `examples/ler_selecao_tts.py` | **SCRIPT PRINCIPAL** |
| 7 | `examples/test_07_edge_cases.py` | Testa casos extremos |
| 8 | `examples/README_LER_SELECAO.md` | Documentação de uso |

---

## 🎯 Critérios de Sucesso Global

### Funcionalidade
- ✅ Captura texto da seleção primária do Wayland
- ✅ Limpa texto adequadamente
- ✅ Gera áudio em português do Brasil com voz pf_dora
- ✅ Toca áudio em streaming real com latência mínima
- ✅ Usa GPU (CUDA) para inferência

### Performance
- ✅ Latência até primeiro som: < 500ms
- ✅ Streaming sem gaps entre chunks
- ✅ RTF < 0.15 (< 150ms para gerar 1s de áudio)
- ✅ Uso de VRAM: < 500MB
- ✅ Uso de RAM: < 300MB

### Qualidade de Código
- ✅ Código limpo e bem estruturado
- ✅ Comentários em blocos complexos
- ✅ Docstrings em todas as funções/classes
- ✅ Logging adequado (INFO no console, DEBUG em arquivo)
- ✅ Tratamento de erros robusto
- ✅ Cleanup de recursos garantido

### Robustez
- ✅ Funciona com seleções vazias (sai graciosamente)
- ✅ Funciona com textos longos (chunking automático)
- ✅ Fallback para CPU se GPU indisponível
- ✅ Interrupção segura (Ctrl+C)
- ✅ Logs auxiliam debug de problemas

---

## 🚀 Próximos Passos Após Aprovação

Após aprovação deste plano:
1. Executar **ETAPA 1** completa
2. Validar sucesso antes de prosseguir
3. Executar **ETAPA 2** completa
4. Validar sucesso antes de prosseguir
5. ... (repetir para todas as 8 etapas)

**Cada etapa só será considerada concluída após:**
- ✅ Código implementado
- ✅ Teste executado com sucesso
- ✅ Saída validada conforme especificado
- ✅ Aprovação explícita do usuário

---

## ⚠️ Notas Importantes

1. **Não pular etapas**: Cada etapa valida um componente isolado
2. **Testar antes de integrar**: Evita debug de múltiplos problemas simultaneamente
3. **Logs são essenciais**: Facilitam troubleshooting futuro
4. **Cleanup é crítico**: Threads/streams devem ser finalizados adequadamente
5. **GPU fallback**: Script deve funcionar mesmo sem CUDA (degradação graceful)

---

**Este plano está pronto para aprovação e execução.**
