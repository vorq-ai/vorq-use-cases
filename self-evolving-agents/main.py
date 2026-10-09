"""Evolve a system prompt: score a population of prompts on a labelled task set, let the
model rewrite the best ones from their own mistakes, repeat. The weights never change."""

import asyncio
import json
import re
from pathlib import Path

import vorq

MODEL = "moonshotai/kimi-k3"
SLA = "async"  # each generation is built from the previous one's scores

GENERATIONS = 3
KEEP = 2  # prompts that survive each generation
CHILDREN = 2  # rewrites per surviving prompt
TRAIN = 12  # tasks used to score; the rest are held out

SEED_PROMPT = "Solve the problem."
ANSWER_FORMAT = "Finish with a line of the form `ANSWER: <integer>`."

REWRITE = """Below is a system prompt given to a model that solves word problems, and problems it got wrong.

System prompt:
{prompt}

Accuracy: {correct}/{total}

Mistakes:
{mistakes}

Write a better system prompt. Rewrite attempt {attempt}: take a different angle from an obvious one.
Return only the new system prompt, with no preamble."""


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


async def evaluate(client: vorq.Client, prompts: list[str], tasks: list[dict]) -> list[dict]:
    """Every prompt on every task, as one batch. Returns one score row per prompt."""
    answers = await ask(
        client,
        [f"{prompt}\n\n{ANSWER_FORMAT}\n\nProblem: {task['question']}" for prompt in prompts for task in tasks],
    )
    rows = []
    for i, prompt in enumerate(prompts):
        mistakes = []
        for task, answer in zip(tasks, answers[i * len(tasks) :]):
            got = int(re.findall(r"ANSWER: (-?\d+)", answer)[-1])
            if got != task["answer"]:
                mistakes.append(f"- {task['question']}\n  answered {got}, correct is {task['answer']}")
        rows.append({"prompt": prompt, "correct": len(tasks) - len(mistakes), "mistakes": mistakes})
    return rows


async def main() -> None:
    tasks = [json.loads(line) for line in Path("data/tasks.jsonl").read_text().splitlines()]
    train, held_out = tasks[:TRAIN], tasks[TRAIN:]

    async with vorq.Client() as client:
        population = [SEED_PROMPT]
        for generation in range(GENERATIONS):
            scored = await evaluate(client, population, train)
            parents = sorted(scored, key=lambda row: row["correct"], reverse=True)[:KEEP]
            print(f"generation {generation}: best {parents[0]['correct']}/{len(train)}")
            rewrites = await ask(
                client,
                [
                    REWRITE.format(
                        prompt=parent["prompt"],
                        correct=parent["correct"],
                        total=len(train),
                        mistakes="\n".join(parent["mistakes"][:5]),
                        attempt=attempt + 1,
                    )
                    for parent in parents
                    for attempt in range(CHILDREN)
                ],
            )
            population = [parent["prompt"] for parent in parents] + [text.strip() for text in rewrites]

        best = max(await evaluate(client, population, train), key=lambda row: row["correct"])["prompt"]
        seed, evolved = await evaluate(client, [SEED_PROMPT, best], held_out)
        print(f"held-out tasks: seed prompt {seed['correct']}/{len(held_out)}, best prompt {evolved['correct']}/{len(held_out)}")

    Path("best_prompt.txt").write_text(best + "\n")


asyncio.run(main())
