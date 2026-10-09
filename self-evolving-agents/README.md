# Let an agent improve its own system prompt

A system prompt is something you can optimise like any other parameter, without touching
model weights. This example runs a small evolutionary search: prompts are scored on a
labelled task set, the model rewrites the best ones after reading their own mistakes, and
the next generation is scored again.

## Run it

```bash
export VORQ_WALLET_KEY=0x...
uv run main.py
```

## What you need

Python 3.11+ and a wallet holding test USDC (see the [repo README](../README.md)).

## What happens

1. **Score.** Every prompt in the population answers every scoring task. That is one
   batch, on the async tier.
2. **Select.** The best `KEEP` prompts survive.
3. **Rewrite.** Each survivor is shown its accuracy and the problems it got wrong, and
   writes `CHILDREN` improved versions of itself. One more batch.
4. **Repeat** for `GENERATIONS`, starting from the seed prompt `Solve the problem.`
5. **Check.** The winner and the seed prompt both run on tasks neither has seen, so you
   can tell improvement from overfitting.

The winner is written to `best_prompt.txt`. It is plain text and works with any model.

The tasks in `data/tasks.jsonl` are multi-step word problems that each carry a number that
does not matter.
