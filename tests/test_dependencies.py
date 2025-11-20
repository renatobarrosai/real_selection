#!/usr/bin/env python3
"""
ETAPA 1: Validação de Dependências e Ambiente

Verifica se todas as dependências necessárias estão instaladas e funcionando:
- wl-clipboard (wl-paste)
- espeak-ng
- pyaudio
- PyTorch com CUDA
"""

import subprocess
import sys
from typing import Tuple, Optional


def verificar_comando_sistema(comando: str, arg_versao: str = "--version") -> Tuple[bool, Optional[str]]:
    """
    Verifica se um comando do sistema está disponível.

    Args:
        comando: Nome do comando a verificar
        arg_versao: Argumento para obter versão (padrão: --version)

    Returns:
        Tuple[bool, Optional[str]]: (sucesso, versão ou mensagem de erro)
    """
    try:
        resultado = subprocess.run(
            [comando, arg_versao],
            capture_output=True,
            text=True,
            timeout=5
        )

        if resultado.returncode == 0:
            # Pega primeira linha da saída que geralmente contém a versão
            versao = resultado.stdout.strip().split('\n')[0]
            if not versao and resultado.stderr:
                versao = resultado.stderr.strip().split('\n')[0]
            return True, versao
        else:
            return False, f"Comando retornou código {resultado.returncode}"

    except FileNotFoundError:
        return False, "Comando não encontrado"
    except subprocess.TimeoutExpired:
        return False, "Timeout ao executar comando"
    except Exception as e:
        return False, f"Erro: {str(e)}"


def verificar_wl_clipboard() -> bool:
    """
    Verifica se wl-clipboard está instalado.

    Returns:
        bool: True se disponível, False caso contrário
    """
    print("📋 Verificando wl-clipboard...")
    sucesso, info = verificar_comando_sistema("wl-paste", "--version")

    if sucesso:
        print(f"   ✅ wl-clipboard: {info}")
        return True
    else:
        print(f"   ❌ wl-clipboard: {info}")
        print("   💡 Instale com: sudo pacman -S wl-clipboard")
        return False


def verificar_espeak_ng() -> bool:
    """
    Verifica se espeak-ng está instalado.

    Returns:
        bool: True se disponível, False caso contrário
    """
    print("\n🔊 Verificando espeak-ng...")
    sucesso, info = verificar_comando_sistema("espeak-ng", "--version")

    if sucesso:
        print(f"   ✅ espeak-ng: {info}")
        return True
    else:
        print(f"   ❌ espeak-ng: {info}")
        print("   💡 Instale com: sudo pacman -S espeak-ng")
        return False


def verificar_pyaudio() -> bool:
    """
    Verifica se PyAudio está instalado e funcionando.

    Returns:
        bool: True se disponível, False caso contrário
    """
    print("\n🎵 Verificando PyAudio...")

    try:
        import pyaudio

        # Tenta inicializar PyAudio
        p = pyaudio.PyAudio()

        # Conta dispositivos de áudio disponíveis
        num_dispositivos = p.get_device_count()

        # Lista dispositivos de saída
        dispositivos_saida = []
        for i in range(num_dispositivos):
            info = p.get_device_info_by_index(i)
            if info['maxOutputChannels'] > 0:
                dispositivos_saida.append((i, info['name']))

        versao = pyaudio.get_portaudio_version_text()
        p.terminate()

        print(f"   ✅ PyAudio: {versao}")
        print(f"   ✅ Dispositivos de áudio: {num_dispositivos} encontrados")
        print(f"   ✅ Dispositivos de saída: {len(dispositivos_saida)}")

        if dispositivos_saida:
            print(f"   📢 Dispositivo padrão: {dispositivos_saida[0][1]}")

        return True

    except ImportError:
        print("   ❌ PyAudio: não instalado")
        print("   💡 Instale com: pip install pyaudio")
        print("   💡 Pode precisar de: sudo pacman -S portaudio")
        return False
    except Exception as e:
        print(f"   ❌ PyAudio: erro ao inicializar - {str(e)}")
        return False


