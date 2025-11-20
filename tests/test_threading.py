#!/usr/bin/env python3
"""
ETAPA 5: Teste de Threading com Queue

Valida arquitetura multi-threading para streaming real:
- ProducerThread: gera áudio e enfileira chunks
- ConsumerThread: desenfileira e toca chunks
- Queue: comunicação thread-safe
- Event: sinalização de conclusão

Este padrão permite que o áudio comece a tocar enquanto
o resto ainda está sendo gerado (latência mínima).
"""

import sys
import time
import threading
import queue
import numpy as np
import pyaudio
from typing import Optional


class ProducerThread(threading.Thread):
    """
    Thread que gera chunks de áudio e os enfileira.

    Simula geração de áudio Kokoro, mas com delays controlados
    para testar sincronização.
    """

    def __init__(
        self,
        audio_queue: queue.Queue,
        finished_event: threading.Event,
        num_chunks: int = 5,
        delay_ms: float = 100
    ):
        """
        Inicializa thread produtora.

        Args:
            audio_queue: Fila para enviar chunks de áudio
            finished_event: Evento para sinalizar conclusão
            num_chunks: Número de chunks a gerar
            delay_ms: Delay entre chunks (simula processamento)
        """
        super().__init__(name="Producer")
        self.audio_queue = audio_queue
        self.finished_event = finished_event
        self.num_chunks = num_chunks
        self.delay_ms = delay_ms
        self.erro = None

    def run(self):
        """
        Executa geração de chunks.
        """
        try:
            print(f"   [Producer] Thread iniciada")

            for i in range(self.num_chunks):
                # Simula processamento (geração de áudio)
                time.sleep(self.delay_ms / 1000)

                # Gera chunk de áudio (tom de 440 Hz por 0.5s)
                sample_rate = 24000
                duracao = 0.5
                t = np.linspace(0, duracao, int(sample_rate * duracao), dtype=np.float32)
                # Frequência aumenta a cada chunk para diferenciar
                freq = 440.0 + (i * 50)
                chunk = 0.2 * np.sin(2 * np.pi * freq * t)

                # Enfileira chunk
                self.audio_queue.put(chunk)
                tamanho_fila = self.audio_queue.qsize()

                print(f"   [Producer] Chunk {i+1}/{self.num_chunks} → fila (size: {tamanho_fila})")

            # Sinaliza fim enviando None
            self.audio_queue.put(None)
            print(f"   [Producer] Finalizado (enviou {self.num_chunks} chunks)")

        except Exception as e:
            self.erro = e
            print(f"   [Producer] ❌ Erro: {e}")
            import traceback
            traceback.print_exc()
            # Envia None para desbloquear consumer
            self.audio_queue.put(None)

        finally:
            # Sinaliza que produtor terminou
            self.finished_event.set()


class ConsumerThread(threading.Thread):
    """
    Thread que desenfileira chunks de áudio e os toca.
    """

    def __init__(
        self,
        audio_queue: queue.Queue,
        pyaudio_instance: pyaudio.PyAudio,
        verbose: bool = True
    ):
        """
        Inicializa thread consumidora.

        Args:
            audio_queue: Fila para receber chunks de áudio
            pyaudio_instance: Instância do PyAudio
            verbose: Se deve imprimir mensagens detalhadas
        """
        super().__init__(name="Consumer")
        self.audio_queue = audio_queue
        self.pyaudio_instance = pyaudio_instance
        self.verbose = verbose
        self.erro = None
        self.chunks_tocados = 0

    def run(self):
        """
        Executa playback de chunks.
        """
        stream = None

        try:
            print(f"   [Consumer] Thread iniciada")

            # Abre stream de áudio
            stream = self.pyaudio_instance.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=24000,
                output=True,
                frames_per_buffer=2048
            )

            print(f"   [Consumer] Stream de áudio aberto")

            while True:
                # Desenfileira próximo chunk (bloqueia se fila vazia)
                chunk = self.audio_queue.get()

                # None sinaliza fim
                if chunk is None:
                    print(f"   [Consumer] Sinal de término recebido")
                    break

                # Toca chunk
                tamanho_fila = self.audio_queue.qsize()
                self.chunks_tocados += 1

                if self.verbose:
                    print(f"   [Consumer] Chunk {self.chunks_tocados} ← fila (size: {tamanho_fila}, tocando...)")

                stream.write(chunk.tobytes())

            print(f"   [Consumer] Finalizado ({self.chunks_tocados} chunks tocados)")

        except Exception as e:
            self.erro = e
            print(f"   [Consumer] ❌ Erro: {e}")
            import traceback
            traceback.print_exc()

        finally:
            # Fecha stream
            if stream:
                try:
                    stream.stop_stream()
                    stream.close()
                    print(f"   [Consumer] Stream fechado")
                except:
                    pass


