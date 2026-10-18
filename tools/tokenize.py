"""Encode the hero's prompt and answer with the real cl100k_base tokenizer.

Usage (offline, once after editing llm.prompt or llm.answer in i18n/*.json):
    pip install tiktoken
    python tools/tokenize.py

Writes data/tokens.json, which tools/build.py reads. The build checks that the tokens
still spell the current prompt and answer, and stops if they are out of date, so the
ids on the page are always the real ones. This script is the only part of the site
that needs a third-party package, and it never runs in the deployment workflow.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENCODING = "cl100k_base"
EOS = "<|endoftext|>"


def encode(enc, text):
    """Token texts with their ids. A token that is only part of a UTF-8 character is
    merged with the next one, so every chip shows readable text; its ids are kept."""
    tokens, pending, ids = [], b"", []
    for token_id in enc.encode(text):
        pending += enc.decode_single_token_bytes(token_id)
        ids.append(token_id)
        try:
            piece = pending.decode("utf-8")
        except UnicodeDecodeError:
            continue
        tokens.append({"t": piece, "id": ids[0] if len(ids) == 1 else ids})
        pending, ids = b"", []
    if pending:
        raise SystemExit(f"could not decode the end of {text!r}")
    return tokens


def main():
    try:
        import tiktoken
    except ImportError:
        sys.exit("tiktoken is not installed: pip install tiktoken")
    enc = tiktoken.get_encoding(ENCODING)
    site = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))
    out = {
        "tokenizer": ENCODING,
        "eos": {"t": EOS, "id": enc.encode(EOS, allowed_special={EOS})[0]},
    }
    for language in site["languages"]:
        code = language["code"]
        llm = json.loads((ROOT / "i18n" / f"{code}.json").read_text(encoding="utf-8"))["llm"]
        out[code] = {"prompt": encode(enc, llm["prompt"]), "answer": encode(enc, llm["answer"])}
        print(f"{code}: {len(out[code]['prompt'])} prompt tokens, {len(out[code]['answer'])} answer tokens")
    path = ROOT / "data" / "tokens.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
