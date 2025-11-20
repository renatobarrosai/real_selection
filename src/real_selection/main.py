#!/usr/bin/env python3
"""
TTS de Seleção Primária com Streaming Real

Script principal que lê texto da seleção primária do Wayland
e realiza síntese de voz em português do Brasil com streaming
em tempo real usando arquitetura multi-threading.

Características:
- Captura seleção primária (wl-paste --primary)
- Limpa texto automaticamente
- Gera áudio com Kokoro (voz pf_dora)
- Usa GPU (CUDA) para inferência rápida
- Streaming com latência mínima (threading)
- Logging em dois níveis (INFO console, DEBUG arquivo)

Uso:
1. Selecione um texto em qualquer aplicativo
2. Execute: python ler_selecao_tts.py
3. O áudio será tocado imediatamente

Autor: Claude Code
Data: 2025-11-20
"""

import sys
import os
import subprocess
import re
import time
import threading
import queue
import signal
from pathlib import Path
from typing import Optional

import numpy as np
import pyaudio
import torch
from loguru import logger
from kokoro import KPipeline


# ============================================================================
# CONFIGURAÇÃO DE LOGGING
# ============================================================================

def configurar_logging():
    """
    Configura sistema de logging com loguru.

    - Console: nível INFO (mensagens importantes)
    - Arquivo: nível DEBUG (tudo, para troubleshooting)
    - Rotação: 10 MB por arquivo
    - Retenção: últimos 5 arquivos
    """
    # Remove handler padrão
    logger.remove()

    # Handler para console (INFO e acima)
    logger.add(
        sys.stderr,
        format="<green>[{time:HH:mm:ss}]</green> <level>{level:8}</level> | <level>{message}</level>",
        level="INFO",
        colorize=True
    )

    # Handler para arquivo (DEBUG e acima)
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    logger.add(
        log_dir / "tts_debug.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:8} | {name}:{line} | {message}",
        level="DEBUG",
        rotation="10 MB",
        retention=5,
        compression="zip"
    )

    logger.debug("Sistema de logging configurado")


# ============================================================================
# CAPTURA E LIMPEZA DE TEXTO
# ============================================================================

def obter_selecao_primaria() -> Optional[str]:
    """
    Captura texto da seleção primária do Wayland.

    Returns:
        Optional[str]: Texto selecionado ou None se erro
    """
    logger.debug("Executando wl-paste --primary")

    try:
        texto = subprocess.check_output(
            ["wl-paste", "--primary"],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=2
        )

        texto = texto.strip()
        logger.debug(f"Texto capturado: {len(texto)} caracteres")
        logger.debug(f"Primeiros 100 chars: {repr(texto[:100])}")

        return texto

    except FileNotFoundError:
        logger.error("wl-clipboard não está instalado")
        logger.error("Instale com: sudo pacman -S wl-clipboard")
        return None

    except subprocess.TimeoutExpired:
        logger.error("Timeout ao capturar seleção")
        return None

    except subprocess.CalledProcessError:
        logger.debug("Seleção primária vazia")
        return ""

    except Exception as e:
        logger.exception(f"Erro inesperado ao capturar seleção: {e}")
        return None


def limpar_texto_para_tts(texto: str) -> Optional[str]:
    """
    Limpa texto para síntese de voz.

    Remove quebras de linha de PDFs/terminais mas preserva parágrafos.

    Args:
        texto: Texto bruto

    Returns:
        Optional[str]: Texto limpo ou None se vazio
    """
    if not texto:
        return None

    logger.debug("Limpando texto para TTS")
    logger.debug(f"Texto original: {len(texto)} chars, {texto.count(chr(10))} quebras de linha")

    # 1. Substitui quebras simples por espaço (preserva quebras duplas)
    texto_limpo = re.sub(r'(?<!\n)\n(?!\n)', ' ', texto)

    # 2. Remove espaços múltiplos (mas não quebras de linha)
    texto_limpo = re.sub(r'[ \t]+', ' ', texto_limpo)

    # 3. Remove espaços no início e fim
    texto_limpo = texto_limpo.strip()

    logger.debug(f"Texto limpo: {len(texto_limpo)} chars, {texto_limpo.count(chr(10))} quebras de linha")

    return texto_limpo if texto_limpo else None


# ============================================================================
# THREADS DE PRODUÇÃO E CONSUMO
# ============================================================================

