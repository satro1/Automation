from langgraph.prebuilt import create_react_agent
from tools import tools
from voice_control import s2t, t2s
import constants, json

# Make sure your API key is set
# Create agent with OpenAI model
# Create the agent
class Agent:
    def __init__(self, mode: str = "text"):
        """Create an Agent.

        mode: 'text' | 'speech' | 'auto'
        """
        self.mode = mode
        self.prompts = json.load(open("prompts.json"))
        self.agent = create_react_agent(
            model=constants.gpt_model,
            tools=tools,
            prompt=self.prompts['system']
        )

    def _get_user_input(self):
        """Return user input depending on mode.

        In 'speech' mode we use s2t(); in 'text' mode we use typed input().
        In 'auto' mode we prefer speech if recognizer is available, else text.
        """
        if self.mode == "text":
            try:
                return input("Type your input: ")
            except EOFError:
                return ""

        if self.mode == "auto":
            # prefer speech if recognizer exists
            if constants.rec is not None:
                return s2t()
            else:
                try:
                    return input("Type your input: ")
                except EOFError:
                    return ""

        # explicit speech mode
        return s2t()

    def _output_response(self, text: str):
        """Output agent response according to mode: print always; speak only in speech/auto when recognizer present."""
        print(text)
        if self.mode in ("speech", "auto") and constants.rec is not None:
            try:
                t2s(text)
            except Exception:
                # swallow TTS errors to avoid crashing the loop
                pass

    def run_agent(self):
        # Run the agent
        try:
            # Only speak the introduction if we're in speech mode and recognizer exists
            if self.mode in ("speech", "auto") and constants.rec is not None:
                try:
                    t2s(self.prompts['introduction'])
                except Exception:
                    pass
            else:
                # Print introduction for text mode
                print(self.prompts['introduction'])

            while True:
                user_input = self._get_user_input()
                if not user_input:
                    # empty input, skip
                    continue

                result = self.agent.invoke(
                    {"messages": [{"role": "user", "content": user_input}]}
                )

                reply = result['messages'][-1].content
                self._output_response(reply)
        except KeyboardInterrupt:
            print("Exiting...")