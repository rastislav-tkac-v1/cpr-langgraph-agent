from pydantic import BaseModel, Field
from typing import List, Optional
from langgraph.prebuilt.chat_agent_executor import AgentStatePydantic

from cpr_langgraph_agent.models import Ticket, Customer, ConsumptionPoint, Contract, Payment

class AgentStateModel(AgentStatePydantic):
    incoming_ticket: Ticket = Field(description='Incoming ticket containing customer claim')
    customer: Optional[Customer] = Field(description='Customer details', default=None)
    consumption_points: Optional[List[ConsumptionPoint]] = Field(description='List of customer consumption points', default=None)
    contracts: Optional[List[Contract]] = Field(description='List of customer contracts', default=None)
    payments: Optional[List[Payment]] = Field(description='List of customer payments', default=None)
    similar_tickets: Optional[List[Ticket]] = Field(description='List of similar tickets', default=None)
    suggested_responses: Optional[List[str]] = Field(description='List of suggested responses to the customer claim', default=None)
