from pydantic import BaseModel, Field
from typing import List, Optional
from langchain_core.messages import AnyMessage
from langgraph.prebuilt.chat_agent_executor import AgentStatePydantic, StructuredResponse

from cpr_langgraph_agent.models import Ticket, Customer, ConsumptionPoint, Contract, Payment

class AgentStateModel(AgentStatePydantic):
    
    incoming_ticket: Ticket = Field(description='Incoming ticket containing customer claim')
    customer: Optional[Customer] = Field(description='Customer details', default=None)
    consumption_points: Optional[List[ConsumptionPoint]] = Field(description='List of customer consumption points', default=None)
    contracts: Optional[List[Contract]] = Field(description='List of customer contracts', default=None)
    payments: Optional[List[Payment]] = Field(description='List of customer payments', default=None)
    similar_tickets: Optional[List[Ticket]] = Field(description='List of similar tickets', default=None)
    structured_response: Optional[StructuredResponse] = Field(description='Structured response of the agent', default=None)

class AgentInputModel(AgentStateModel):
    llm_input_messages: List[AnyMessage] = Field(description='Messages prepared as an input for LLM model invocation. Some of these are not preserved in agent state')