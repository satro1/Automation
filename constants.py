import queue, os
from vosk import Model, KaldiRecognizer

path = "/".join(os.path.abspath(__file__).split("/")[:-1])
MODEL_PATH = f"{path}/vosk-model-en-us-0.22-lgraph"  # unpacked folder
model = Model(MODEL_PATH)

samplerate = 16000
blocksize = 8000
channels = 1
rec = KaldiRecognizer(model, samplerate)
q = queue.Queue()