import pyaudio

class AudioRecorder:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.chunk = 1024
        self.stream = None

    def init_audio_stream(self, sample_rate=44100):
        stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=sample_rate, input=True, frames_per_buffer=self.chunk)
        return stream
    
    def stop(self):
        self.stream.stop_stream()
        self.stream.close()


