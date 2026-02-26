## Importing libraries and files
import os
from dotenv import load_dotenv
load_dotenv()

from crewai.tools import tool
from crewai_tools import SerperDevTool
from langchain_community.document_loaders import PyPDFLoader

## Creating search tool
search_tool = SerperDevTool()

## Creating custom pdf reader tool using @tool decorator
@tool("read_financial_document")
def read_data_tool(file_path: str = 'data/sample.pdf') -> str:
    """Tool to read data from a PDF financial document.

    Args:
        file_path (str, optional): Path of the pdf file. Defaults to 'data/sample.pdf'.

    Returns:
        str: Full Financial Document content
    """
    
    loader = PyPDFLoader(file_path=file_path)
    docs = loader.load()

    full_report = ""
    for data in docs:
        # Clean and format the financial document data
        content = data.page_content
        
        # Remove extra whitespaces and format properly
        while "\n\n" in content:
            content = content.replace("\n\n", "\n")
            
        full_report += content + "\n"
        
    return full_report