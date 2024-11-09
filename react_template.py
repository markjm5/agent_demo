from langchain_core.prompts import PromptTemplate

def get_react_prompt_template():
    return PromptTemplate.from_file("./prompts/react.txt")