class AudioProducerThread(threading.Thread):
    """
    Thread que gera áudio com Kokoro e enfileira chunks.
    """

    def __init__(
        self,
        texto: str,
        audio_queue: queue.Queue,
        pipeline: KPipeline,
        voz: str = 'pf_dora',
        speed: float = 1.0
    ):
        super().__init__(name="AudioProducer", daemon=False)
        self.texto = texto
        self.audio_queue = audio_queue
        self.pipeline = pipeline
        self.voz = voz
        self.speed = speed
        self.erro = None
        self.num_chunks = 0

    def run(self):
        """
        Executa geração de áudio.
        """
        try:
            logger.debug(f"[Producer] Thread iniciada")
            logger.debug(f"[Producer] Texto: {self.texto[:100]}...")

            tempo_inicio = time.perf_counter()

            # Gera chunks
            for i, result in enumerate(self.pipeline(self.texto, voice=self.voz, speed=self.speed)):
                if result.audio is not None:
                    self.num_chunks += 1
                    chunk = result.audio.cpu().numpy().astype(np.float32)

                    duracao = len(chunk) / 24000
                    tamanho_fila = self.audio_queue.qsize()

                    logger.debug(f"[Producer] Chunk {self.num_chunks}: {len(chunk)} samples ({duracao:.2f}s)")
                    logger.debug(f"[Producer] Fila: {tamanho_fila} chunks aguardando")
                    logger.info(f"Chunk {self.num_chunks} gerado ({duracao:.2f}s)")

                    # Enfileira
                    self.audio_queue.put(chunk)

            # Sinaliza fim
            self.audio_queue.put(None)

            tempo_total = (time.perf_counter() - tempo_inicio) * 1000
            logger.debug(f"[Producer] Finalizado: {self.num_chunks} chunks em {tempo_total:.0f}ms")
            logger.info(f"Geração finalizada: {self.num_chunks} chunks")

        except Exception as e:
            self.erro = e
            logger.exception(f"[Producer] Erro: {e}")
            # Envia None para desbloquear consumer
            self.audio_queue.put(None)


class AudioConsumerThread(threading.Thread):
    """
    Thread que desenfileira e toca chunks de áudio.
    """

    def __init__(
        self,
        audio_queue: queue.Queue,
        pyaudio_instance: pyaudio.PyAudio
    ):
        super().__init__(name="AudioConsumer", daemon=False)
        self.audio_queue = audio_queue
        self.pyaudio_instance = pyaudio_instance
        self.erro = None
        self.chunks_tocados = 0

    def run(self):
        """
        Executa playback de chunks.
        """
        stream = None

        try:
            logger.debug("[Consumer] Thread iniciada")

            # Abre stream
            stream = self.pyaudio_instance.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=24000,
                output=True,
                output_device_index = 9,
                frames_per_buffer=2048
            )

            logger.debug("[Consumer] Stream de áudio aberto")
            logger.info("Iniciando playback...")

            while True:
                # Desenfileira (bloqueia se vazio)
                chunk = self.audio_queue.get()

                # None = fim
                if chunk is None:
                    logger.debug("[Consumer] Sinal de término recebido")
                    break

                # Toca
                self.chunks_tocados += 1
                duracao = len(chunk) / 24000

                logger.debug(f"[Consumer] Tocando chunk {self.chunks_tocados} ({duracao:.2f}s)")

                stream.write(chunk.tobytes())

            logger.debug(f"[Consumer] Finalizado: {self.chunks_tocados} chunks tocados")
            logger.info(f"Playback finalizado: {self.chunks_tocados} chunks")

        except Exception as e:
            self.erro = e
            logger.exception(f"[Consumer] Erro: {e}")

        finally:
            if stream:
                try:
                    stream.stop_stream()
                    stream.close()
                    logger.debug("[Consumer] Stream fechado")
                except:
                    pass


# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def inicializar_pipeline() -> Optional[KPipeline]:
    """
    Inicializa pipeline Kokoro com GPU.

    Returns:
        Optional[KPipeline]: Pipeline ou None se erro
    """
    logger.info("Inicializando pipeline...")
    logger.debug("Lang: pt-br (p), Voz: pf_dora, Repo: hexgrad/Kokoro-82M")

    # Verifica CUDA
    cuda_disponivel = torch.cuda.is_available()

    if cuda_disponivel:
        device = 'cuda'
        gpu_nome = torch.cuda.get_device_name(0)
        logger.debug(f"CUDA disponível: {gpu_nome}")
    else:
        device = 'cpu'
        logger.warning("CUDA não disponível, usando CPU (mais lento)")

    # Inicializa
    try:
        tempo_inicio = time.perf_counter()

        pipeline = KPipeline(
            lang_code='p',
            repo_id='hexgrad/Kokoro-82M',
            device=device
        )

        tempo_init = (time.perf_counter() - tempo_inicio) * 1000
        logger.debug(f"Pipeline inicializado em {tempo_init:.0f}ms")

        # Pré-carrega voz
        logger.debug("Carregando voz pf_dora...")
        pipeline.load_voice('pf_dora')

        logger.info(f"Pipeline pronto (device: {device})")
        return pipeline

    except Exception as e:
        logger.exception(f"Erro ao inicializar pipeline: {e}")
        return None