def verificar_pytorch_cuda() -> bool:
    """
    Verifica se PyTorch está instalado com suporte a CUDA.

    Returns:
        bool: True se CUDA disponível, False caso contrário
    """
    print("\n🔥 Verificando PyTorch e CUDA...")

    try:
        import torch

        versao_torch = torch.__version__
        print(f"   ✅ PyTorch: {versao_torch}")

        # Verifica CUDA
        cuda_disponivel = torch.cuda.is_available()

        if cuda_disponivel:
            num_gpus = torch.cuda.device_count()
            gpu_nome = torch.cuda.get_device_name(0)
            cuda_versao = torch.version.cuda

            print(f"   ✅ CUDA: disponível (versão {cuda_versao})")
            print(f"   ✅ GPUs detectadas: {num_gpus}")
            print(f"   ✅ GPU 0: {gpu_nome}")

            # Teste rápido de alocação na GPU
            try:
                teste = torch.zeros(1).cuda()
                del teste
                torch.cuda.empty_cache()
                print(f"   ✅ Teste de alocação GPU: sucesso")
            except Exception as e:
                print(f"   ⚠️  Teste de alocação GPU: falhou - {str(e)}")
                return False

            return True
        else:
            print("   ⚠️  CUDA: não disponível")
            print("   💡 Script funcionará em CPU (mais lento)")
            print("   💡 Verifique instalação do CUDA Toolkit e drivers NVIDIA")
            return False

    except ImportError:
        print("   ❌ PyTorch: não instalado")
        print("   💡 Instale com: pip install torch")
        return False
    except Exception as e:
        print(f"   ❌ PyTorch: erro - {str(e)}")
        return False


def verificar_kokoro() -> bool:
    """
    Verifica se biblioteca Kokoro está instalada.

    Returns:
        bool: True se disponível, False caso contrário
    """
    print("\n🗣️  Verificando Kokoro...")

    try:
        import kokoro
        versao = kokoro.__version__
        print(f"   ✅ Kokoro: {versao}")
        return True
    except ImportError:
        print("   ❌ Kokoro: não instalado")
        print("   💡 Instale com: pip install kokoro")
        return False
    except Exception as e:
        print(f"   ❌ Kokoro: erro - {str(e)}")
        return False


def main():
    """
    Executa todas as verificações de dependências.
    """
    print("=" * 60)
    print("  ETAPA 1: Validação de Dependências e Ambiente")
    print("=" * 60)

    resultados = {
        "wl-clipboard": verificar_wl_clipboard(),
        "espeak-ng": verificar_espeak_ng(),
        "pyaudio": verificar_pyaudio(),
        "pytorch_cuda": verificar_pytorch_cuda(),
        "kokoro": verificar_kokoro()
    }

    # Resumo
    print("\n" + "=" * 60)
    print("  RESUMO")
    print("=" * 60)

    total = len(resultados)
    sucessos = sum(resultados.values())

    for nome, sucesso in resultados.items():
        status = "✅" if sucesso else "❌"
        print(f"{status} {nome}")

    print(f"\n📊 Status: {sucessos}/{total} dependências disponíveis")

    # Verifica se todas as dependências críticas estão OK
    criticas = ["wl-clipboard", "pyaudio", "kokoro"]
    criticas_ok = all(resultados[dep] for dep in criticas)

    if criticas_ok and resultados["pytorch_cuda"]:
        print("\n🎉 SUCESSO! Todas as dependências estão OK.")
        print("   Sistema pronto para execução com GPU (CUDA).")
        return 0
    elif criticas_ok:
        print("\n⚠️  ATENÇÃO! Dependências críticas OK, mas CUDA não disponível.")
        print("   Sistema funcionará em CPU (mais lento).")
        return 0
    else:
        print("\n❌ FALHA! Dependências críticas faltando.")
        print("   Instale as dependências indicadas acima.")
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
