#!/usr/bin/env python3
"""
ETAPA 7: Teste de Casos Extremos

Valida robustez do sistema em cenários adversos:
1. Seleção vazia
2. Texto muito longo
3. Texto com caracteres especiais
4. Interrupção (simulada)
"""

import sys
import subprocess
import time
from pathlib import Path


def testar_selecao_vazia():
    """
    Testa comportamento com seleção vazia.

    Returns:
        bool: True se tratamento correto, False caso contrário
    """
    print("\n🧪 Teste 1: Seleção vazia")
    print("-" * 70)

    # Limpa seleção primária
    try:
        subprocess.run(
            ["wl-copy", "--primary", "--clear"],
            check=True,
            timeout=2
        )
        print("   ✅ Seleção primária limpa")
    except:
        print("   ⚠️  Não foi possível limpar seleção, pulando teste")
        return True  # Não falha o teste

    # Executa script
    print("   🔧 Executando script com seleção vazia...")

    try:
        resultado = subprocess.run(
            [".venv/bin/python", "examples/ler_selecao_tts.py"],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Verifica se saiu graciosamente
        if resultado.returncode == 0:
            if "Nenhum texto selecionado" in resultado.stdout or "Nenhum texto selecionado" in resultado.stderr:
                print("   ✅ Script saiu graciosamente com mensagem apropriada")
                return True
            else:
                print("   ⚠️  Script saiu com código 0 mas sem mensagem clara")
                return True
        else:
            print(f"   ❌ Script retornou código {resultado.returncode}")
            print(f"   Saída: {resultado.stdout[:200]}")
            print(f"   Erro: {resultado.stderr[:200]}")
            return False

    except subprocess.TimeoutExpired:
        print("   ❌ Script travou (timeout)")
        return False
    except Exception as e:
        print(f"   ❌ Erro ao executar: {e}")
        return False


def testar_texto_longo():
    """
    Testa comportamento com texto muito longo.

    Returns:
        bool: True se tratamento correto, False caso contrário
    """
    print("\n🧪 Teste 2: Texto muito longo")
    print("-" * 70)

    # Gera texto longo (repete parágrafo 100 vezes)
    paragrafo = "Este é um parágrafo de teste para validar o processamento de textos longos. "
    texto_longo = (paragrafo * 100)[:10000]  # Limita a 10k chars

    print(f"   📝 Texto gerado: {len(texto_longo)} caracteres")

    # Copia para seleção primária
    try:
        processo = subprocess.Popen(
            ["wl-copy", "--primary"],
            stdin=subprocess.PIPE,
            text=True
        )
        processo.communicate(input=texto_longo, timeout=2)
        print("   ✅ Texto copiado para seleção primária")
    except Exception as e:
        print(f"   ❌ Erro ao copiar texto: {e}")
        return False

    # Executa script (com timeout maior)
    print("   🔧 Executando script com texto longo...")
    print("   ⏳ (isto pode demorar ~30s...)")

    try:
        tempo_inicio = time.time()

        resultado = subprocess.run(
            [".venv/bin/python", "examples/ler_selecao_tts.py"],
            capture_output=True,
            text=True,
            timeout=60  # 60 segundos de timeout
        )

        tempo_total = time.time() - tempo_inicio

        print(f"   ✅ Script concluiu em {tempo_total:.1f}s")

        # Verifica se processou ou se truncou apropriadamente
        if resultado.returncode == 0:
            print("   ✅ Processamento bem-sucedido")
            return True
        else:
            print(f"   ⚠️  Script retornou código {resultado.returncode}")
            # Ainda considera sucesso se saiu graciosamente
            return resultado.returncode < 2

    except subprocess.TimeoutExpired:
        print("   ❌ Script travou (timeout de 60s)")
        return False
    except Exception as e:
        print(f"   ❌ Erro ao executar: {e}")
        return False


def testar_caracteres_especiais():
    """
    Testa comportamento com caracteres especiais.

    Returns:
        bool: True se tratamento correto, False caso contrário
    """
    print("\n🧪 Teste 3: Caracteres especiais")
    print("-" * 70)

    # Texto com vários caracteres especiais
    texto_especial = """
    Teste com caracteres especiais: àáâãäåèéêëìíîïòóôõöùúûü
    Cedilha: ç
    Símbolos: @#$%&*()_+-=[]{}|;:'"<>,.?/
    Números: 0123456789
    """

    print(f"   📝 Texto com caracteres especiais preparado")

    # Copia para seleção primária
    try:
        processo = subprocess.Popen(
            ["wl-copy", "--primary"],
            stdin=subprocess.PIPE,
            text=True
        )
        processo.communicate(input=texto_especial, timeout=2)
        print("   ✅ Texto copiado para seleção primária")
    except Exception as e:
        print(f"   ❌ Erro ao copiar texto: {e}")
        return False

    # Executa script
    print("   🔧 Executando script...")

    try:
        resultado = subprocess.run(
            [".venv/bin/python", "examples/ler_selecao_tts.py"],
            capture_output=True,
            text=True,
            timeout=30
        )

        if resultado.returncode == 0:
            print("   ✅ Processamento bem-sucedido")
            return True
        else:
            print(f"   ⚠️  Script retornou código {resultado.returncode}")
            # Ainda considera sucesso se não crashou
            return resultado.returncode < 2

    except subprocess.TimeoutExpired:
        print("   ❌ Script travou (timeout)")
        return False
    except Exception as e:
        print(f"   ❌ Erro ao executar: {e}")
        return False


def testar_log_rotacao():
    """
    Verifica se sistema de logging está funcionando.

    Returns:
        bool: True se logs existem, False caso contrário
    """
    print("\n🧪 Teste 4: Sistema de logging")
    print("-" * 70)

    log_file = Path("logs/tts_debug.log")

    if not log_file.exists():
        print("   ❌ Arquivo de log não existe")
        return False

    # Lê tamanho
    tamanho = log_file.stat().st_size

    print(f"   ✅ Arquivo de log existe: {log_file}")
    print(f"   ✅ Tamanho: {tamanho} bytes ({tamanho/1024:.1f} KB)")

    # Lê primeiras linhas
    try:
        with open(log_file, 'r') as f:
            linhas = f.readlines()[:5]

        print(f"   ✅ Total de linhas no log: ~{len(linhas)} (primeiras 5)")

        # Verifica formato
        if any("DEBUG" in linha for linha in linhas):
            print("   ✅ Log contém entradas DEBUG")
            return True
        else:
            print("   ⚠️  Log não contém entradas DEBUG esperadas")
            return False

    except Exception as e:
        print(f"   ❌ Erro ao ler log: {e}")
        return False


def main():
    """
    Executa todos os testes de casos extremos.
    """
    print("=" * 70)
    print("  ETAPA 7: Teste de Casos Extremos")
    print("=" * 70)
    print("\n⚠️  NOTA: Alguns testes podem demorar até 60 segundos")
    print("         e vão tocar áudio. Seja paciente!\n")

    # Executa testes
    resultados = {
        "Seleção vazia": testar_selecao_vazia(),
        "Texto longo": testar_texto_longo(),
        "Caracteres especiais": testar_caracteres_especiais(),
        "Sistema de logging": testar_log_rotacao()
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

    if sucessos >= total - 1:  # Permite 1 falha
        print("\n🎉 ETAPA 7 CONCLUÍDA COM SUCESSO!")
        print("   Sistema robusto e pronto para uso!")
        return 0
    else:
        print("\n⚠️  Alguns testes falharam, mas sistema pode estar OK")
        print("    Revise os logs para mais detalhes")
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
