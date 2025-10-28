import sounddevice as sd, json, pyttsx3, constants

''' Text to speech '''
def t2s(text):
    engine = pyttsx3.init()

    engine.setProperty("rate", 180)   # speed
    # engine.setProperty("volume", 0.9) # 0–1
    # voices = engine.getProperty("voices")
    # engine.setProperty("voice", voices[2].id)  # pick a voice

    engine.say(text)
    engine.runAndWait()
    engine.stop()

# 2, 4, 11, 13

''' Speech to text '''
def callback(indata, frames, time, status):
    constants.q.put(bytes(indata))

def s2t():
    # If recognizer wasn't created (e.g., model failed to load), fall back to typed input.
    if constants.rec is None:
        print("Speech recognizer unavailable — falling back to typed input.")
        try:
            return input("Type your input: ")
        except EOFError:
            return ""

    with sd.RawInputStream(samplerate=constants.samplerate, blocksize=constants.blocksize, dtype='int16',
                        channels=constants.channels, callback=callback):
        print("Speak… Ctrl+C to stop.")
        try:
            while True:
                data = constants.q.get()
                if constants.rec.AcceptWaveform(data):
                    text = json.loads(constants.rec.Result())["text"]
                    print(text)
                    return text
        except KeyboardInterrupt:
            text = json.loads(constants.rec.FinalResult())["text"]
            print(text)
            return text
