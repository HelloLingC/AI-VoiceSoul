import edge_tts
from edge_tts import VoicesManager
import asyncio
import sounddevice
import soundfile
import numpy as np

voice_name = "en-HK-YanNeural" # zh-CN-XiaoyiNeural

async def get_voices():
    voices = await edge_tts.list_voices()
    res = {f"{v['ShortName']} - {v['Locale']} ({v['Gender']})": v['ShortName'] for v in voices}
    print(res)

def synthesize(text):
    communicate = edge_tts.Communicate(text, voice_name)
    # await communicate.save("output.wav")
    audio_file = open("output.wav", "wb")
    for chunk in communicate.stream_sync():
        if chunk["type"] == "audio":
            audio_file.write(chunk["data"])
        else:
            print(chunk["type"])
            print(chunk["text"])
    data, samplerate = soundfile.read("output.wav")
    sounddevice.play(data, samplerate=samplerate)
    sounddevice.wait()

if __name__ == "__main__":
    synthesize("大西洋革命是18世纪末和19世纪初的革命浪潮的总称。从1760年代到1870年代，影响范围波及大西洋两岸。")
    # asyncio.run(synthesize("你好，世界"))
    # asyncio.run(get_voices())