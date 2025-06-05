
from typing import Annotated, List, Optional
import json

from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage
from langchain_core.tools import InjectedToolCallId, tool
from langchain_core.runnables import RunnableConfig
from langchain_openai import AzureChatOpenAI

from langgraph.prebuilt import InjectedState, ToolNode
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.types import Command
from langgraph.graph import StateGraph, END

from langchain_community.vectorstores.azuresearch import AzureSearch

from cpr_langgraph_agent.agent_prompt import AGENT_PROMPT_2
from cpr_langgraph_agent.models import Ticket
from cpr_langgraph_agent.crm_client import AsyncCrmClient
from cpr_langgraph_agent.state_models import AgentStateModel, AgentInputModel
from cpr_langgraph_agent.output_models import AgentOutput

class ReActAgent:
    def __init__(
            self, 
            llm: AzureChatOpenAI,
            search: AzureSearch, 
            crm_client: AsyncCrmClient, 
            checkpointer: BaseCheckpointSaver, 
    ):
        self.tools=[
                self.find_relevant_claims, 
                self.get_customer, 
                self.get_customer_consumption_points,
                self.get_customer_contracts,
                self.get_contract_payments
            ]

        self.llm_with_tools = llm.bind_tools(self.tools)
        self.llm_with_structured_output = llm.with_structured_output(AgentOutput)

        workflow = StateGraph(AgentStateModel)
        
        workflow.add_node("pre_model_hook", self.pre_model_hook)
        workflow.add_node("agent", self.call_model, input=AgentInputModel)
        workflow.add_node("tools", ToolNode(self.tools))
        workflow.add_node("respond", self.respond)

        workflow.set_entry_point("pre_model_hook")
        workflow.add_edge("pre_model_hook", "agent")
        workflow.add_conditional_edges(
            "agent", 
            self.should_continue,
            {
                "continue": "tools",
                "end": "respond",
            }
        )
        workflow.add_edge("tools", "pre_model_hook")
        workflow.add_edge("respond", END)

        self.agent = workflow.compile(checkpointer=checkpointer)
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

    async def respond(self, state: AgentStateModel):
        response = await self.llm_with_structured_output.ainvoke(
            [HumanMessage(content=state.messages[-1].content)]
        )
        return {"structured_response": response}
    
    async def call_model(self, input: AgentInputModel, config: RunnableConfig):
        system_prompt = SystemMessage(AGENT_PROMPT_2)
        response = await self.llm_with_tools.ainvoke([system_prompt] + input.llm_input_messages, config)
        # We return a list, because this will get added to the existing list
        return {"messages": [response]}
    
    # Define the conditional edge that determines whether to continue or not
    async def should_continue(self, state: AgentStateModel):
        messages = state.messages
        last_message = messages[-1]
        # If there is no function call, then we finish
        if not last_message.tool_calls:
            return "end"
        # Otherwise if there is, we continue
        else:
            return "continue"
    
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
                ToolMessage(content='Successfully found similar tickets. See the CURRENT DATA for their contents.', tool_call_id=tool_call_id)
            ]
        })
    
    async def get_customer(self, tool_call_id: Annotated[str, InjectedToolCallId], state: Annotated[AgentStateModel, InjectedState]) -> Command:
        """
        Use this tool to retrieve customer details from CRM.
        """
        customer = await self.crm_client.get_customer_by_email(state.incoming_ticket.email)
        return Command(update={
            'customer': customer,
            'messages': [
                ToolMessage(content='Successfully loaded customer record. See the CURRENT DATA for the customer record content.', tool_call_id=tool_call_id)
            ]
        })
    
    async def get_customer_consumption_points(self, tool_call_id: Annotated[str, InjectedToolCallId], state: Annotated[AgentStateModel, InjectedState], product_family: Optional[str] = None) -> Command:
        """
        Use this tool to retrieve customer consumption points.
        Optionally you can filter consumption points by product family ('electricity' or 'gas') based on the incoming ticket contents

        Arguments:
          - product_family - optional argument, use it in case you want to retrieve only consumption points for certain product family. Supported product families are 'electricity' and 'gas'
        """
        if state.customer:
            consumption_points = await self.crm_client.get_customer_consumption_points(state.customer.customer_id, product_family=product_family)
            return Command(update={
                'consumption_points': consumption_points,
                'messages': [
                    ToolMessage(content='Successfully loaded consumption point list. See the CURRENT DATA for the list contents.', tool_call_id=tool_call_id)
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
                    ToolMessage(content='Successfully loaded contract list. See the CURRENT DATA for the list contents.', tool_call_id=tool_call_id)
                ]
            })
    
    async def get_contract_payments(self, tool_call_id: Annotated[str, InjectedToolCallId], state: Annotated[AgentStateModel, InjectedState], contract_ids: List[str]) -> Command:
        """
        Use this tool to retrieve contract payments by contract id. 
        Arguments:
          - contract_ids - List of contract IDs for which the payments shall be retrieved 
        """
        if state.customer:
            payments = [await self.crm_client.get_contract_payments(state.customer.customer_id, contract_id) for contract_id in contract_ids]
            return Command(update={
                'payments': payments,
                'messages': [
                    ToolMessage(content='Successfully loaded payment list', tool_call_id=tool_call_id)
                ]
            })