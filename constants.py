import queue, os
from vosk import Model, KaldiRecognizer

path = "/".join(os.path.abspath(__file__).split("/")[:-1])
MODEL_PATH = f"{path}/vosk-model-en-us-0.22-lgraph"  # unpacked folder
# Try to load the VOSK model but fail gracefully if it's missing or invalid
model = None
rec = None
try:
	model = Model(MODEL_PATH)
except Exception as e:
	# Don't raise here; let the rest of the program run without speech recognition.
	# Print a concise warning so the user knows why speech features are disabled.
	print(f"Warning: failed to load VOSK model at {MODEL_PATH}: {e}")

samplerate = 16000
blocksize = 8000
channels = 1

if model is not None:
	try:
		rec = KaldiRecognizer(model, samplerate)
	except Exception as e:
		print(f"Warning: failed to create KaldiRecognizer: {e}")

q = queue.Queue()

gpt_model = "openai:gpt-5-nano"


def load_vosk_model(path=None):
	"""Attempt to load the VOSK model at runtime.

	If `path` is provided it will be used; otherwise the module-level
	`MODEL_PATH` is used. Returns True on success, False on failure.
	"""
	global model, rec, MODEL_PATH
	mp = path or MODEL_PATH
	try:
		model = Model(mp)
		# ensure samplerate variable exists
		rec = KaldiRecognizer(model, samplerate)
		MODEL_PATH = mp
		print(f"Loaded VOSK model from {mp}")
		return True
	except Exception as e:
		print(f"Error loading VOSK model from {mp}: {e}")
		model = None
		rec = None
		return False