# -*- coding: utf-8 -*-
"""Post-processing of the CSS bundle.

guard_hover(): hover styles only for devices that can hover.
On an iPhone a tap puts the element into :hover and it stays there until the next tap elsewhere, so a slider arrow
that turns green on hover stays green after it was pressed. Every selector with :hover is therefore moved into
@media (hover: hover); the rest of its selector list stays where it was, so on a desktop the cascade (order and
specificity) is exactly the same as in the source files. Rules already inside a hover media query, @keyframes,
@font-face and other non-conditional at-rules are left as they are.
"""
from __future__ import annotations

HOVER_QUERY = "(hover: hover)"
CONDITIONAL = ("@media", "@supports", "@container", "@layer", "@document")


def _skip_string(css: str, i: int) -> int:
    """Index right after the string that starts at css[i] (a quote)."""
    quote = css[i]
    i += 1
    while i < len(css):
        if css[i] == "\\":
            i += 2
            continue
        if css[i] == quote:
            return i + 1
        i += 1
    raise ValueError("незакрытая строка в CSS")


def _skip_comment(css: str, i: int) -> int:
    end = css.find("*/", i + 2)
    if end < 0:
        raise ValueError("незакрытый комментарий в CSS")
    return end + 2


def _match_brace(css: str, i: int) -> int:
    """Index of the "}" that closes the "{" at css[i]."""
    depth = 0
    while i < len(css):
        c = css[i]
        if c in "\"'":
            i = _skip_string(css, i)
            continue
        if css.startswith("/*", i):
            i = _skip_comment(css, i)
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError("незакрытая фигурная скобка в CSS")


def _items(css: str):
    """Top-level items: ("comment", text) | ("statement", text) | ("block", prelude, body)."""
    i, n = 0, len(css)
    while i < n:
        if css[i].isspace():
            i += 1
            continue
        if css.startswith("/*", i):
            j = _skip_comment(css, i)
            yield ("comment", css[i:j])
            i = j
            continue
        j, depth = i, 0
        while True:
            if j >= n:
                if css[i:].strip():
                    raise ValueError(f"обрывок CSS без блока: {css[i:i + 60]!r}")
                return
            c = css[j]
            if c in "\"'":
                j = _skip_string(css, j)
                continue
            if css.startswith("/*", j):
                j = _skip_comment(css, j)
                continue
            if c in "([":
                depth += 1
            elif c in ")]":
                depth -= 1
            elif c == ";" and depth == 0:
                yield ("statement", css[i:j + 1])
                i = j + 1
                break
            elif c == "{" and depth == 0:
                k = _match_brace(css, j)
                yield ("block", css[i:j].strip(), css[j + 1:k])
                i = k + 1
                break
            j += 1


def split_selectors(prelude: str) -> list[str]:
    """Selector list split on the commas that are not inside (), [] or strings."""
    parts, depth, start, i = [], 0, 0, 0
    while i < len(prelude):
        c = prelude[i]
        if c in "\"'":
            i = _skip_string(prelude, i)
            continue
        if c in "([":
            depth += 1
        elif c in ")]":
            depth -= 1
        elif c == "," and depth == 0:
            parts.append(prelude[start:i].strip())
            start = i + 1
        i += 1
    parts.append(prelude[start:].strip())
    return [p for p in parts if p]


def _has_hover(selector: str) -> bool:
    """:hover that makes the selector match only while hovered (not the negated one inside :not(), which touch keeps true)."""
    out, i = [], 0
    while i < len(selector):
        if selector.startswith(":not(", i):
            depth, j = 0, i + 4
            while j < len(selector):
                depth += {"(": 1, ")": -1}.get(selector[j], 0)
                if depth == 0:
                    break
                j += 1
            i = j + 1
            continue
        out.append(selector[i])
        i += 1
    return ":hover" in "".join(out)


def _process(css: str, in_hover: bool) -> str:
    out = []
    for item in _items(css):
        kind = item[0]
        if kind in ("comment", "statement"):
            out.append(item[1])
            continue
        prelude, body = item[1], item[2]
        if prelude.startswith("@"):
            name = prelude.split(None, 1)[0].lower()
            if name in CONDITIONAL:
                inner_hover = in_hover or (name == "@media" and "hover" in prelude.lower())
                out.append(f"{prelude} {{\n{_process(body, inner_hover)}\n}}")
            else:
                out.append(f"{prelude} {{{body}}}")
            continue
        selectors = split_selectors(prelude)
        hover = [s for s in selectors if _has_hover(s)]
        if in_hover or not hover:
            out.append(f"{prelude} {{{body}}}")
            continue
        plain = [s for s in selectors if not _has_hover(s)]
        if plain:
            out.append(f"{', '.join(plain)} {{{body}}}")
        out.append(f"@media {HOVER_QUERY} {{ {', '.join(hover)} {{{body}}} }}")
    return "\n".join(out)


def guard_hover(css: str) -> str:
    """The bundle with every :hover selector moved into @media (hover: hover); see the module docstring."""
    return _process(css, in_hover=False)
