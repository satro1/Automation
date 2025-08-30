from langgraph.prebuilt import create_react_agent
from tools import *
from voice_control import *
from constants import *

# Make sure your API key is set
# Create agent with OpenAI model
def create_agent():
    agent = create_react_agent(
        model="openai:gpt-5-nano",
        tools=[get_weather],
        prompt="You are a helpful assistant"
    )
    return agent

def run_agent(agent):
    # Run the agent
    try:
        t2s("Hello Papi this is Alexi, how may I help you baby?")
        while True:
            result = agent.invoke(
                {"messages": [{"role": "user", "content": s2t()}]}
            )

            print(result['messages'][-1].content)
            t2s(result['messages'][-1].content)
    except KeyboardInterrupt:
        print("Exiting...")