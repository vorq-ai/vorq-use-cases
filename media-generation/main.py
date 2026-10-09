"""Fan out a file of renders and download what comes back.

Each line of the renders file names a model and the input that model takes; the input
is passed through untouched, so a new model is a new line, not a code change."""

import asyncio
import json
from pathlib import Path

import vorq

SLA = "batch"  # independent renders, one pass, nobody waiting on a single output


async def main() -> None:
    renders = [json.loads(line) for line in Path("renders.jsonl").read_text().splitlines()]

    async with vorq.Client() as client:
        jobs = await asyncio.gather(
            *[client.submit(model=render["model"], input=render["input"], sla=SLA) for render in renders]
        )
        results = await asyncio.gather(*[job.result() for job in jobs])

    for i, result in enumerate(results):
        paths = result.download(Path("out") / f"{i:03d}")
        print(f"${result.cost}  {', '.join(str(path) for path in paths)}")


asyncio.run(main())