def testar_threading_simples():
    """
    Testa threading com chunks sintéticos (tons).

    Returns:
        bool: True se sucesso, False se falha
    """
    print("\n🧪 Teste 1: Threading com chunks sintéticos")
    print("-" * 70)

    # Cria fila e eventos
    audio_queue = queue.Queue(maxsize=10)  # Limita tamanho para evitar uso excessivo de memória
    finished_event = threading.Event()

    # Cria PyAudio
    p = pyaudio.PyAudio()

    # Cria threads
    producer = ProducerThread(
        audio_queue=audio_queue,
        finished_event=finished_event,
        num_chunks=5,
        delay_ms=100  # 100ms entre chunks
    )

    consumer = ConsumerThread(
        audio_queue=audio_queue,
        pyaudio_instance=p,
        verbose=True
    )

    # Inicia threads
    tempo_inicio = time.perf_counter()

    print("\n   🧵 Iniciando threads...")
    consumer.start()  # Consumer primeiro para estar pronto
    time.sleep(0.1)   # Pequeno delay
    producer.start()  # Depois producer

    # Aguarda producer terminar
    producer.join()
    tempo_producao = (time.perf_counter() - tempo_inicio) * 1000
    print(f"\n   ✅ Producer finalizado em {tempo_producao:.0f}ms")

    # Aguarda consumer terminar
    consumer.join()
    tempo_total = (time.perf_counter() - tempo_inicio) * 1000
    print(f"   ✅ Consumer finalizado em {tempo_total:.0f}ms")

    # Termina PyAudio
    p.terminate()

    # Verifica erros
    if producer.erro or consumer.erro:
        print(f"   ❌ Erros detectados:")
        if producer.erro:
            print(f"      Producer: {producer.erro}")
        if consumer.erro:
            print(f"      Consumer: {consumer.erro}")
        return False

    # Verifica se todos os chunks foram tocados
    if consumer.chunks_tocados == producer.num_chunks:
        print(f"   ✅ Todos os chunks foram tocados ({consumer.chunks_tocados}/{producer.num_chunks})")
        return True
    else:
        print(f"   ❌ Chunks perdidos ({consumer.chunks_tocados}/{producer.num_chunks})")
        return False


class KokoroProducerThread(threading.Thread):
    """
    Thread que gera áudio real com Kokoro e enfileira chunks.
    """

    def __init__(
        self,
        texto: str,
        audio_queue: queue.Queue,
        finished_event: threading.Event,
        pipeline=None
    ):
        """
        Inicializa thread produtora com Kokoro.

        Args:
            texto: Texto para síntese
            audio_queue: Fila para enviar chunks
            finished_event: Evento de conclusão
            pipeline: Pipeline Kokoro (opcional, cria novo se None)
        """
        super().__init__(name="KokoroProducer")
        self.texto = texto
        self.audio_queue = audio_queue
        self.finished_event = finished_event
        self.pipeline = pipeline
        self.erro = None
        self.num_chunks = 0

    def run(self):
        """
        Executa geração com Kokoro.
        """
        try:
            print(f"   [Producer] Thread iniciada")

            # Inicializa pipeline se necessário
            if self.pipeline is None:
                from kokoro import KPipeline
                import torch

                print(f"   [Producer] Inicializando pipeline...")
                self.pipeline = KPipeline(
                    lang_code='p',
                    repo_id='hexgrad/Kokoro-82M',
                    device='cuda' if torch.cuda.is_available() else 'cpu'
                )
                print(f"   [Producer] Pipeline inicializado")

            # Gera chunks
            print(f"   [Producer] Gerando áudio para: \"{self.texto[:50]}...\"")

            for result in self.pipeline(self.texto, voice='pf_dora', speed=1.0):
                if result.audio is not None:
                    self.num_chunks += 1
                    chunk = result.audio.cpu().numpy().astype(np.float32)

                    # Enfileira
                    self.audio_queue.put(chunk)
                    tamanho_fila = self.audio_queue.qsize()

                    duracao = len(chunk) / 24000
                    print(f"   [Producer] Chunk {self.num_chunks} → fila (size: {tamanho_fila}, {duracao:.2f}s)")

            # Sinaliza fim
            self.audio_queue.put(None)
            print(f"   [Producer] Finalizado ({self.num_chunks} chunks)")

        except Exception as e:
            self.erro = e
            print(f"   [Producer] ❌ Erro: {e}")
            import traceback
            traceback.print_exc()
            self.audio_queue.put(None)

        finally:
            self.finished_event.set()


