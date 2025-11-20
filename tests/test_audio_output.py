#!/usr/bin/env python3
"""
Teste de Saída de Áudio - Diagnóstico

Testa todos os dispositivos de áudio e toca um tom em cada um
para identificar qual está funcionando.
"""

import pyaudio
import numpy as np
import time

def tocar_tom_teste(device_id, device_name, p):
    """Toca tom de teste em dispositivo específico."""
    print(f"\n{'='*70}")
    print(f"🔊 Testando: [{device_id}] {device_name}")
    print(f"{'='*70}")

    try:
        # Gera tom de 440 Hz (Lá) por 2 segundos
        sample_rate = 24000
        duracao = 2.0
        freq = 440.0

        t = np.linspace(0, duracao, int(sample_rate * duracao), dtype=np.float32)
        tom = 0.3 * np.sin(2 * np.pi * freq * t)

        # Abre stream NESTE dispositivo específico
        stream = p.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=sample_rate,
            output=True,
            output_device_index=device_id,
            frames_per_buffer=2048
        )

        print(f"   ▶️  Tocando tom de 440 Hz por 2 segundos...")
        print(f"   🎧 VOCÊ OUVIU O SOM? (aguarde...)")

        stream.write(tom.tobytes())

        stream.stop_stream()
        stream.close()

        print(f"   ✅ Playback concluído neste dispositivo")

        # Pergunta ao usuário
        resposta = input("\n   👂 Você OUVIU o som? (s/n): ").strip().lower()

        if resposta == 's':
            print(f"\n   🎉 DISPOSITIVO FUNCIONANDO: [{device_id}] {device_name}")
            return device_id
        else:
            print(f"   ❌ Sem som neste dispositivo")
            return None

    except Exception as e:
        print(f"   ❌ Erro ao testar dispositivo: {e}")
        return None

def main():
    print("="*70)
    print("  TESTE DE SAÍDA DE ÁUDIO - Diagnóstico")
    print("="*70)
    print("\nEste script vai:")
    print("1. Listar todos os dispositivos de áudio")
    print("2. Tocar um tom de teste em cada um")
    print("3. Você me diz qual funcionou")
    print("\n⚠️  IMPORTANTE: Deixe o volume do sistema em nível audível!")

    input("\nPressione ENTER para começar...")

    p = pyaudio.PyAudio()

    # Lista dispositivos de saída
    print("\n" + "="*70)
    print("  DISPOSITIVOS DE SAÍDA DISPONÍVEIS")
    print("="*70)

    dispositivos_saida = []
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info['maxOutputChannels'] > 0:
            dispositivos_saida.append((i, info))
            eh_padrao = " [PADRÃO]" if i == p.get_default_output_device_info()['index'] else ""
            print(f"   [{i}] {info['name']}{eh_padrao}")

    print(f"\nTotal: {len(dispositivos_saida)} dispositivos de saída")

    # Testa cada dispositivo
    print("\n" + "="*70)
    print("  INICIANDO TESTES")
    print("="*70)
    print("\n⚠️  Atenção: Um tom de 440 Hz vai tocar em CADA dispositivo.")
    print("   Você terá 2 segundos para ouvir e depois responder se ouviu.")

    input("\nPressione ENTER para iniciar os testes...")

    dispositivos_funcionando = []

    for device_id, info in dispositivos_saida:
        resultado = tocar_tom_teste(device_id, info['name'], p)
        if resultado is not None:
            dispositivos_funcionando.append((device_id, info['name']))

        # Pausa entre testes
        time.sleep(0.5)

    # Resumo
    p.terminate()

    print("\n" + "="*70)
    print("  RESUMO DO TESTE")
    print("="*70)

    if dispositivos_funcionando:
        print(f"\n✅ Dispositivos que FUNCIONARAM ({len(dispositivos_funcionando)}):")
        for device_id, name in dispositivos_funcionando:
            print(f"   [{device_id}] {name}")

        print("\n" + "="*70)
        print("  SOLUÇÃO")
        print("="*70)

        device_id = dispositivos_funcionando[0][0]
        device_name = dispositivos_funcionando[0][1]

        print(f"\n🔧 Configure o TTS para usar o dispositivo [{device_id}]:")
        print(f"   Nome: {device_name}")
        print(f"\n📝 Edite: examples/ler_selecao_tts.py")
        print(f"   Linha ~254, modifique para:")
        print(f"\n   stream = self.pyaudio_instance.open(")
        print(f"       format=pyaudio.paFloat32,")
        print(f"       channels=1,")
        print(f"       rate=24000,")
        print(f"       output=True,")
        print(f"       output_device_index={device_id},  # ← ADICIONE ESTA LINHA")
        print(f"       frames_per_buffer=2048")
        print(f"   )")

    else:
        print("\n❌ NENHUM dispositivo funcionou!")
        print("\n🔍 Possíveis causas:")
        print("   1. Volume do sistema está mudo")
        print("   2. Fones/caixas desconectados")
        print("   3. Problema com PipeWire/PulseAudio")
        print("\n💡 Tente:")
        print("   - Verificar volume: pavucontrol")
        print("   - Verificar PipeWire: systemctl --user status pipewire")
        print("   - Testar com: speaker-test -c 2")

    print("\n" + "="*70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Teste interrompido")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