def processar_tts(texto: str, pipeline: KPipeline) -> bool:
    """
    Processa TTS com streaming em tempo real.

    Args:
        texto: Texto limpo para síntese
        pipeline: Pipeline Kokoro inicializado

    Returns:
        bool: True se sucesso, False se erro
    """
    logger.info(f"Processando texto: {len(texto)} caracteres")
    logger.debug(f"Texto completo: {texto[:200]}...")

    # Cria fila e PyAudio
    audio_queue = queue.Queue(maxsize=10)
    p = pyaudio.PyAudio()

    # Cria threads
    producer = AudioProducerThread(
        texto=texto,
        audio_queue=audio_queue,
        pipeline=pipeline,
        voz='pf_dora',
        speed=1.0
    )

    consumer = AudioConsumerThread(
        audio_queue=audio_queue,
        pyaudio_instance=p
    )

    # Inicia threads
    logger.debug("Iniciando threads de produção e consumo")
    tempo_inicio = time.perf_counter()

    consumer.start()
    time.sleep(0.1)  # Pequeno delay para consumer estar pronto
    producer.start()

    # Aguarda conclusão
    producer.join()
    consumer.join()

    tempo_total = (time.perf_counter() - tempo_inicio) * 1000

    # Termina PyAudio
    p.terminate()

    # Verifica erros
    if producer.erro or consumer.erro:
        logger.error("Erros durante processamento")
        if producer.erro:
            logger.error(f"Producer: {producer.erro}")
        if consumer.erro:
            logger.error(f"Consumer: {consumer.erro}")
        return False

    logger.info(f"Processamento concluído em {tempo_total/1000:.1f}s")
    logger.debug(f"Chunks gerados: {producer.num_chunks}, Chunks tocados: {consumer.chunks_tocados}")

    return consumer.chunks_tocados == producer.num_chunks


# Variável global para pipeline (reutilização)
_pipeline_global = None


def cleanup_handler(signum, frame):
    """
    Handler para sinais de interrupção (Ctrl+C).
    """
    logger.warning("Interrupção detectada (SIGINT)")
    logger.info("Encerrando...")
    sys.exit(130)


def main():
    """
    Função principal do script.
    """
    global _pipeline_global

    # Configura logging
    configurar_logging()

    # Configura handler de sinais
    signal.signal(signal.SIGINT, cleanup_handler)

    logger.info("=" * 60)
    logger.info("TTS de Seleção Primária - Kokoro Streaming")
    logger.info("=" * 60)

    # 1. Captura seleção
    logger.info("Capturando seleção primária...")
    texto_bruto = obter_selecao_primaria()

    if texto_bruto is None:
        logger.error("Erro ao capturar seleção")
        return 1

    if not texto_bruto:
        logger.warning("Nenhum texto selecionado")
        return 0

    logger.info(f"Texto capturado: {len(texto_bruto)} caracteres")

    # 2. Limpa texto
    logger.info("Limpando texto...")
    texto_limpo = limpar_texto_para_tts(texto_bruto)

    if not texto_limpo:
        logger.warning("Texto vazio após limpeza")
        return 0

    logger.info(f"Texto limpo: {len(texto_limpo)} caracteres")

    # 3. Inicializa pipeline (reutiliza se já existir)
    if _pipeline_global is None:
        _pipeline_global = inicializar_pipeline()

        if _pipeline_global is None:
            logger.error("Falha ao inicializar pipeline")
            return 1

    # 4. Processa TTS
    logger.info("Iniciando síntese de voz...")
    sucesso = processar_tts(texto_limpo, _pipeline_global)

    if sucesso:
        logger.info("Concluído com sucesso!")
        return 0
    else:
        logger.error("Erro durante processamento")
        return 1


if __name__ == "__main__":
    try:
        codigo_saida = main()
        sys.exit(codigo_saida)
    except Exception as e:
        logger.exception(f"Erro fatal: {e}")
        sys.exit(1)
