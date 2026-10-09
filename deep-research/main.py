"""A recursive research agent. The question is split into sub-questions, each one reads
its sources and may ask deeper questions, and a last pass writes the report. Every
round is one batch holding all the agents that are waiting."""

import asyncio
import json
import sys
from pathlib import Path

import httpx
import vorq

MODEL = "moonshotai/kimi-k3"
SLA = "async"  # rounds chain: each one is built from the answers of the last

BREADTH = 4  # sub-questions from the plan
DEPTH = 2  # rounds of reading
FOLLOW_UPS = 2  # deeper questions one agent may ask
PAGES = 2  # sources per agent

WIKIPEDIA = "https://en.wikipedia.org/w/api.php"

PLAN = """You are planning research on this question:
{question}

Split it into {n} sub-questions that together answer it. For each, give a short
Wikipedia search query. Return one JSON object and nothing else:
{{"questions": [{{"question": "...", "query": "..."}}]}}"""

READ = """You are one agent in a research team working on: {root}

Your sub-question: {question}

Sources:
{sources}

Write notes that answer your sub-question from these sources only, naming the source
title for each claim. Then ask {n} follow-up questions on what is still open, each with
a Wikipedia search query.
Return one JSON object and nothing else:
{{"notes": "...", "follow_ups": [{{"question": "...", "query": "..."}}]}}"""

REPORT = """Write a research report answering: {question}

Use only the notes below. Structure it with markdown headings, state where the notes
disagree or leave a gap, and cite source titles in brackets.

{notes}"""


async def ask(client: vorq.Client, prompts: list[str]) -> list[str]:
    """One batch: a prompt per line in, the answers out in the same order."""
    lines = [
        {"custom_id": str(i), "url": "/v1/responses", "body": {"model": MODEL, "input": prompt}}
        for i, prompt in enumerate(prompts)
    ]
    batch = await client.batches.submit(lines, SLA)
    results = await batch.results()
    print(f"{len(results)} answers, ${sum(float(result.cost) for result in results):.4f}")
    return [result.text for result in sorted(results, key=lambda result: int(result.custom_id))]


def parse(text: str) -> dict:
    return json.loads(text[text.index("{") : text.rindex("}") + 1])


async def sources_for(http: httpx.AsyncClient, query: str) -> str:
    """The top Wikipedia pages for a query, as plain text under their titles."""
    found = await http.get(
        WIKIPEDIA, params={"action": "query", "list": "search", "srsearch": query, "srlimit": PAGES, "format": "json"}
    )
    pages = []
    for hit in found.json()["query"]["search"]:
        reply = await http.get(
            WIKIPEDIA,
            params={"action": "query", "prop": "extracts", "explaintext": 1, "titles": hit["title"], "format": "json"},
        )
        page = next(iter(reply.json()["query"]["pages"].values()))
        pages.append(f"## {page['title']}\n{page['extract'][:6000]}")
    return "\n\n".join(pages)


async def main() -> None:
    question = sys.argv[1]
    http = httpx.AsyncClient(headers={"User-Agent": "vorq-use-cases/0.1 (deep-research example)"})

    async with http, vorq.Client() as client:
        [plan] = await ask(client, [PLAN.format(question=question, n=BREADTH)])
        pending = parse(plan)["questions"]

        notes = []
        for _ in range(DEPTH):
            # Search before the round, not inside it: no agent spends a round asking for
            # sources, so the tree grows wide instead of deep and every round does real work.
            sources = await asyncio.gather(*[sources_for(http, node["query"]) for node in pending])
            answers = await ask(
                client,
                [
                    READ.format(root=question, question=node["question"], sources=text, n=FOLLOW_UPS)
                    for node, text in zip(pending, sources)
                ],
            )
            answers = [parse(answer) for answer in answers]
            notes += [f"### {node['question']}\n{answer['notes']}" for node, answer in zip(pending, answers)]
            pending = [follow_up for answer in answers for follow_up in answer["follow_ups"]]

        [report] = await ask(client, [REPORT.format(question=question, notes="\n\n".join(notes))])

    Path("report.md").write_text(report + "\n")
    print("Report -> report.md")


asyncio.run(main())
