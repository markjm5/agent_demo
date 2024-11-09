from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage 
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser 
from langchain.tools.render import render_text_description
#from langchain import hub
from common import get_react_prompt_template
from langchain.agents import create_react_agent, AgentExecutor
from tools.system_time_tool import check_system_time
from groq import Groq

# Up to 39:56    of https://www.youtube.com/watch?v=W7TZwB-KErw

load_dotenv()  # take environment variables from .env.

#llm = ChatOpenAI(model="gpt-4o-mini", model_kwargs={"stop": "\nObservation"}) 
llm = ChatOpenAI(model="gpt-4o-mini") 

#query = "Who is Katy Perry?"
query = "What is the current time in New York. You are currently in Singapore."

"""
messages = [
    SystemMessage(content="you're a helpful assistant"),
    HumanMessage(content=query)
]
"""
#prompt_template = PromptTemplate.from_template("{input}?")
#prompt_template = hub.pull("hwchase17/react")
prompt_template = get_react_prompt_template()

#prompt_template = prompt_template + """ I will first retrieve the current system time.
#Action: check_system_time  
#Action Input: '%Y-%m-%d %H:%M:%S'""" + "\n Observation: 13:04:00\nThought:"

tools = [check_system_time]

agent = create_react_agent(llm, tools, prompt_template)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
agent_executor.invoke({"input": query})

#tools_list = render_text_description(list(tools))
#tool_names = ", ".join((t.name for t in tools))
#output_parser = StrOutputParser()
#chain = prompt_template | llm | output_parser
#result = chain.invoke({"input": query, "tools":tools_list, "tool_names":tool_names, "agent_scratchpad":""})

#result = llm.invoke(messages)
#print(result)
