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
estimate the CO2 impact of recycling, and estimate approximate local scrap resale
value. Prefer calling a tool over guessing whenever a question is about a specific
material's rules, recyclability, environmental impact, or resale value. You may
call multiple tools before answering. After gathering what you need, give a short,
practical answer (2-5 sentences). Never invent local regulations — recommend
checking the user's local waste authority for jurisdiction-specific rules.
"""

# config.REGION == "pk": most of Pakistan has no municipal kerbside recycling —
# what exists instead is an informal scrap-dealer ("kabaria") resale economy. This
# addendum steers the agent away from assuming Western-style recycling bins.
SYSTEM_PROMPT_PK_ADDENDUM = """

Region note: the user is most likely in Pakistan. Assume there is no municipal \
kerbside recycling unless the user says otherwise — what actually exists locally is \
an informal scrap-dealer ("kabaria") resale economy. Some materials (metal, \
cardboard, paper, clean PET plastic bottles) can usually be sold by weight to a \
kabaria or scrap shop; others (most glass, "trash"-category items) typically have no \
local recovery path and go to general waste. Prefer the estimate_resale_value tool \
over the CO2 impact tool when the user is asking what something is "worth" locally.
"""

if config.REGION == "pk":
    SYSTEM_PROMPT += SYSTEM_PROMPT_PK_ADDENDUM


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
