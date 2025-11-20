#!/usr/bin/env python3
"""
Real Selection - Síntese de voz em tempo real a partir de texto selecionado
Copyright (C) 2025 Renato Barros

Este programa é software livre: você pode redistribuí-lo e/ou modificá-lo
sob os termos da GNU General Public License conforme publicada pela
Free Software Foundation, versão 3 da Licença, ou (a seu critério)
qualquer versão posterior.

Este programa é distribuído na esperança de que seja útil, mas SEM QUALQUER
GARANTIA; sem mesmo a garantia implícita de COMERCIALIZAÇÃO ou ADEQUAÇÃO A UM
PROPÓSITO ESPECÍFICO. Consulte a GNU General Public License para mais detalhes.

Você deve ter recebido uma cópia da GNU General Public License junto com este
programa. Caso contrário, consulte <https://www.gnu.org/licenses/>.
"""

"""
Script principal que captura texto da seleção primária do Wayland e sintetiza
voz em português brasileiro usando Kokoro TTS com streaming em tempo real.

Arquitetura:
- Producer thread: gera chunks de áudio via Kokoro (GPU)
- Consumer thread: reproduz chunks via PyAudio
- Queue de até 10 chunks para buffering mínimo

Dependências externas:
- wl-clipboard: captura seleção primária
- CUDA: aceleração GPU (fallback para CPU)
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
# LOGGING
# ============================================================================

def configurar_logging():
    """
    Console: INFO (mensagens relevantes para usuário)
    Arquivo: DEBUG (troubleshooting detalhado)
    Rotação: 10 MB, últimos 5 arquivos compactados
    """
    logger.remove()

    # Console: apenas o essencial
    logger.add(
        sys.stderr,
        format="<green>[{time:HH:mm:ss}]</green> <level>{level:8}</level> | <level>{message}</level>",
        level="INFO",
        colorize=True
    )

    # Arquivo: tudo para debug posterior
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
    Captura via wl-paste --primary (seleção do mouse no Wayland).
    Timeout de 2s previne travamentos se clipboard não responder.
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
        return texto

    except FileNotFoundError:
        logger.error("wl-clipboard não está instalado")
        logger.error("Instale com: sudo pacman -S wl-clipboard")
        return None

    except subprocess.TimeoutExpired:
        logger.error("Timeout ao capturar seleção")
        return None

    except subprocess.CalledProcessError:
        # Seleção vazia não é erro
        logger.debug("Seleção primária vazia")
        return ""

    except Exception as e:
        logger.exception(f"Erro inesperado ao capturar seleção: {e}")
        return None


def limpar_texto_para_tts(texto: str) -> Optional[str]:
    """
    Remove quebras de linha indesejadas (PDFs, terminal) mas preserva parágrafos.
    
    Estratégia:
    - Quebra simples (\n) → espaço (junta linhas do mesmo parágrafo)
    - Quebra dupla (\n\n) → mantém (separação entre parágrafos)
    """
    if not texto:
        return None

    logger.debug("Limpando texto para TTS")
    logger.debug(f"Original: {len(texto)} chars, {texto.count(chr(10))} quebras")

    # Substitui \n isolado por espaço, mantém \n\n
    texto_limpo = re.sub(r'(?<!\n)\n(?!\n)', ' ', texto)
    
    # Remove espaços múltiplos (mas não quebras)
    texto_limpo = re.sub(r'[ \t]+', ' ', texto_limpo)
    texto_limpo = texto_limpo.strip()

    logger.debug(f"Limpo: {len(texto_limpo)} chars, {texto_limpo.count(chr(10))} quebras")

    return texto_limpo if texto_limpo else None


# ============================================================================
# THREADS DE PRODUÇÃO E CONSUMO
# ============================================================================

class AudioProducerThread(threading.Thread):
    """
    Gera áudio via Kokoro e enfileira chunks para reprodução.
    Non-daemon: precisa finalizar corretamente para enviar sinal de término.
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
        """Executa pipeline Kokoro e enfileira chunks conforme são gerados."""
        try:
            logger.debug(f"[Producer] Thread iniciada")
            tempo_inicio = time.perf_counter()

            for i, result in enumerate(self.pipeline(self.texto, voice=self.voz, speed=self.speed)):
                if result.audio is not None:
                    self.num_chunks += 1
                    
                    # Kokoro retorna torch.Tensor, convertemos para numpy float32
                    chunk = result.audio.cpu().numpy().astype(np.float32)

                    duracao = len(chunk) / 24000
                    tamanho_fila = self.audio_queue.qsize()

                    logger.debug(f"[Producer] Chunk {self.num_chunks}: {len(chunk)} samples ({duracao:.2f}s)")
                    logger.debug(f"[Producer] Fila: {tamanho_fila} chunks aguardando")
                    logger.info(f"Chunk {self.num_chunks} gerado ({duracao:.2f}s)")

                    self.audio_queue.put(chunk)

            # None sinaliza fim para consumer
            self.audio_queue.put(None)

            tempo_total = (time.perf_counter() - tempo_inicio) * 1000
            logger.debug(f"[Producer] Finalizado: {self.num_chunks} chunks em {tempo_total:.0f}ms")
            logger.info(f"Geração finalizada: {self.num_chunks} chunks")

        except Exception as e:
            self.erro = e
            logger.exception(f"[Producer] Erro: {e}")
            # Envia None para desbloquear consumer mesmo com erro
            self.audio_queue.put(None)