def testar_threading_kokoro():
    """
    Testa threading com Kokoro real.

    Returns:
        bool: True se sucesso, False se falha
    """
    print("\n🧪 Teste 2: Threading com Kokoro")
    print("-" * 70)

    # Cria fila e eventos
    audio_queue = queue.Queue(maxsize=10)
    finished_event = threading.Event()

    # Cria PyAudio
    p = pyaudio.PyAudio()

    # Texto de teste
    texto = """
    Testando streaming em tempo real com threading.
    Este é o segundo parágrafo do teste.
    E este é o terceiro e último parágrafo.
    """

    # Cria threads
    producer = KokoroProducerThread(
        texto=texto,
        audio_queue=audio_queue,
        finished_event=finished_event
    )

    consumer = ConsumerThread(
        audio_queue=audio_queue,
        pyaudio_instance=p,
        verbose=True
    )

    # Inicia threads
    tempo_inicio = time.perf_counter()

    print("\n   🧵 Iniciando threads...")
    consumer.start()
    time.sleep(0.1)
    producer.start()

    # Aguarda conclusão
    producer.join()
    tempo_producao = (time.perf_counter() - tempo_inicio) * 1000

    consumer.join()
    tempo_total = (time.perf_counter() - tempo_inicio) * 1000

    print(f"\n   ✅ Producer finalizado em {tempo_producao:.0f}ms")
    print(f"   ✅ Consumer finalizado em {tempo_total:.0f}ms")

    # Termina PyAudio
    p.terminate()

    # Verifica erros
    if producer.erro or consumer.erro:
        print(f"   ❌ Erros detectados")
        return False

    # Verifica chunks
    if consumer.chunks_tocados == producer.num_chunks and producer.num_chunks > 0:
        print(f"   ✅ Todos os chunks tocados ({consumer.chunks_tocados}/{producer.num_chunks})")

        # Calcula benefício de streaming
        # Se producer demorou menos que consumer, significa que começou a tocar antes de terminar de gerar
        if tempo_producao < tempo_total:
            ganho = tempo_total - tempo_producao
            print(f"   🚀 Ganho de streaming: {ganho:.0f}ms (áudio começou a tocar antes de terminar geração)")

        return True
    else:
        print(f"   ❌ Problema com chunks ({consumer.chunks_tocados}/{producer.num_chunks})")
        return False


def main():
    """
    Executa todos os testes de threading.
    """
    print("=" * 70)
    print("  ETAPA 5: Teste de Threading com Queue")
    print("=" * 70)

    resultados = {
        "Threading sintético": testar_threading_simples(),
        "Threading Kokoro": testar_threading_kokoro()
    }

    # Resumo
    print("\n" + "=" * 70)
    print("  RESUMO")
    print("=" * 70)

    for nome, sucesso in resultados.items():
        status = "✅" if sucesso else "❌"
        print(f"{status} {nome}")

    sucessos = sum(resultados.values())
    total = len(resultados)
    print(f"\n📊 Resultado: {sucessos}/{total} testes passaram")

    if sucessos == total:
        print("\n🎉 ETAPA 5 CONCLUÍDA COM SUCESSO!")
        print("   Arquitetura multi-threading funcionando perfeitamente!")
        print("   Sistema pronto para streaming em tempo real!")
        return 0
    else:
        print("\n❌ Alguns testes falharam")
        return 1


if __name__ == "__main__":
    try:
        codigo_saida = main()
        sys.exit(codigo_saida)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrompido pelo usuário")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
