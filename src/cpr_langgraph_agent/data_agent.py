from typing import Annotated, List, Optional
import json

from langchain_core.messages import ToolMessage, SystemMessage
from langchain_core.tools import InjectedToolCallId

from langchain_openai import AzureChatOpenAI

from langgraph.prebuilt import create_react_agent, InjectedState
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.types import Command

from langchain_community.vectorstores.azuresearch import AzureSearch

from cpr_langgraph_agent.crm_client import AsyncCrmClient
from cpr_langgraph_agent.state_models import AgentStateModel
from cpr_langgraph_agent.data_agent_prompts import AGENT_PROMPT

class DataAgent:
    def __init__(self, llm: AzureChatOpenAI, crm_client: AsyncCrmClient, checkpointer: BaseCheckpointSaver):
        self.agent = create_react_agent(
            name='data_agent',
            model=llm,
            tools=[
                self.get_customer_by_email, 
                self.get_customer_consumption_points,
                self.get_customer_contracts,
                self.get_contract_payments
            ],
            pre_model_hook=self.pre_model_hook,
            state_schema=AgentStateModel,
            prompt=AGENT_PROMPT,
            checkpointer=checkpointer,
        )
        with open("doc/cpr_langgraph_data_agent.png", "wb") as f:
            f.write(self.agent.get_graph().draw_mermaid_png())
        self.crm_client = crm_client
    
    async def pre_model_hook(self, state: AgentStateModel):
        content = state.model_dump(include={
                    'incoming_ticket', 
                    'customer',
                    'consumption_points',
                    'contracts',
                    'payments',
                })
        state_data = SystemMessage(content=f'Following are the CURRENT DATA provided by the tools and user: \n {json.dumps(content, indent=4, ensure_ascii=False)}')
        output = {
            "llm_input_messages": [*state.messages, state_data]
        }
        return output

    async def get_customer_by_email(self, tool_call_id: Annotated[str, InjectedToolCallId], state: Annotated[AgentStateModel, InjectedState]) -> Command:
        """
        Use this tool to retrieve customer details from CRM.
        """
        customer = await self.crm_client.get_customer_by_email(state.incoming_ticket.email)
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