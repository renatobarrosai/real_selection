#!/usr/bin/env python3
"""
ETAPA 3: Teste de Pipeline Kokoro + GPU

Valida que o pipeline Kokoro carrega corretamente:
- Lang code 'p' (Português do Brasil)
- Voz 'pf_dora'
- Device 'cuda' (GPU)
- Gera áudio de teste e mede performance
"""

import sys
import time
import torch
import soundfile as sf
from pathlib import Path


def main():
    """
    Executa teste completo do pipeline Kokoro com GPU.
    """
    print("=" * 70)
    print("  ETAPA 3: Teste de Pipeline Kokoro + GPU")
    print("=" * 70)

    # Importa Kokoro
    try:
        from kokoro import KPipeline
        print("\n✅ Módulo kokoro importado")
    except ImportError as e:
        print(f"\n❌ Erro ao importar kokoro: {e}")
        return 1

    # Verifica CUDA
    print("\n🔥 Verificando CUDA...")
    cuda_disponivel = torch.cuda.is_available()
    if cuda_disponivel:
        gpu_nome = torch.cuda.get_device_name(0)
        print(f"   ✅ CUDA disponível")
        print(f"   ✅ GPU: {gpu_nome}")
    else:
        print("   ⚠️  CUDA não disponível, usando CPU")

    # Inicializa pipeline
    print("\n🔧 Inicializando pipeline...")
    print("   Lang code: 'p' (Português do Brasil)")
    print("   Repo: hexgrad/Kokoro-82M")
    print(f"   Device: {'cuda' if cuda_disponivel else 'cpu'}")

    tempo_inicio = time.perf_counter()

    try:
        pipeline = KPipeline(
            lang_code='p',
            repo_id='hexgrad/Kokoro-82M',
            device='cuda' if cuda_disponivel else 'cpu'
        )
        tempo_init = (time.perf_counter() - tempo_inicio) * 1000
        print(f"   ✅ Pipeline inicializado em {tempo_init:.0f}ms")

    except Exception as e:
        print(f"   ❌ Erro ao inicializar pipeline: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Verifica device do modelo
    device_modelo = str(pipeline.model.device)
    print(f"   ✅ Modelo carregado em: {device_modelo}")

    # Pré-carrega voz
    print("\n🎤 Carregando voz pf_dora...")
    tempo_inicio = time.perf_counter()

    try:
        voz = pipeline.load_voice('pf_dora')
        tempo_voz = (time.perf_counter() - tempo_inicio) * 1000

        # Calcula tamanho da voz em MB
        tamanho_voz = voz.element_size() * voz.nelement() / (1024 * 1024)

        print(f"   ✅ Voz carregada em {tempo_voz:.0f}ms")
        print(f"   ✅ Tamanho: {tamanho_voz:.1f} MB")
        print(f"   ✅ Shape: {tuple(voz.shape)}")
        print(f"   ✅ Device: {voz.device}")

    except Exception as e:
        print(f"   ❌ Erro ao carregar voz: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Gera áudio de teste
    print("\n🔊 Gerando áudio de teste...")

    texto_teste = "Olá Renato, este é um teste do sistema de síntese de voz. A voz da Dora está funcionando perfeitamente!"
    print(f"   Texto: \"{texto_teste}\"")

    tempo_inicio = time.perf_counter()
    audio_chunks = []
    num_chunks = 0

    try:
        generator = pipeline(texto_teste, voice='pf_dora', speed=1.0)

        for i, result in enumerate(generator):
            num_chunks += 1
            audio = result.audio
            phonemes = result.phonemes

            if audio is not None:
                audio_chunks.append(audio)
                duracao_chunk = len(audio) / 24000  # 24kHz sample rate

                print(f"   ✅ Chunk {i+1}:")
                print(f"      Fonemas: {phonemes[:50]}{'...' if len(phonemes) > 50 else ''}")
                print(f"      Samples: {len(audio):,} ({duracao_chunk:.2f}s)")

        tempo_geracao = (time.perf_counter() - tempo_inicio) * 1000

    except Exception as e:
        print(f"   ❌ Erro ao gerar áudio: {e}")
        import traceback
        traceback.print_exc()
        return 1

    if not audio_chunks:
        print("   ❌ Nenhum áudio gerado")
        return 1

    # Concatena chunks
    print("\n📊 Processando áudio...")
    try:
        import numpy as np
        audio_completo = np.concatenate([a.cpu().numpy() for a in audio_chunks])

        duracao_total = len(audio_completo) / 24000
        print(f"   ✅ Chunks gerados: {num_chunks}")
        print(f"   ✅ Total de samples: {len(audio_completo):,}")
        print(f"   ✅ Duração: {duracao_total:.2f}s")
        print(f"   ✅ Tempo de geração: {tempo_geracao:.0f}ms")

        # Calcula RTF (Real-Time Factor)
        rtf = (tempo_geracao / 1000) / duracao_total
        print(f"   ✅ RTF: {rtf:.3f} ({1/rtf:.1f}x mais rápido que tempo real)")

    except Exception as e:
        print(f"   ❌ Erro ao processar áudio: {e}")
        return 1

    # Salva arquivo WAV
    print("\n💾 Salvando arquivo WAV...")
    arquivo_saida = Path("test_output_gpu.wav")

    try:
        sf.write(str(arquivo_saida), audio_completo, 24000)
        tamanho_arquivo = arquivo_saida.stat().st_size / 1024  # KB
        print(f"   ✅ Arquivo salvo: {arquivo_saida}")
        print(f"   ✅ Tamanho: {tamanho_arquivo:.1f} KB")

    except Exception as e:
        print(f"   ❌ Erro ao salvar arquivo: {e}")
        return 1

    # Verifica uso de memória GPU (se CUDA disponível)
    if cuda_disponivel:
        print("\n💻 Uso de memória GPU:")
        try:
            mem_alocada = torch.cuda.memory_allocated(0) / (1024**2)  # MB
            mem_reservada = torch.cuda.memory_reserved(0) / (1024**2)  # MB
            mem_max = torch.cuda.max_memory_allocated(0) / (1024**2)  # MB

            print(f"   ✅ Alocada: {mem_alocada:.1f} MB")
            print(f"   ✅ Reservada: {mem_reservada:.1f} MB")
            print(f"   ✅ Máxima: {mem_max:.1f} MB")

        except Exception as e:
            print(f"   ⚠️  Não foi possível obter uso de memória: {e}")

    # Resumo final
    print("\n" + "=" * 70)
    print("  RESUMO")
    print("=" * 70)
    print(f"✅ Inicialização do pipeline: OK ({tempo_init:.0f}ms)")
    print(f"✅ Carregamento da voz: OK ({tempo_voz:.0f}ms)")
    print(f"✅ Geração de áudio: OK ({tempo_geracao:.0f}ms, RTF={rtf:.3f})")
    print(f"✅ Arquivo salvo: {arquivo_saida}")
    print(f"✅ Device: {device_modelo}")

    # Critérios de sucesso
    sucesso = True
    problemas = []

    if tempo_init > 5000:  # > 5 segundos
        problemas.append(f"Inicialização lenta ({tempo_init:.0f}ms)")
        sucesso = False

    if rtf > 0.2:  # Não está 5x mais rápido que tempo real
        problemas.append(f"RTF alto ({rtf:.3f}, esperado < 0.2)")
        sucesso = False

    if not cuda_disponivel:
        problemas.append("CUDA não disponível (usando CPU)")
        # Não marca como falha, apenas aviso

    if sucesso and cuda_disponivel:
        print("\n🎉 ETAPA 3 CONCLUÍDA COM SUCESSO!")
        print("   Sistema pronto para inferência em tempo real com GPU!")
        return 0
    elif sucesso:
        print("\n⚠️  ETAPA 3 CONCLUÍDA COM AVISOS")
        print("   Sistema funcionando em CPU (performance reduzida)")
        return 0
    else:
        print("\n❌ ETAPA 3 CONCLUÍDA COM PROBLEMAS:")
        for prob in problemas:
            print(f"   - {prob}")
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
