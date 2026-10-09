# Process a document corpus in one batch

Extraction, classification and tagging over a pile of documents is work nobody is waiting
on row by row. This example queues a whole corpus on the batch tier as one batch: each
support ticket comes back as a category, a priority, tags, the order number and a
one-sentence summary.

At batch prices you can afford to ask twice. Every ticket is processed two times, and
agreement between the two answers is the confidence signal: rows where they agree are
trusted, rows where they disagree go to a person.

## Run it

```bash
export VORQ_WALLET_KEY=0x...
uv run main.py
```

## What you need

Python 3.11+ and a wallet holding test USDC (see the [repo README](../README.md)).

## What happens

1. **Queue.** Every row becomes `RUNS` lines of a batch. Each line is sealed to the provider
   that will run it before it leaves your machine.
2. **Wait.** The script waits for the batch to finish.
3. **Collect.** Tickets whose runs agree on the category go to `results.jsonl`, the
   rest to `review.jsonl`.

The sample in `data/tickets.jsonl` is synthetic and labelled, so the run also prints
accuracy for both groups: the agreed rows should be right far more often.
