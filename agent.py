from langgraph.prebuilt import create_react_agent
from tools import tools
from voice_control import *
import constants, json

# Make sure your API key is set
# Create agent with OpenAI model
# Create the agent
class Agent:
    def __init__(self):
        self.prompts = json.load(open("prompts.json"))
        self.agent = create_react_agent(
            model=constants.gpt_model,
            tools=tools,
            prompt=self.prompts['system']
        )

    def run_agent(self):
        # Run the agent
        try:
            t2s(self.prompts['introduction'])
            while True:
                result = self.agent.invoke(
                    {"messages": [{"role": "user", "content": s2t()}]}
                )

                print(result['messages'][-1].content)
                t2s(result['messages'][-1].content)
        except KeyboardInterrupt:
            print("Exiting...")