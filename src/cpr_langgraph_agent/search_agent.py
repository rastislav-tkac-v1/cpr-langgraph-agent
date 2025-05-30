
from typing import Annotated
import json

from langchain_core.documents import Document
from langchain_core.messages import ToolMessage, SystemMessage
from langchain_core.tools import InjectedToolCallId
from langchain_openai import AzureChatOpenAI

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.types import Command

from langchain_community.vectorstores.azuresearch import AzureSearch

from cpr_langgraph_agent.search_agent_prompts import AGENT_PROMPT
from cpr_langgraph_agent.models import Ticket
from cpr_langgraph_agent.state_models import AgentStateModel

class SearchAgent:
    def __init__(self, llm: AzureChatOpenAI, search: AzureSearch, checkpointer: BaseCheckpointSaver):
        self.agent = create_react_agent(
            name='search_agent',
            model=llm,
            tools=[
                self.find_relevant_claims, 
            ],
            pre_model_hook=self.pre_model_hook,
            state_schema=AgentStateModel,
            prompt=AGENT_PROMPT,
            checkpointer=checkpointer,
        )
        with open("doc/cpr_langgraph_search_agent.png", "wb") as f:
            f.write(self.agent.get_graph().draw_mermaid_png())
        
        self.search = search

    async def pre_model_hook(self, state: AgentStateModel):
        content = state.model_dump(include={
                    'incoming_ticket', 
                    'similar_tickets'
                })
        state_data = SystemMessage(content=f'Following are the CURRENT DATA provided by the tools and user: \n {json.dumps(content, indent=4, ensure_ascii=False)}')
        output = {
            "llm_input_messages": [*state.messages, state_data]
        }
        return output

    async def find_relevant_claims(self, tool_call_id: Annotated[str, InjectedToolCallId], search_term: str) -> Command:
        """Use this tool to find relevant customer claim and complaint tickets"""
        search_result: Document = await self.search.asemantic_hybrid_search(
            query=search_term,
            k=5,
        )
        similar_tickets = []
        for document in search_result:
            d = document.metadata
            ticket = Ticket(
                id=d.get('id'),
                category_1=d.get('category_1'),
                category_2=d.get('category_2'),
                category_3=d.get('category_3'),
                status=d.get('status'),
                created_by=d.get('created_by'),
                eic=d.get('eic'),
                email=d.get('email'),
                request_content=document.page_content,
                response_content=d.get('response_content')
            )
            similar_tickets.append(ticket)
        return Command(update={
            'similar_tickets': similar_tickets,
            'messages': [
                ToolMessage('Successfully found similar tickets. See the CURRENT DATA for their contents.', tool_call_id=tool_call_id)
            ]
        })