class AudioConsumerThread(threading.Thread):
    """
    Desenfileira e reproduz chunks via PyAudio.
    Bloqueia em queue.get() até ter dados ou receber sinal de término (None).
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
        """Reproduz chunks conforme ficam disponíveis na fila."""
        stream = None

        try:
            logger.debug("[Consumer] Thread iniciada")

            # TODO: Remover hardcoded output_device_index=9
            # Device atual é específico do ambiente de dev (Arch + Hyprland).
            # Em produção, deve usar device padrão do sistema ou ser configurável.
            stream = self.pyaudio_instance.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=24000,
                output=True,
                output_device_index=9,  # FIXME: hardcoded
                frames_per_buffer=2048
            )

            logger.debug("[Consumer] Stream de áudio aberto")
            logger.info("Iniciando playback...")

            while True:
                # Bloqueia até ter chunk disponível
                chunk = self.audio_queue.get()

                if chunk is None:
                    logger.debug("[Consumer] Sinal de término recebido")
                    break

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
# INICIALIZAÇÃO E PROCESSAMENTO
# ============================================================================

def inicializar_pipeline() -> Optional[KPipeline]:
    """
    Carrega modelo Kokoro (82M parâmetros) e voz pf_dora.
    Prefere CUDA se disponível, fallback para CPU.
    """
    logger.info("Inicializando pipeline...")
    logger.debug("Lang: pt-br (p), Voz: pf_dora, Repo: hexgrad/Kokoro-82M")

    cuda_disponivel = torch.cuda.is_available()

    if cuda_disponivel:
        device = 'cuda'
        gpu_nome = torch.cuda.get_device_name(0)
        logger.debug(f"CUDA disponível: {gpu_nome}")
    else:
        device = 'cpu'
        logger.warning("CUDA não disponível, usando CPU (mais lento)")

    try:
        tempo_inicio = time.perf_counter()

        pipeline = KPipeline(
            lang_code='p',  # português
            repo_id='hexgrad/Kokoro-82M',
            device=device
        )

        tempo_init = (time.perf_counter() - tempo_inicio) * 1000
        logger.debug(f"Pipeline inicializado em {tempo_init:.0f}ms")

        # Pré-carrega voz para evitar latência no primeiro uso
        logger.debug("Carregando voz pf_dora...")
        pipeline.load_voice('pf_dora')

        logger.info(f"Pipeline pronto (device: {device})")
        return pipeline

    except Exception as e:
        logger.exception(f"Erro ao inicializar pipeline: {e}")
        return None


def processar_tts(texto: str, pipeline: KPipeline) -> bool:
    """
    Orquestra producer/consumer threads para streaming.
    
    Consumer inicia primeiro para evitar perda de chunks iniciais.
    Delay de 100ms garante que stream esteja pronto antes de producer começar.
    """
    logger.info(f"Processando texto: {len(texto)} caracteres")

    # Fila limitada a 10 chunks previne uso excessivo de memória
    audio_queue = queue.Queue(maxsize=10)
    p = pyaudio.PyAudio()

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

    logger.debug("Iniciando threads de produção e consumo")
    tempo_inicio = time.perf_counter()

    # Consumer primeiro, depois producer
    consumer.start()
    time.sleep(0.1)
    producer.start()

    # Aguarda ambas finalizarem
    producer.join()
    consumer.join()

    tempo_total = (time.perf_counter() - tempo_inicio) * 1000
    p.terminate()

    # Verifica se houve erros
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


# Pipeline global para reutilização entre chamadas
# (evita recarregar modelo a cada execução)
_pipeline_global = None


def cleanup_handler(signum, frame):
    """Handler para Ctrl+C - encerra graciosamente."""
    logger.warning("Interrupção detectada (SIGINT)")
    logger.info("Encerrando...")
    sys.exit(130)


def main():
    """Fluxo principal: captura → limpa → sintetiza → reproduz."""
    global _pipeline_global

    configurar_logging()
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

    # 3. Inicializa pipeline (reutiliza se já carregado)
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
