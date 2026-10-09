# Give your agent a brain it owns

An agent that sends everything to one model overpays for the easy requests. This example
puts the routing decision on your own machine: a local decision model, Laya, reads each
request and picks the network model that should answer it. The request then goes to
that model, paid from the agent's own wallet. No API key, no account.

Laya is not a chat model. It is a 421M-parameter decision model that scores every row
of the routing table in one pass, so a decision takes tens of milliseconds on a laptop
and comes with a confidence.

## Run it

```bash
ollama pull laya
export VORQ_WALLET_KEY=0x...
uv run main.py
```

## What you need

- Python 3.11+ and a wallet holding test USDC (see the [repo README](../README.md)).
- [Ollama](https://ollama.com) 0.40 or later, running locally. The Laya model is an
  846 MB download.

## The routing table

`models.json` is the whole routing policy: one row per kind of task, with a line
describing it and the model that takes it.

```json
{"task": "coding", "use_for": "Writing, debugging or refactoring source code.", "model": "moonshotai/kimi-k3"}
```

Laya chooses between the `task` names by reading the `use_for` lines, so both are plain
words about the request, not about the model. Its answer is one of the rows in this
file: it cannot route to a model you did not list.

## What happens

1. **Decide.** For each request, Laya gets the request and the table and returns a row
   and its confidence. This step is local.
2. **Send.** The request goes to the chosen model on the async tier, sealed to the
   provider that runs it.
3. **Answer.** The script prints each decision, its cost and the answer.

`requests.txt` is a mix of coding, reasoning and trivial requests, to show the spread.
