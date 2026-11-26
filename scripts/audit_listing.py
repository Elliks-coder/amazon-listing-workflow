"""Measure listing text and report deterministic checks from supplied rules."""

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
import unicodedata


WORD = re.compile(r"[^\W_]+(?:['’][^\W_]+)*", re.UNICODE)
METRICS = ("characters", "utf8_bytes", "non_separator_utf8_bytes")
FRONTEND_FIELDS = ("title", "item_highlights", "bullet_points", "description")


def words(text):
    normalized = unicodedata.normalize("NFKC", text).casefold().replace("’", "'")
    return WORD.findall(normalized)


def field_texts(value, path):
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, list):
        for index, child in enumerate(value, start=1):
            yield from field_texts(child, f"{path}[{index}]")
    elif isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else key
            yield from field_texts(child, child_path)
    else:
        raise ValueError(f"Expected listing text at {path or 'fields'}")


def measures(text):
    without_separators = "".join(
        char for char in text
        if not char.isspace() and not unicodedata.category(char).startswith("P")
    )
    return {
        "characters": len(text),
        "utf8_bytes": len(text.encode("utf-8")),
        "non_separator_utf8_bytes": len(without_separators.encode("utf-8")),
    }


def check_limits(limits):
    for path, metrics in limits.items():
        for metric, limit in metrics.items():
            if metric not in METRICS:
                raise ValueError(f"Unknown limit metric for {path}: {metric}")
            if type(limit) is not int or limit < 0:
                raise ValueError(f"Expected a nonnegative integer limit for {path}")


def phrase_appears(text_words, phrase):
    phrase_words = words(phrase)
    size = len(phrase_words)
    return bool(size) and any(
        text_words[start:start + size] == phrase_words
        for start in range(len(text_words) - size + 1)
    )


def audit(data):
    fields = data["fields"]
    if not isinstance(fields, dict):
        raise ValueError("fields must be an object")
    limits = data.get("limits", {})
    blocked_terms = data.get("blocked_terms", {})
    blocked_characters = data.get("blocked_characters", {})
    repetition = data.get("title_repetition", {})
    check_limits(limits)
    repeat_max = repetition.get("max_occurrences")
    if repeat_max is not None and (type(repeat_max) is not int or repeat_max < 1):
        raise ValueError("title_repetition.max_occurrences must be a positive integer")
    title_exceptions = set(words(" ".join(repetition.get("ignore_words", []))))

    frontend_words = {}
    if data.get("search_terms_exclude_frontend", False):
        for field in FRONTEND_FIELDS:
            if field in fields:
                for path, text in field_texts(fields[field], field):
                    for token in set(words(text)):
                        frontend_words.setdefault(token, []).append(path)

    result = {"fields": {}, "issues": []}
    for path, text in field_texts(fields, ""):
        counts = measures(text)
        group = re.sub(r"\[\d+\]", "", path)
        active_limits = {**limits.get(group, {}), **limits.get(path, {})}
        result["fields"][path] = {**counts, "limits": active_limits}
        for metric, limit in active_limits.items():
            if counts[metric] > limit:
                result["issues"].append({
                    "field": path, "type": "over_limit", "metric": metric,
                    "actual": counts[metric], "limit": limit,
                })

        tokens = words(text)
        phrases = dict.fromkeys(blocked_terms.get(group, []) + blocked_terms.get(path, []))
        for phrase in phrases:
            if phrase_appears(tokens, phrase):
                result["issues"].append({
                    "field": path, "type": "blocked_term_match", "term": phrase,
                })

        forbidden = set(blocked_characters.get(group, "") + blocked_characters.get(path, ""))
        found = [char for char in dict.fromkeys(text) if char in forbidden]
        if found:
            result["issues"].append({
                "field": path, "type": "blocked_characters", "characters": found,
            })

        if path == "search_terms":
            for token, count in Counter(tokens).items():
                if count > 1:
                    result["issues"].append({
                        "field": path, "type": "repeated_search_term",
                        "term": token, "count": count,
                    })
                if token in frontend_words:
                    result["issues"].append({
                        "field": path, "type": "search_term_in_frontend",
                        "term": token, "used_in": frontend_words[token],
                    })
        if path == "title" and repeat_max is not None:
            for token, count in Counter(tokens).items():
                if count > repeat_max and token not in title_exceptions:
                    result["issues"].append({
                        "field": path, "type": "repeated_title_word",
                        "term": token, "count": count, "limit": repeat_max,
                    })
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", type=Path, help="UTF-8 JSON; defaults to stdin")
    args = parser.parse_args()
    try:
        raw = args.input.read_bytes() if args.input else sys.stdin.buffer.read()
        result = audit(json.loads(raw.decode("utf-8-sig")))
    except (KeyError, AttributeError, TypeError, ValueError, OSError) as error:
        parser.exit(2, f"Invalid audit input: {error}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
