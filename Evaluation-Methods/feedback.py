import os
import base64
import logging
import json
from typing import TypedDict, List, Any
# from PIL import Image
# import cv2
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """
    Defines the state that flows through our agent. It's a dictionary that
    holds all the intermediate data as the agent works on a problem.
    """
    initial_prompt: str
    media_path: str
    disease_name: str
    initial_analysis: str
    remedy_search_results: str
    final_report: str
    
class promptRouter:
    
    def __init__(self, )-> None:
        


