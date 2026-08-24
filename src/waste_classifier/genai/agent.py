"""A tool-calling recycling agent built on Groq function calling.

Unlike the plain RAG assistant (assistant.py), this runs a real agent loop: the
LLM is given a set of tools and autonomously decides which to call (and with what
arguments) to answer the user. We execute the requested tools, feed the results
back, and let the model continue until it produces a final answer. The list of
tools it actually invoked is returned alongside the answer so the UI can show the
agent's reasoning trace.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from waste_classifier import config
from waste_classifier.genai.groq_client import get_client, safe_call
from waste_classifier.genai.tools import TOOL_SCHEMAS, execute_tool

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 4  # safety cap on the agent loop

SYSTEM_PROMPT = """\
You are a recycling assistant agent embedded in a waste-classification app. You
have tools to look up material-specific recycling guides, check recyclability,
and estimate the CO2 impact of recycling. Prefer calling a tool over guessing
whenever a question is about a specific material's rules, recyclability, or
environmental impact. You may call multiple tools before answering. After
gathering what you need, give a short, practical answer (2-5 sentences). Never
invent local regulations — recommend checking the user's local waste authority
for jurisdiction-specific rules.
"""


@dataclass
class AgentResult:
    answer: str
    tools_used: list[dict] = field(default_factory=list)


def run_agent(
    question: str,
    classification_label: str | None = None,
    history: list[dict] | None = None,
    language: str = "en",
) -> AgentResult:
    client = get_client()

    system_content = SYSTEM_PROMPT
    if classification_label:
        system_content += (
            f"\n\nThe user's uploaded image was just classified as: {classification_label}."
        )
    if language == "ur":
        system_content += "\n\nRespond to the user in Urdu (اردو)."

    messages: list[dict] = [{"role": "system", "content": system_content}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": question})

    tools_used: list[dict] = []

    for _ in range(MAX_TOOL_ROUNDS):
        response = safe_call(
            client.chat.completions.create,
            model=config.GROQ_MODEL,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
            temperature=0.3,
        )
        message = response.choices[0].message

        if not message.tool_calls:
            return AgentResult(answer=message.content or "", tools_used=tools_used)

        # Record the assistant's tool-call turn, then execute each requested tool.
        messages.append(
            {
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in message.tool_calls
                ],
            }
        )

        for tc in message.tool_calls:
            result = execute_tool(tc.function.name, tc.function.arguments)
            tools_used.append({"name": tc.function.name, "arguments": tc.function.arguments})
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": tc.function.name,
                    "content": json.dumps(result),
                }
            )

    # Tool-round cap reached — ask once more for a final answer without tools.
    final = safe_call(
        client.chat.completions.create,
        model=config.GROQ_MODEL,
        messages=messages,
        temperature=0.3,
    )
    return AgentResult(answer=final.choices[0].message.content or "", tools_used=tools_used)
