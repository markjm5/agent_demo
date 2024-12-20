from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from tools.agent_tools import check_system_time, get_order_id, get_order_detail
from langchain_core.prompts import PromptTemplate

# Up to 39:56    of https://www.youtube.com/watch?v=W7TZwB-KErw

def invoke_agent(st, option_llm="gpt-4o-mini", option_prompt="react", query="What is the current time in New York. You are currently in Singapore."):
  load_dotenv()  # take environment variables from .env.

  llm = ChatOpenAI(model=option_llm) 

  query = query
  
  prompt_template = get_react_prompt_template(option_prompt)

  tools = [check_system_time, get_order_id, get_order_detail]
  #tools = []

  agent = create_react_agent(llm, tools, prompt_template)
  agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True, return_intermediate_steps=True)
  response = agent_executor.invoke({"input": query})

  st.header("Answer:")
  st.write(response['output'])
  st.header("ReAct Reasoning Process:")
  try:
    #import pdb; pdb.set_trace()
    resp = response['intermediate_steps'][0][0].to_json()['kwargs']['log']
    #train_of_thought = resp.split('.')
    i=0
    for x in response['intermediate_steps']:    
      i = i + 1
      #import pdb; pdb.set_trace()
      st.write("%s - %s" % (i, x[0].log.lstrip()))
  except IndexError as e:
      st.write("Still thinking...")

def get_react_prompt_template(prompt):
    return PromptTemplate.from_file("./prompts/%s.txt" % (prompt))