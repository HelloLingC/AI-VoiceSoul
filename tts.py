from kokoro import KPipeline
import sounddevice as sd

pipeline = KPipeline(lang_code='a')

def synthesize(text):
    generator = pipeline(
    text, voice='af_heart', # af_bella, af_heart, af_nicole
    speed=1, split_pattern=r'\n+'
    )
    for i, (gs, ps, audio) in enumerate(generator):
        # print(i)  # i => index
        # print(gs) # gs => graphemes/text
        # print(ps) # ps => phonemes
        sd.play(audio, samplerate=22050)
        sd.wait()

if __name__ == '__main__':
    synthesize("hi, emmmmm... what's your name by the way?")