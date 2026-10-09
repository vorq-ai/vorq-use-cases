# Generate fine-tuning data, then throw the worst fifth away

When generation is cheap you stop rationing it. This example over-generates
customer-support conversations, has the model score every one, and drops the bottom 20%
before writing the fine-tuning file.

## Run it

```bash
export VORQ_WALLET_KEY=0x...
uv run main.py
```

## What you need

Python 3.11+ and a wallet holding test USDC (see the [repo README](../README.md)).

## What happens

Three stages, each one batch on the async tier, each built from the answers of the one
before:

1. **Scenarios.** A grid of topics and difficulty levels, a handful of scenarios per
   cell. The grid is what controls coverage.
2. **Conversations.** One support chat per scenario, as a `messages` list.
3. **Scores.** Each chat is rated 1 to 10 for realism, resolution and tone.

Chats that open with the same customer line are collapsed to one, then the lowest-scored
20% are dropped. `train.jsonl` holds the rest, one
`{"messages": [...]}` object per line.
