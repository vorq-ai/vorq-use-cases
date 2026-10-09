"""Generate support conversations for fine-tuning: scenarios, conversations, quality
scores. Over-generate, then drop the lowest-scored fifth."""

import asyncio
import json
from pathlib import Path

import vorq

MODEL = "moonshotai/kimi-k3"
SLA = "async"  # three chained stages, each waiting on the one before

TOPICS = ["billing dispute", "late delivery", "login problem", "product defect", "plan upgrade"]
DIFFICULTIES = ["easy", "medium", "hard"]
PER_CELL = 2  # scenarios per topic and difficulty
DROP = 0.2

SCENARIOS = """Write {n} distinct customer-support scenarios about "{topic}" at {difficulty} difficulty.
Easy means one clear request; hard means an upset customer, missing information or a policy edge case.
Return one JSON object and nothing else: {{"scenarios": ["one or two sentences", ...]}}"""

CONVERSATION = """Write a realistic support chat for this scenario:
{scenario}

Four to eight turns, starting with the customer. The agent is concise, never invents policy,
and ends with a concrete next step.
Return one JSON object and nothing else:
{{"messages": [{{"role": "user" or "assistant", "content": "..."}}]}}"""

SCORE = """Rate this support chat as fine-tuning data, from 1 (unusable) to 10 (excellent).
Judge realism, whether the agent resolves the request, and tone.
Return one JSON object and nothing else: {{"score": integer, "reason": "one sentence"}}

{conversation}"""


async def ask(client: vorq.Client, prompts: dict[str, str]) -> dict[str, dict]:
    """One batch: a prompt per line in, the parsed JSON answers out under the same keys."""
    lines = [
        {"custom_id": key, "url": "/v1/responses", "body": {"model": MODEL, "input": prompt}}
        for key, prompt in prompts.items()
    ]
    batch = await client.batches.submit(lines, SLA)
    results = await batch.results()
    print(f"{len(results)} answers, ${sum(float(result.cost) for result in results):.4f}")
    return {
        result.custom_id: json.loads(result.text[result.text.index("{") : result.text.rindex("}") + 1])
        for result in results
    }


async def main() -> None:
    async with vorq.Client() as client:
        cells = await ask(
            client,
            {
                f"{topic}/{difficulty}": SCENARIOS.format(n=PER_CELL, topic=topic, difficulty=difficulty)
                for topic in TOPICS
                for difficulty in DIFFICULTIES
            },
        )
        scenarios = {f"{cell}/{i}": s for cell, answer in cells.items() for i, s in enumerate(answer["scenarios"])}

        conversations = await ask(client, {key: CONVERSATION.format(scenario=s) for key, s in scenarios.items()})

        scores = await ask(
            client,
            {key: SCORE.format(conversation=json.dumps(c["messages"], indent=1)) for key, c in conversations.items()},
        )

    # Two chats that open with the same customer line teach the same thing: keep one.
    unique = {c["messages"][0]["content"]: key for key, c in conversations.items()}.values()
    ranked = sorted(unique, key=lambda key: scores[key]["score"], reverse=True)
    kept = ranked[: round(len(ranked) * (1 - DROP))]
    Path("train.jsonl").write_text("".join(json.dumps(conversations[key]) + "\n" for key in kept))
    print(f"Kept {len(kept)} of {len(conversations)} conversations -> train.jsonl")


asyncio.run(main())
