from typing import List, Any

from langchain_openai import AzureChatOpenAI

from langgraph_supervisor import create_supervisor
from langgraph.checkpoint.base import BaseCheckpointSaver

from cpr_langgraph_agent.supervisor_agent_prompts import AGENT_PROMPT
from cpr_langgraph_agent.state_models import AgentStateModel


class SupervisorAgent:
    def __init__(self, llm: AzureChatOpenAI, agents: List[Any], checkpointer:  BaseCheckpointSaver):
        self.supervisor = create_supervisor(
            agents=agents,
            output_mode="full_history",
            model=llm,
            state_schema=AgentStateModel,
            prompt=AGENT_PROMPT,
        )
        self.agent = self.supervisor.compile(checkpointer=checkpointer)
        with open("doc/cpr_langgraph_supervisor_agent.png", "wb") as f:
            f.write(self.agent.get_graph().draw_mermaid_png())