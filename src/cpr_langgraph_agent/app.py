import os
import json
from typing import List
from dotenv import load_dotenv
from fastapi import FastAPI

from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_core.documents import Document
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.prebuilt import create_react_agent
from langchain_community.vectorstores.azuresearch import AzureSearch
from azure.search.documents.indexes.models import (
    SearchField, SearchFieldDataType, SimpleField, SearchableField
)

from cpr_langgraph_agent.agent_prompt import AGENT_PROMPT, AGENT_PROMPT_2

load_dotenv()

AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
AZURE_OPENAI_MODEL_NAME = os.getenv("AZURE_OPENAI_MODEL_NAME")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")
AZURE_OPENAI_EMBEDDING_MODEL_NAME = os.getenv("AZURE_OPENAI_EMBEDDING_MODEL_NAME")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")

AZURE_AI_SEARCH_ENDPOINT = os.getenv("AZURE_AI_SEARCH_ENDPOINT")
AZURE_AI_SEARCH_INDEX_NAME = os.getenv("AZURE_AI_SEARCH_INDEX_NAME")
AZURE_AI_SEARCH_API_KEY = os.getenv("AZURE_AI_SEARCH_API_KEY")


SEMANTIC_CONFIG = os.getenv("SEMANTIC_CONFIG")

llm = AzureChatOpenAI(
    api_version=AZURE_OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    azure_deployment=AZURE_OPENAI_DEPLOYMENT_NAME,
    model=AZURE_OPENAI_MODEL_NAME,
    api_key=AZURE_OPENAI_API_KEY,
    timeout=60,
    max_retries=3,
)

embeding = AzureOpenAIEmbeddings(
    api_version=AZURE_OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    azure_deployment=AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME,
    model=AZURE_OPENAI_EMBEDDING_MODEL_NAME,
    api_key=AZURE_OPENAI_API_KEY
)

fields = [
    SimpleField( name="id", type=SearchFieldDataType.String, key=True, filterable=True ),
    SearchableField( name="ticket_id", type=SearchFieldDataType.String, filterable=True ),
    SearchableField( name="category_1", type=SearchFieldDataType.String, filterable=True),
    SearchableField( name="category_2", type=SearchFieldDataType.String, filterable=True),
    SearchableField( name="category_3", type=SearchFieldDataType.String, filterable=True ),
    SearchableField( name="status", type=SearchFieldDataType.String, filterable=True ),
    SearchableField( name="created_by", type=SearchFieldDataType.String, filterable=True ),
    SearchableField( name="eic", type=SearchFieldDataType.String, filterable=True ),
    SearchableField( name="email", type=SearchFieldDataType.String, filterable=True ),
    SearchableField( name="request_content", type=SearchFieldDataType.String ),
    SearchableField( name="response_content", type=SearchFieldDataType.String ),
    SearchField(   name="request_embedding",
                   type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                   searchable=True,
                   vector_search_dimensions=3072,
                   vector_search_profile_name="request_embedding_profile" ),
    SearchableField( name="filename", type=SearchFieldDataType.String, filterable=True ),
    SearchableField( name="source_uri", type=SearchFieldDataType.String, filterable=True ),
    SimpleField( name="index_datetime", type=SearchFieldDataType.DateTimeOffset, filterable=True),
    SimpleField( name="deleted", type=SearchFieldDataType.Boolean, filterable=True),
    SearchableField( name="key_phrases", type=SearchFieldDataType.Collection(SearchFieldDataType.String), searchable=True, filterable=True),
    SearchableField( name="entities", type=SearchFieldDataType.Collection(SearchFieldDataType.String), searchable=True, filterable=True),
]

search = AzureSearch(
    azure_search_endpoint=AZURE_AI_SEARCH_ENDPOINT,
    index_name=AZURE_AI_SEARCH_INDEX_NAME,
    azure_search_key=AZURE_AI_SEARCH_API_KEY,
    embedding_function=embeding,
    semantic_configuration_name=SEMANTIC_CONFIG,
    search_type="semantic_hybrid",
    fields=fields
)

async def find_relevant_claims(search_term: str) -> List[Document]:
    """Use this tool to find relevant customer claim and complaint tickets"""
    return await search.asemantic_hybrid_search(
        query=search_term,
        k=5,
    )

agent = create_react_agent(
    model=llm,
    tools=[find_relevant_claims],
    prompt=AGENT_PROMPT_2
)
with open("doc/cpr_langgraph_agent.png", "wb") as f:
    f.write(agent.get_graph().draw_mermaid_png())

app = FastAPI(title="cpr_langgraph_agent")

@app.post("/chat")
async def chat(question: str):
    messages = [
        HumanMessage(content=question)
    ]
    output = await agent.ainvoke(
        input={'messages': messages}
    )
    for message in output['messages']:
        if isinstance(message, BaseMessage):
            m: BaseMessage=message
            print(json.dumps(m.model_dump(), ensure_ascii=False, indent=4))
    return output

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("cpr_langgraph_agent.app:app", host="0.0.0.0", port=8000, reload=False)