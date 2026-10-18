"""Encode the hero chat's question and answer with the real cl100k_base tokenizer.

Local only: needs `pip install tiktoken` and is run by hand to regenerate
data/tokens.json. The GitHub workflow never runs or imports it; it only runs
tools/build.py, which reads the committed data/tokens.json.

Usage (once after editing chat.prompt or chat.answer in i18n/*.json):
    pip install tiktoken
    python tools/tokenize.py

The build checks that the tokens still spell the current question and answer, and
stops if they are out of date, so the ids on the page are always the real ones.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENCODING = "cl100k_base"


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
    out = {"tokenizer": ENCODING}
    for language in site["languages"]:
        code = language["code"]
        chat = json.loads((ROOT / "i18n" / f"{code}.json").read_text(encoding="utf-8"))["chat"]
        out[code] = {"prompt": encode(enc, chat["prompt"]), "answer": encode(enc, chat["answer"])}
        print(f"{code}: {len(out[code]['prompt'])} prompt tokens, {len(out[code]['answer'])} answer tokens")
    path = ROOT / "data" / "tokens.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
