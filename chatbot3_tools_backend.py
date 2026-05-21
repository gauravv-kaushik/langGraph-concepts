from langgraph.graph import StateGraph, START, END
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.tools import tool
import requests
import random
import sqlite3

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)

#tools

search_tool = DuckDuckGoSearchRun(region="us-en")

@tool
def calculator(first_num: float, second_num: float, operation: str) -> dict:
    """
    Performs basic arithmetic operations on two numbers.
    supported operations are: add, subtract, multiply, divide.
    """

    try:
        if operation == "add":
            result =  first_num + second_num
        elif operation == "subtract":
            result = first_num - second_num
        elif operation == "multiply":
            result = first_num * second_num
        elif operation == "divide":
            if second_num == 0:
                return {"error": "division by zero is not allowed"}
            result = first_num / second_num
        else:
            return {"error": f"unsupported operation {operation}"}
        
        return {"first_name": first_num, "second_num": second_num, "operation": operation, "result": result}
    
    except Exception as e:
        raise ValueError("An error occurred while performing the calculation.")
    
tools = [search_tool, calculator]

llm_with_tools =llm.bind_tools(tools=tools)

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState):
    """LLM node that may answer or call tools based on the user query."""
    messages = state["messages"]
    res = llm_with_tools.invoke(messages)
    return {"messages": [res]}


tool_node = ToolNode(tools=tools)

conn = sqlite3.connect(database='chatbot.db', check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)

graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_node("tools", tool_node)

graph.add_edge(START, "chat_node")
graph.add_conditional_edges("chat_node", tools_condition)
graph.add_edge("tools", "chat_node")

chatbot = graph.compile(checkpointer=checkpointer)

def retrieve_all_threads():
    all_unique_threads = set()
    for checkpoint in checkpointer.list(None):
        all_unique_threads.add(checkpoint.config['configurable']['thread_id'])
    return list(all_unique_threads)

