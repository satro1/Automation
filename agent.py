from langgraph.prebuilt import create_react_agent
from tools import tools
from voice_control import *
import constants, json

# Make sure your API key is set
# Create agent with OpenAI model
def create_agent():
    agent = create_react_agent(
        model=constants.gpt_model,
        tools=tools,
        prompt=json.load(open("prompts.json"))['system']
    )
    return agent

def run_agent(agent):
    # Run the agent
    try:
        t2s(json.load(open("prompts.json"))['introduction'])
        while True:
            result = agent.invoke(
                {"messages": [{"role": "user", "content": s2t()}]}
            )

            print(result['messages'][-1].content)
            t2s(result['messages'][-1].content)
    except KeyboardInterrupt:
        print("Exiting...")