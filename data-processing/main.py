"""Classify, tag and extract fields from a document corpus in one batch.

Every document is processed twice. Where the two answers agree on the category the row
is trusted; where they disagree it goes to a review file instead."""

import asyncio
import json
from collections import Counter
from pathlib import Path

import vorq

MODEL = "moonshotai/kimi-k3"
SLA = "batch"  # one pass over a corpus, nobody waiting on a single row
RUNS = 2  # answers per document; agreement between them is the confidence signal

PROMPT = """You process customer support tickets. Return one JSON object and nothing else:
{{"category": "billing", "shipping", "technical", "account" or "returns",
  "priority": "low", "medium" or "high",
  "tags": up to three short lowercase tags,
  "order_id": the order number named in the ticket, or null,
  "summary": one sentence}}

Ticket:
{text}"""


def parse(text: str) -> dict:
    return json.loads(text[text.index("{") : text.rindex("}") + 1])


async def main() -> None:
    tickets = [json.loads(line) for line in Path("data/tickets.jsonl").read_text().splitlines()]
    lines = [
        {
            "custom_id": f"{ticket['id']}#{run}",
            "url": "/v1/responses",
            "body": {"model": MODEL, "input": PROMPT.format(text=ticket["text"])},
        }
        for ticket in tickets
        for run in range(RUNS)
    ]

    async with vorq.Client() as client:
        batch = await client.batches.submit(lines, SLA)
        results = await batch.results()

    answers = {result.custom_id: parse(result.text) for result in results}
    agreed, review = [], []
    for ticket in tickets:
        runs = [answers[f"{ticket['id']}#{run}"] for run in range(RUNS)]
        row = {"id": ticket["id"], "label": ticket["category"], **runs[0]}
        (agreed if len({run["category"] for run in runs}) == 1 else review).append(row)
    Path("results.jsonl").write_text("".join(json.dumps(row) + "\n" for row in agreed))
    Path("review.jsonl").write_text("".join(json.dumps(row) + "\n" for row in review))

    for category, count in Counter(row["category"] for row in agreed).most_common():
        print(f"{category:<10} {count}")
    for name, rows in ("agree", agreed), ("disagree", review):
        correct = sum(row["category"] == row["label"] for row in rows)
        print(f"Runs {name:<8}: {len(rows)} tickets, {correct} correct")
    print(f"Cost    : ${sum(float(result.cost) for result in results):.4f}")


asyncio.run(main())
