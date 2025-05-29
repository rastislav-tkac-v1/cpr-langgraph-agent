
from typing import List, Optional

from langchain_core.documents import Document
from langchain_openai import AzureChatOpenAI

from langgraph.prebuilt import create_react_agent

from langchain_community.vectorstores.azuresearch import AzureSearch

from cpr_langgraph_agent.agent_prompt import AGENT_PROMPT_2
from cpr_langgraph_agent.models import Ticket, Customer, ConsumptionPoint, Contract, Payment
from cpr_langgraph_agent.crm_client import AsyncCrmClient
from cpr_langgraph_agent.state_models import AgentStateModel

class ReActAgent:
    def __init__(self, llm: AzureChatOpenAI, search: AzureSearch, crm_client: AsyncCrmClient):
        self.agent = create_react_agent(
            model=llm,
            tools=[
                self.find_relevant_claims, 
                self.get_customer_by_email, 
                self.get_customer_consumption_points,
                self.get_customer_contracts,
                self.get_contract_payments
            ],
            prompt=AGENT_PROMPT_2
        )
        with open("doc/cpr_langgraph_agent.png", "wb") as f:
            f.write(self.agent.get_graph().draw_mermaid_png())
        
        self.search = search
        self.crm_client = crm_client


    async def find_relevant_claims(self, search_term: str) -> List[Ticket]:
        """Use this tool to find relevant customer claim and complaint tickets"""
        search_result: Document = await self.search.asemantic_hybrid_search(
            query=search_term,
            k=5,
        )
        response = []
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
            response.append(ticket)
        return response
    
    async def get_customer_by_email(self, email: str) -> Customer:
        """
        Use this tool to retrieve customer details from CRM by email address
        """
        return await self.crm_client.get_customer_by_email(email)
    
    async def get_customer_consumption_points(self, customer_id: str, product_family: Optional[str] = None) -> List[ConsumptionPoint]:
        """
        Use this tool to retrieve customer consumption points by customer id. 
        Optionally you can filter consumption points by product family ('electricity' or 'gas')
        """
        return await self.crm_client.get_customer_consumption_points(customer_id, product_family=product_family)

    async def get_customer_contracts(self, customer_id: str) -> List[Contract]:
        """
        Use this tool to retrieve customer contracts by customer id. 
        """
        return await self.crm_client.get_customer_contracts(customer_id)
    
    async def get_contract_payments(self, customer_id: str, contract_id: str) -> List[Payment]:
        """
        Use this tool to retrieve contract payments by customer id and contract id. 
        """
        return await self.crm_client.get_customer_payments(customer_id, contract_id)