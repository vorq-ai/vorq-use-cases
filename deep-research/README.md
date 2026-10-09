# Run a research agent that fans out instead of queueing up

A research agent chains many calls for one question. This one runs them in rounds: the
question is split into sub-questions, one agent per sub-question reads its sources, any
agent may ask deeper questions, and a last pass writes a cited report. All the agents
waiting in a round go out together as one batch.

## Run it

```bash
export VORQ_WALLET_KEY=0x...
uv run main.py "Why did the Bronze Age civilisations of the eastern Mediterranean collapse?"
```

The report lands in `report.md`.

## What you need

Python 3.11+ and a wallet holding test USDC (see the [repo README](../README.md)).
Sources come from Wikipedia's public API, so there is no search key to get.

## What happens

1. **Plan.** One job splits the question into `BREADTH` sub-questions, each with a
   search query.
2. **Read.** For every sub-question the script fetches `PAGES` sources, and one agent
   writes notes from them and asks `FOLLOW_UPS` deeper questions.
3. **Go deeper.** The follow-ups become the next round, for `DEPTH` rounds.
4. **Report.** One job writes the report from all the notes, citing source titles.

Rounds run on the async tier because each one is built from the last. Time is the scarce
thing here, not tokens, so the tree is built wide: the script searches for an agent before
its round starts, and no round is spent waiting on a search call.
