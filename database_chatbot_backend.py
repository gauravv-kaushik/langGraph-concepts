from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
load_dotenv()
import sqlite3

model = ChatGoogleGenerativeAI(model='gemini-2.5-flash', temperature=0.5)

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState):
    messages = state['messages']
    res = model.invoke(messages)
    return {'messages':[res]}

conn = sqlite3.connect(database='chatbot.db', check_same_thread=False)

checkpointer = SqliteSaver(conn=conn)

graph = StateGraph(ChatState)
graph.add_node('chat_node', chat_node)

graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)

chatbot = graph.compile(checkpointer=checkpointer)

CONFIG = {'configurable': {'thread_id': 'thread-2'}}

chatbot.invoke({'messages':[HumanMessage(content='What is the capital of India?')]},config=CONFIG)


def retrieve_all_threads():
    all_unique_threads = set()
    for checkpoint in checkpointer.list(None):
        all_unique_threads.add(checkpoint.config['configurable']['thread_id'])
    return list(all_unique_threads)