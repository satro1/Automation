import argparse, sys

import constants

def parse_args():
	p = argparse.ArgumentParser(description="Run the automation agent in speech or text mode")
	p.add_argument("--mode", choices=["speech", "text", "auto"], default="auto",
				   help="Operation mode: 'speech' to use microphone (requires a VOSK model), 'text' to use typed input, 'auto' to use speech if available else text")
	p.add_argument("--model-path", help="Optional path to VOSK model directory to use when --mode=speech or when loading in auto mode")
	return p.parse_args()


def main():
	args = parse_args()

	if args.mode == "speech":
		# Try to load model (may have already been attempted at import time). If it fails, exit with error.
		ok = constants.load_vosk_model(args.model_path) if hasattr(constants, 'load_vosk_model') else False
		if not ok and constants.rec is None:
			print("Error: speech mode requested but VOSK model could not be loaded. Provide a valid --model-path or install a model at the default path.")
			sys.exit(1)
	elif args.mode == "auto":
		# If recognizer not loaded yet, try to load if a model path was provided.
		if constants.rec is None and args.model_path:
			constants.load_vosk_model(args.model_path)
		if constants.rec is None:
			print("Auto mode: speech recognizer not available, falling back to text mode.")

	# Import Agent and run after we attempted any model loading above.
	from agent import Agent
	Agent().run_agent()


if __name__ == "__main__":
	main()