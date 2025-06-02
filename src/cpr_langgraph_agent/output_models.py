from pydantic import BaseModel, Field
from typing import List, Optional

class AgentOutput(BaseModel):
    suggested_responses: Optional[List[str]] = Field(description='List of suggested responses to the customer claim', default=None)