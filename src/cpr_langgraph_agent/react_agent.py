
from typing import Annotated, List, Optional
import json

from langchain_core.documents import Document
from langchain_core.messages import ToolMessage, SystemMessage
from langchain_core.tools import InjectedToolCallId
from langchain_openai import AzureChatOpenAI

from langgraph.prebuilt import create_react_agent, InjectedState
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.types import Command

from langchain_community.vectorstores.azuresearch import AzureSearch

from cpr_langgraph_agent.agent_prompt import AGENT_PROMPT_2
from cpr_langgraph_agent.models import Ticket, Customer, ConsumptionPoint, Contract, Payment
from cpr_langgraph_agent.crm_client import AsyncCrmClient
from cpr_langgraph_agent.state_models import AgentStateModel

class ReActAgent:
    def __init__(self, llm: AzureChatOpenAI, search: AzureSearch, crm_client: AsyncCrmClient, checkpointer: BaseCheckpointSaver):
        self.agent = create_react_agent(
            model=llm,
            tools=[
                self.find_relevant_claims, 
                self.get_customer_by_email, 
                self.get_customer_consumption_points,
                self.get_customer_contracts,
                self.get_contract_payments
            ],
            pre_model_hook=self.pre_model_hook,
            state_schema=AgentStateModel,
            prompt=AGENT_PROMPT_2,
            checkpointer=checkpointer,
        )
        with open("doc/cpr_langgraph_agent.png", "wb") as f:
            f.write(self.agent.get_graph().draw_mermaid_png())
        
        self.search = search
        self.crm_client = crm_client

    async def pre_model_hook(self, state: AgentStateModel):
        content = state.model_dump(include={
                    'incoming_ticket', 
                    'customer',
                    'consumption_points',
                    'contracts',
                    'payments',
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
    
    async def get_customer_by_email(self, tool_call_id: Annotated[str, InjectedToolCallId], state: Annotated[AgentStateModel, InjectedState]) -> Command:
        """
        Use this tool to retrieve customer details from CRM.
        """
        customer:Customer = await self.crm_client.get_customer_by_email(state.incoming_ticket.email)
        return Command(update={
            'customer': customer,
            'messages': [
                ToolMessage('Successfully loaded customer record. See the CURRENT DATA for the customer record content.', tool_call_id=tool_call_id)
            ]
        })
    
    async def get_customer_consumption_points(self, tool_call_id: Annotated[str, InjectedToolCallId], state: Annotated[AgentStateModel, InjectedState], product_family: Optional[str] = None) -> Command:
        """
        Use this tool to retrieve customer consumption points.
        Optionally you can filter consumption points by product family ('electricity' or 'gas') based on the incoming ticket contents
        """
        if state.customer:
            consumption_points = await self.crm_client.get_customer_consumption_points(state.customer.customer_id, product_family=product_family)
            return Command(update={
                'consumption_points': consumption_points,
                'messages': [
                    ToolMessage('Successfully loaded consumption point list. See the CURRENT DATA for the list contents.', tool_call_id=tool_call_id)
                ]
            })

    async def get_customer_contracts(self, tool_call_id: Annotated[str, InjectedToolCallId], state: Annotated[AgentStateModel, InjectedState]) -> Command:
        """
        Use this tool to retrieve customer contracts
        """
        if state.customer:
            contracts = await self.crm_client.get_customer_contracts(state.customer.customer_id)
            return Command(update={
                'contracts': contracts,
                'messages': [
                    ToolMessage('Successfully loaded contract list. See the CURRENT DATA for the list contents.', tool_call_id=tool_call_id)
                ]
            })
    
    async def get_contract_payments(self, tool_call_id: Annotated[str, InjectedToolCallId], state: Annotated[AgentStateModel, InjectedState], contract_ids: List[str]) -> Command:
        """
        Use this tool to retrieve contract payments by contract id. 
        """
        if state.customer:
            payments = [await self.crm_client.get_contract_payments(state.customer.customer_id, contract_id) for contract_id in contract_ids]
            return Command(update={
                'payments': payments,
                'messages': [
                    ToolMessage('Successfully loaded payment list', tool_call_id=tool_call_id)
                ]
            })