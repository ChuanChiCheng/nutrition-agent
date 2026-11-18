"""Controller protocol and adapters over the existing application agent."""
from typing import Literal, Protocol

from nutrition_demo.agent import DemoAgent
from nutrition_demo.models import Result


class Controller(Protocol):
    def handle(self, message: str) -> Result: ...

    def approve(self, preview_id: str, outcome: Literal["approve", "reject"]) -> Result: ...


class AgentController:
    def __init__(self, agent: DemoAgent, workflow):
        self.agent = agent
        self.workflow = workflow

    def handle(self, message: str) -> Result:
        return self.agent.handle(message)

    def approve(self, preview_id: str, outcome: Literal["approve", "reject"]) -> Result:
        if outcome not in ("approve", "reject"):
            return Result(False, {}, "Approval outcome must be approve or reject")
        pending_preview = self.workflow.load().get("pending_preview")
        if not pending_preview or preview_id != pending_preview:
            return Result(False, {}, "Confirmation must match the current pending preview")
        command = "/confirm" if outcome == "approve" else "/reject"
        return self.agent.handle(f"{command} {pending_preview}")


def _application_settings(config):
    from nutrition_demo.agent import Settings

    return Settings(
        model=config.model_id,
        reasoning_effort=config.reasoning_effort,
        max_model_calls=config.max_model_calls,
        max_tool_calls=config.max_tool_calls,
        max_clarifications=config.max_clarifications,
        max_output_tokens=config.max_output_tokens,
    )


def _client(config):
    import os
    import openai

    return openai.OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_BASE_URL") or None,
        max_retries=0,
        timeout=config.timeout_seconds,
    )


def agent_factory(store, catalog, config, *, client=None) -> Controller:
    """Build a controller from safe runtime dependencies; no task or rubric enters."""
    from nutrition_demo.service import NutritionService
    from nutrition_demo.workflow import Workflow

    service = NutritionService(store, catalog, clock=lambda: config.now)
    workflow = Workflow(service, session_id="evaluation")
    settings = _application_settings(config)
    agent = DemoAgent(service, workflow, client or _client(config), settings)
    return AgentController(agent, workflow)
