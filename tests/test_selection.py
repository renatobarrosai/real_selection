#!/usr/bin/env python3
"""
ETAPA 2: Teste de Captura de Seleção Primária

Valida a captura de texto da seleção primária do Wayland e
a função de limpeza de texto para TTS.

Instruções:
1. Selecione um texto em qualquer aplicativo (browser, terminal, editor)
2. Execute este script
3. O script mostrará o texto bruto e o texto limpo
"""

import subprocess
import sys
import re
from typing import Optional


def obter_selecao_primaria() -> Optional[str]:
    """
    Captura o texto da seleção primária do Wayland.

    A seleção primária é o texto que está apenas selecionado (destacado),
    sem precisar usar Ctrl+C.

    Returns:
        Optional[str]: Texto selecionado ou None se houver erro
    """
    try:
        # O parâmetro '--primary' captura a seleção primária (texto selecionado)
        # O stderr=subprocess.DEVNULL evita poluir o terminal se não houver seleção
        texto = subprocess.check_output(
            ["wl-paste", "--primary"],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=2
        )
        return texto.strip()

    except FileNotFoundError:
        print("❌ Erro: wl-clipboard não está instalado")
        print("   💡 Instale com: sudo pacman -S wl-clipboard")
        return None

    except subprocess.TimeoutExpired:
        print("❌ Erro: Timeout ao capturar seleção")
        return None

    except subprocess.CalledProcessError:
        # Acontece quando a seleção primária está vazia
        return ""

    except Exception as e:
        print(f"❌ Erro inesperado ao capturar seleção: {str(e)}")
        return None


def limpar_texto_para_tts(texto: str) -> Optional[str]:
    """
    Limpa e prepara texto para síntese de voz.

    Remove quebras de linha indesejadas (típicas de PDFs e terminais)
    mas preserva parágrafos (quebras duplas).

    Args:
        texto: Texto bruto a ser limpo

    Returns:
        Optional[str]: Texto limpo ou None se vazio
    """
    if not texto:
        return None

    # 1. Substitui quebras de linha simples por espaço
    #    Mantém quebras duplas (parágrafos)
    #    Regex: (?<!\n)\n(?!\n) significa "quebra não precedida nem seguida por outra quebra"
    texto_limpo = re.sub(r'(?<!\n)\n(?!\n)', ' ', texto)

    # 2. Remove espaços múltiplos (mas preserva quebras de linha)
    #    Substitui múltiplos espaços/tabs por um único espaço
    #    Mas NÃO substitui quebras de linha
    texto_limpo = re.sub(r'[ \t]+', ' ', texto_limpo)

    # 3. Remove espaços no início e fim
    texto_limpo = texto_limpo.strip()

    return texto_limpo if texto_limpo else None


def mostrar_comparacao(texto_bruto: str, texto_limpo: str):
    """
    Exibe comparação visual entre texto bruto e limpo.

    Args:
        texto_bruto: Texto original capturado
        texto_limpo: Texto após limpeza
    """
    print("\n" + "=" * 70)
    print("  COMPARAÇÃO DE TEXTO")
    print("=" * 70)

    # Texto bruto
    print("\n📝 TEXTO BRUTO (como capturado):")
    print("─" * 70)
    if len(texto_bruto) > 300:
        print(repr(texto_bruto[:300]) + "...")
        print(f"   (mostrando 300 de {len(texto_bruto)} caracteres)")
    else:
        print(repr(texto_bruto))
    print(f"   Tamanho: {len(texto_bruto)} caracteres")
    print(f"   Quebras de linha: {texto_bruto.count(chr(10))}")

    # Texto limpo
    print("\n✨ TEXTO LIMPO (para TTS):")
    print("─" * 70)
    if len(texto_limpo) > 300:
        print(repr(texto_limpo[:300]) + "...")
        print(f"   (mostrando 300 de {len(texto_limpo)} caracteres)")
    else:
        print(repr(texto_limpo))
    print(f"   Tamanho: {len(texto_limpo)} caracteres")
    print(f"   Quebras de linha: {texto_limpo.count(chr(10))}")

    # Estatísticas
    reducao = len(texto_bruto) - len(texto_limpo)
    print(f"\n📊 Redução: {reducao} caracteres removidos")


