from langgraph.graph import StateGraph
from typing import TypedDict

from .agents import (
    architecture_agent,
    technical_debt_agent,
    risk_agent,
    recommendation_agent
)


class ProjectState(TypedDict):

    total_files: int
    lines_of_code: int
    health_score: int
    technologies: str

    total_classes: int
    total_functions: int

    large_files: int
    test_files: int

    project_summary: str

    full_report: str

    architecture_report: str
    technical_debt_report: str
    risk_report: str
    recommendation_report: str


def build_workflow():

    workflow = StateGraph(
        ProjectState
    )

    workflow.add_node(
        "architecture",
        architecture_agent
    )

    workflow.add_node(
        "technical_debt",
        technical_debt_agent
    )

    workflow.add_node(
        "risk",
        risk_agent
    )

    workflow.add_node(
        "recommendation",
        recommendation_agent
    )

    workflow.set_entry_point(
        "architecture"
    )

    workflow.add_edge(
        "architecture",
        "technical_debt"
    )

    workflow.add_edge(
        "technical_debt",
        "risk"
    )

    workflow.add_edge(
        "risk",
        "recommendation"
    )

    workflow.set_finish_point(
        "recommendation"
    )

    return workflow.compile()