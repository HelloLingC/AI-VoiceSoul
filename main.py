import pyaudio
import numpy as np
import time
import os
from dotenv import load_dotenv
from rich.console import Console
from rich.live import Live
from rich.text import Text
import torch
import torchaudio
import asr
import threading
import llm
import prompt
import tts
import tts_edge

console = Console()

# Initialize Silero VAD model properly
model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                            model='silero_vad',
                            force_reload=False,
                            onnx=True)
(get_speech_timestamps,
 save_audio,
 read_audio,
 VADIterator,
 collect_chunks) = utils

"""
silero vad (Supported values: 256 for 8000 sample rate, 512 for 16000)
"""
pending_seconds = 2.8
is_pending = False
pending_stop_signal = False

vad_iterator = VADIterator(model)
current_asr_thread = None
is_speaking = False # when is_speaking is True, we are recording audio
is_transcribing = False
is_llm_waiting = False
is_tts_synthesizing = False

vad_results = []
vad_lines = []
speaking_audio_chunk = []  # store audio during speech

llm_response_text = ""

def on_llm_response(response: str):
    global llm_response_text
    if llm_response_text == "thinking...":
        llm_response_text = ""
    llm_response_text += response
    # console.print(f"[blue]{llm_response_text}[/blue]", end="")

def ask_llm(text: str):
    is_llm_waiting = True
    console.print("thinking...", end="")
    tts.synthesize('thinking...')
    resp = llm.ask_llm(text, None, prompt.get_assistant_prompt())
    console.print(resp)
    is_llm_waiting = False
    is_tts_synthesizing = True
    tts.synthesize("LLM response detected")
    tts_edge.synthesize(resp)
    tts.synthesize("Enquiry completed")
    is_tts_synthesizing = False

def transcribe_audio_thread(audio_data):
    global is_transcribing, is_llm_waiting, llm_response_text, is_tts_synthesizing
    text = asr.transcribe_audio(audio_data)
    console.print(text)
    is_transcribing = False
    is_llm_waiting = True
    llm_response_text = "thinking..."
    llm.ask_llm(text, on_llm_response, prompt.get_assistant_prompt())
    is_llm_waiting = False
    is_tts_synthesizing = True
    tts.synthesize(llm_response_text)
    is_tts_synthesizing = False

def detected_vad(data):
    global is_speaking, speaking_audio_chunk, is_pending, is_transcribing
    vad_results.append(data)
    if len(vad_lines) > 4:
        vad_lines.pop(0)

    if 'start' in data:
        is_speaking = True
        speaking_audio_chunk = []  # Reset audio chunk at start of speech
        vad_lines.append(f"VAD detected at {data['start']}")
    else:
        pending_stop_signal = False
        is_pending = True
        time.sleep(pending_seconds)
        is_pending = False
        if pending_stop_signal:
            console.print("VAD stopped")
            return
        is_speaking = False
        vad_lines.append(f"VAD ended at {data['end']}")
        if speaking_audio_chunk:  # If we have collected audio
            audio_data = np.concatenate(speaking_audio_chunk)
            if not is_transcribing and not is_llm_waiting and not is_tts_synthesizing:
                is_transcribing = True
                transcribe_audio_thread(audio_data)

        speaking_audio_chunk = []
        vad_iterator.reset_states()

def draw_volume_wave_cli(live, rate=16000, chunk=512, channels=1, format=pyaudio.paInt16, duration=100):
    """Draws a simple audio volume wave in the CLI."""
    global current_asr_thread, pending_stop_signal, is_speaking

    p = pyaudio.PyAudio()

    stream = p.open(format=format,
                    channels=channels,
                    rate=rate,
                    input=True,
                    frames_per_buffer=chunk)

    print("Recording and displaying wave...")

    start_time = time.time()
    while True:
        try:
            data = stream.read(chunk)
            # Create a writable copy of the numpy array
            data_np = np.frombuffer(data, dtype=np.int16).copy()
            volume = np.abs(data_np).mean()  # Simple volume calculation

            # Convert audio data for VAD - normalize to float between -1 and 1
            tensor = torch.from_numpy(data_np).float() / 32768.0
            speech_prob = vad_iterator(tensor, rate)

            # Normalize and scale for CLI display
            max_volume = 2**15  # Max value for paInt16
            normalized_volume = volume / max_volume
            bar_length = int(normalized_volume * os.get_terminal_size().columns * 1.5)

            bar = "#" * bar_length
            spaces = " " * (os.get_terminal_size().columns - bar_length - 2)

            # Store audio data if speaking
            if is_speaking:
                speaking_audio_chunk.append(data_np)
            else:
                time.sleep(0.02)

            # vad signal # 当外放的时候，不要记录
            if speech_prob and not is_tts_synthesizing:
                if 'start' in speech_prob and is_pending:
                    is_speaking = True
                    pending_stop_signal = True
                    continue

                current_asr_thread = threading.Thread(target=detected_vad, args=(speech_prob,))
                current_asr_thread.start()
                # if 'end' in speech_prob:

            if len(vad_lines) > 0:
                vad_text = " & ".join(vad_lines)
            else:
                vad_text = "No speech detected"

            live.update(f"""[{bar}{spaces}
                        Volume: {int(volume)}
                        {vad_text}
                        {'[bold green]Speaking[/bold green]' if is_speaking else '[bold red]Not speaking[/bold red]'} | {'[bold green]Transcribing[/bold green]' if is_transcribing else '[bold]Not transcribing[/bold]'} | {'[bold green]LLM processing[/bold green]' if is_llm_waiting else '[bold]LLM not processing[/bold]'} | {'[bold green]synthesizing[/bold green]' if is_tts_synthesizing else '[bold]not synthesizing[/bold]'}

    [blue]{llm_response_text}[/blue]

""")

        except OSError as e:
            if e.errno == pyaudio.paInputOverflowed:
                console.print("Input overflowed. Skipping chunk.")
                continue;
            else:
                console.print(f"An OS error occurred: {e}")
                break;

    console.print("\nFinished.")

    stream.stop_stream()
    stream.close()
    p.terminate()

if __name__ == "__main__":
    load_dotenv()
    console.clear()
    # while True:
    #     text = input("Input your text: ")
    #     ask_llm(text)
    with Live(console=console, refresh_per_second=25) as live:
        draw_volume_wave_cli(live)