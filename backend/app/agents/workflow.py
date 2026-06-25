import asyncio
from typing import Any, Dict
from app.agents.base import ADKContext, adk_node
from app.agents.commander import CommanderAgent

# Instantiate the Commander
commander = CommanderAgent()

@adk_node
async def run_commander_agent(prompt: str) -> Dict[str, Any]:
    """ADK Node wrapper executing the Commander orchestration."""
    return await commander.orchestrate(prompt)

@adk_node
async def humanityos_workflow(ctx: ADKContext, prompt: str) -> Dict[str, Any]:
    """Root ADK Workflow coordinating the incident response platform nodes."""
    # Execute the commander orchestration graph inside the ADK Context
    result = await ctx.run_node(run_commander_agent, {"prompt": prompt})
    return result

