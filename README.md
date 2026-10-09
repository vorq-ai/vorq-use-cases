# VORQ use cases

Runnable Python examples for the workloads VORQ is built for: high-volume,
latency-tolerant inference on open-weight models, paid per job from your own wallet.
Each folder is one use case, stands alone, and uses the [`vorq`](https://pypi.org/project/vorq/)
client SDK.

| Example | What it does | SLA tier |
|---|---|---|
| [model-router](./model-router/) | An agent brain: a decision model on your machine picks the network model for every request | Async |
| [self-evolving-agents](./self-evolving-agents/) | Evolves a system prompt against a labelled task set, generation by generation | Async |
| [deep-research](./deep-research/) | A recursive research agent that reads sources and writes a cited report | Async |
| [synthetic-data](./synthetic-data/) | Generates, scores and filters fine-tuning conversations | Async |
| [media-generation](./media-generation/) | Fans out a file of renders and downloads the outputs | Batch |
| [data-processing](./data-processing/) | Classifies, tags and extracts fields from a corpus in one batch | Batch |

## Get started

You need Python 3.11+ and a wallet. There is no account and no API key: the wallet signs
each job and pays for it.

```bash
git clone https://github.com/vorq-ai/vorq-use-cases.git
cd vorq-use-cases/data-processing
export VORQ_WALLET_KEY=0x...      # a dedicated wallet, not your main one
uv run main.py                    # or: pip install vorq && python main.py
```

VORQ runs on Base Sepolia today and jobs are paid in test USDC. Get some from
[faucet.circle.com](https://faucet.circle.com) (choose USDC on Base Sepolia). You need no
ETH; the network pays the gas.

## Two tiers

- **Async** finishes within an hour. Use it when the next step waits on the answer:
  agents, chained pipelines, anything that runs in rounds.
- **Batch** finishes within a day at the lowest price. Use it for a single pass over a
  lot of work that nobody is waiting on.

Every example is one short `main.py` with its tier, model and sizes written at the top.
They follow the happy path only, to keep the idea readable: add your own error handling
before running them at scale.

## Licence

Apache-2.0. See [LICENSE](./LICENSE).