def testar_casos_especificos():
    """
    Testa a função de limpeza com casos de teste específicos.
    """
    print("\n" + "=" * 70)
    print("  TESTES DE LIMPEZA")
    print("=" * 70)

    casos_teste = [
        (
            "Linha 1\nLinha 2\nLinha 3",
            "Linha 1 Linha 2 Linha 3",
            "Quebras simples → espaços"
        ),
        (
            "Parágrafo 1\n\nParágrafo 2",
            "Parágrafo 1\n\nParágrafo 2",
            "Quebras duplas preservadas"
        ),
        (
            "Texto    com     espaços     múltiplos",
            "Texto com espaços múltiplos",
            "Espaços múltiplos → único espaço"
        ),
        (
            "  Espaços no início e fim  ",
            "Espaços no início e fim",
            "Trim de espaços"
        ),
        (
            "PDF quebrado\nno meio da\npalavra ou frase\ne continua aqui",
            "PDF quebrado no meio da palavra ou frase e continua aqui",
            "Texto típico de PDF"
        ),
    ]

    sucessos = 0
    for i, (entrada, esperado, descricao) in enumerate(casos_teste, 1):
        resultado = limpar_texto_para_tts(entrada)
        passou = resultado == esperado

        status = "✅" if passou else "❌"
        print(f"\n{status} Teste {i}: {descricao}")
        print(f"   Entrada:  {repr(entrada)}")
        print(f"   Esperado: {repr(esperado)}")
        print(f"   Obtido:   {repr(resultado)}")

        if passou:
            sucessos += 1

    print(f"\n📊 Resultado: {sucessos}/{len(casos_teste)} testes passaram")
    return sucessos == len(casos_teste)


def main():
    """
    Executa teste de captura de seleção primária.
    """
    print("=" * 70)
    print("  ETAPA 2: Teste de Captura de Seleção Primária")
    print("=" * 70)
    print("\n📋 Instruções:")
    print("   1. Selecione um texto em qualquer aplicativo")
    print("   2. NÃO copie (Ctrl+C), apenas selecione")
    print("   3. Este script capturará a seleção automaticamente")
    print("\n⏳ Aguardando 3 segundos para você selecionar o texto...")

    import time
    time.sleep(3)

    # Captura seleção
    print("\n🔍 Capturando seleção primária...")
    texto_bruto = obter_selecao_primaria()

    if texto_bruto is None:
        print("❌ Erro ao capturar seleção")
        return 1

    if not texto_bruto:
        print("⚠️  Nenhum texto selecionado")
        print("   Tente novamente selecionando algum texto antes de executar o script")
        print("\n🧪 Executando testes de limpeza de qualquer forma...")
        testes_ok = testar_casos_especificos()
        return 0 if testes_ok else 1

    # Limpa texto
    print("✅ Texto capturado!")
    texto_limpo = limpar_texto_para_tts(texto_bruto)

    if not texto_limpo:
        print("⚠️  Texto vazio após limpeza")
        return 1

    # Mostra comparação
    mostrar_comparacao(texto_bruto, texto_limpo)

    # Executa testes
    testes_ok = testar_casos_especificos()

    # Resumo final
    print("\n" + "=" * 70)
    print("  RESUMO")
    print("=" * 70)
    print(f"✅ Captura de seleção: OK")
    print(f"✅ Limpeza de texto: OK")
    print(f"{'✅' if testes_ok else '❌'} Testes unitários: {'OK' if testes_ok else 'FALHA'}")

    if testes_ok:
        print("\n🎉 ETAPA 2 CONCLUÍDA COM SUCESSO!")
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
