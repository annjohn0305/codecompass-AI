from typing import Dict

from .qwen_agent import analyze_project


def architecture_agent(state: Dict):

    prompt = f"""
You are an expert software architect.

Analyze this software project.

Technologies:
{state.get('technologies', '')}

Total Files:
{state.get('total_files', 0)}

Lines Of Code:
{state.get('lines_of_code', 0)}

Classes:
{state.get('total_classes', 0)}

Functions:
{state.get('total_functions', 0)}

Large Files:
{state.get('large_files', 0)}

Test Files:
{state.get('test_files', 0)}

Project Code Summary:
{state.get('project_summary', '')[:1000]}

Return your response EXACTLY in this format:

ARCHITECTURE:
<architecture analysis>

TECHNICAL_DEBT:
<technical debt analysis>

RISK:
<risk analysis>

RECOMMENDATIONS:
<recommendations>
"""

    full_report = analyze_project(
        prompt
    )

    state["full_report"] = (
        full_report
    )

    try:

        architecture = (
            full_report
            .split("ARCHITECTURE:")[1]
            .split("TECHNICAL_DEBT:")[0]
            .strip()
        )

    except:

        architecture = full_report

    state[
        "architecture_report"
    ] = architecture

    return state


def technical_debt_agent(state: Dict):

    report = state.get(
        "full_report",
        ""
    )

    try:

        section = (
            report
            .split("TECHNICAL_DEBT:")[1]
            .split("RISK:")[0]
            .strip()
        )

    except:

        section = report

    state[
        "technical_debt_report"
    ] = section

    return state


def risk_agent(state: Dict):

    report = state.get(
        "full_report",
        ""
    )

    try:

        section = (
            report
            .split("RISK:")[1]
            .split("RECOMMENDATIONS:")[0]
            .strip()
        )

    except:

        section = report

    state[
        "risk_report"
    ] = section

    return state


def recommendation_agent(state: Dict):

    report = state.get(
        "full_report",
        ""
    )

    try:

        section = (
            report
            .split("RECOMMENDATIONS:")[1]
            .strip()
        )

    except:

        section = report

    state[
        "recommendation_report"
    ] = section

    return state