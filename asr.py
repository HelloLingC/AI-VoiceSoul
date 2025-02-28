from faster_whisper import WhisperModel

v3_model_path = "D:/Projects/Python/VidComet/models/models--mobiuslabsgmbh--faster-whisper-large-v3-turbo/snapshots/0c94664816ec82be77b20e824c8e8675995b0029"
v2_model_path = "D:/Projects/Python/VidComet/models/models--Systran--faster-whisper-large-v2/snapshots/f0fe81560cb8b68660e564f55dd99207059c092e"

target_language = "en"

def transcribe_audio(audio_data):
    model = WhisperModel(v3_model_path, device="cuda", compute_type="float16")
    segments, _ = model.transcribe(audio_data, language=target_language)
    # for segment in segments:
    #     print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
    return " ".join([segment.text for segment in segments])

if __name__ == "__main__":
    audio_data = "D:/Projects/Python/VidComet/test.wav"
    segments = transcribe_audio(audio_data)
    for segment in segments:
        print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))