
import subprocess
import re
import sys

def obter_selecao_primaria():
    """
    Captura o texto que está apenas selecionado (azulzinho),
    sem precisar dar Ctrl+C. Usa o registro 'primary' do Wayland.
    """
    try:
        # O parametro '--primary' é o segredo.
        # O stderr=subprocess.DEVNULL evita sujar o terminal se nada estiver selecionado.
        texto = subprocess.check_output(
            ["wl-paste", "--primary"],
            text=True,
            stderr=subprocess.DEVNULL
        )
        return texto.strip()
    except FileNotFoundError:
        print("Erro: O pacote 'wl-clipboard' não está instalado.")
        sys.exit(1)
    except subprocess.CalledProcessError:
        # Acontece se a seleção estiver vazia
        return ""

def limpar_texto_para_tts(texto):
    """
    Remove quebras de linha de PDFs ou terminais para o áudio não ficar picotado.
    """
    if not texto:
        return None

    # 1. Substitui quebras de linha simples por espaço (junta a frase)
    # Mas mantém quebras duplas (parágrafos)
    texto_limpo = re.sub(r'(?<!\n)\n(?!\n)', ' ', texto)

    # 2. Remove espaços múltiplos gerados pela limpeza
    texto_limpo = re.sub(r'\s+', ' ', texto_limpo)

    return texto_limpo.strip()

# --- BLOCO PRINCIPAL (Integre isso onde você gera o áudio) ---

if __name__ == "__main__":
    print("🔍 Buscando texto na seleção do mouse...")

    texto_bruto = obter_selecao_primaria()
    texto_final = limpar_texto_para_tts(texto_bruto)

    if texto_final:
        print(f"🗣️ Lendo: {texto_final[:100]}...") # Mostra os primeiros 100 chars

        # ============================================================
        # AQUI ENTRA O SEU CÓDIGO DO KOKORO
        # Exemplo:
        # kokoro.create_audio(texto_final, voice="af_bella", speed=1.0)
        # ============================================================

    else:
        print("⚠️ Nada selecionado ou seleção vazia.")
