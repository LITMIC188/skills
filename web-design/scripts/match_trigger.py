#!/usr/bin/env python3
"""Deterministic Web-Design trigger gate; no network or third-party packages."""

import argparse
import json
from pathlib import Path
import re
import sys
import unicodedata

REGISTRATION = Path(__file__).resolve().parents[1] / "references" / "registration.json"
DOMAINS = ("网页", "网站", "工作台布局", "React", "Next.js", "webapp")
ASCII_LOWER = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")


def normalize(text):
    """NFKC -> trim -> collapse Unicode whitespace -> fold ASCII English case."""
    return " ".join(unicodedata.normalize("NFKC", text).strip().split()).translate(ASCII_LOWER)


def load_registration():
    data = json.loads(REGISTRATION.read_text(encoding="utf-8"))
    if list(data) != ["name", "description", "triggers", "match_description"]:
        raise ValueError("Registration must contain exactly four ordered fields")
    expected = ["设计网页", "设计网站", "设计工作台布局", "skills<Web-Design>",
                "优化 React 页面性能", "优化 Next.js 页面性能", "测试 webapp"]
    if data["name"] != "Web-Design" or data["triggers"] != expected:
        raise ValueError("Registration name or ordered trigger contract changed")
    if not all(isinstance(data[k], str) and data[k].strip()
               for k in ("name", "description", "match_description")):
        raise ValueError("Registration string fields must be nonempty strings")
    return data


def match(text):
    registration = load_registration()
    terms = registration["triggers"]
    normalized = normalize(text)
    result = {"matched": False, "reason": "no_trigger", "normalized_input": normalized,
              "matched_triggers": [], "context_domains": []}
    if normalize(terms[3]) in normalized:
        result.update(matched=True, reason="explicit", matched_triggers=[terms[3]])
        return result
    core_hits = [term for term in terms[:3] if normalize(term) in normalized]
    if core_hits:
        result.update(matched=True, reason="core", matched_triggers=core_hits)
        return result

    spans = []
    extended_hits = []
    for term in terms[4:]:
        occurrences = list(re.finditer(re.escape(normalize(term)), normalized))
        if occurrences:
            extended_hits.append(term)
            spans.extend((m.start(), m.end()) for m in occurrences)
    if not spans:
        return result

    # Spaces retain boundaries; deleting spans could falsely join partial words.
    remaining = list(normalized)
    for start, end in spans:
        remaining[start:end] = " " * (end - start)
    context = "".join(remaining)
    domains = []
    for domain in DOMAINS:
        word = normalize(domain)
        if domain in DOMAINS[:3]:
            found = word in context
        else:
            found = re.search(r"(?<![a-z0-9_])" + re.escape(word) + r"(?![a-z0-9_])", context)
        if found:
            domains.append(domain)
    result.update(matched=bool(domains), matched_triggers=extended_hits, context_domains=domains,
                  reason="extended_with_domain" if domains else "extended_without_domain")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--text", help="Current user message")
    inputs.add_argument("--stdin", action="store_true", help="Read current message as UTF-8 from stdin")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if args.stdin and hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8", errors="strict")
    text = sys.stdin.read() if args.stdin else args.text
    print(json.dumps(match(text), ensure_ascii=False))


if __name__ == "__main__":
    main()
