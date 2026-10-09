"""An agent brain that owns its routing: a decision model running on this machine picks,
for every request, which model on the network should answer it.

The routing table is models.json. The decision model is Laya, served locally by Ollama.
It is not a chat model: it reads the request and the table and scores every row in one
pass, in milliseconds, and nothing leaves the machine until it has chosen."""

import asyncio
import json
from pathlib import Path

import httpx
import vorq

SLA = "async"  # an agent is waiting on each answer
LAYA = "laya"  # the Ollama tag of the decision model
OLLAMA = "http://localhost:11434"

QUESTION = "Which kind of task is this request?"


def decide(table: list[dict], request: str) -> dict:
    """Ask Laya which row of the table takes this request."""
    reply = httpx.post(
        f"{OLLAMA}/v1/systemone",
        timeout=120,
        json={
            "model": LAYA,
            "state": request,
            "questions": {
                "task": {
                    "type": "choice",
                    "instructions": QUESTION,
                    # The options are the table: Laya cannot pick a row that is not in it.
                    "criteria": {row["task"]: row["use_for"] for row in table},
                }
            },
        },
    )
    return reply.json()["answers"]["task"]


async def main() -> None:
    table = json.loads(Path("models.json").read_text())
    requests = Path("requests.txt").read_text().splitlines()
    decisions = [decide(table, request) for request in requests]
    models = {row["task"]: row["model"] for row in table}

    async with vorq.Client() as client:
        jobs = await asyncio.gather(
            *[
                client.submit(model=models[decision["choice"]], input=request, sla=SLA)
                for request, decision in zip(requests, decisions)
            ]
        )
        results = await asyncio.gather(*[job.result() for job in jobs])

    for request, decision, result in zip(requests, decisions, results):
        print(f"\n> {request}")
        print(f"  {decision['choice']} -> {models[decision['choice']]}  (confidence {decision['confidence']:.2f})  ${result.cost}\n")
        print(result.text.strip())


asyncio.run(main())
