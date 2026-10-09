# Render a file of clips in one pass

A render farm in one script: every line of a file is one render, they all go out
together, and the outputs come back to a folder. The price of each output is fixed when
the job is posted.

## Run it

```bash
export VORQ_WALLET_KEY=0x...
uv run main.py
```

Outputs land in `out/000/`, `out/001/`, ... in the order of the file.

## What you need

Python 3.11+ and a wallet holding test USDC (see the [repo README](../README.md)).

## The renders file

`renders.jsonl` holds one render per line: the model, and the input that model takes.

```json
{"model": "bytedance/seedance-2", "input": {"prompt": "a slow pan across a mountain valley at dawn", "resolution": "720p", "aspect_ratio": "16:9", "duration": 4}}
```

The script passes `input` through untouched. A different model, or an image model with
`width`, `height` and `num_images`, is a new line in this file and no change to the code.

## What happens

1. **Post.** Every line is submitted at once, on the batch tier.
2. **Wait.** The script waits for every render to finish.
3. **Download.** Each result is decrypted and written to its own folder.
