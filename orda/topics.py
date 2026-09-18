"""Layered topic identification (simple-first, v0.1 keyword/metadata only).

Layer A: explicit slug (/slug prefix or `orda continue <slug>` verb).
Layer B: metadata + bounded keyword search over slugs + <=500-char summaries.
Layer C (applied by router): confidence floor + ambiguous-margin check.

The router NEVER opens transcripts or Eldunari events.jsonl; it sees slugs
plus short summaries only. No embeddings dependency in v0.1.
"""

import re

from . import TOPIC_SEARCH_K

EXPLICIT_RE = re.compile(r"^\s*/([\w][\w\-]*)\b")
CONTINUE_VERB_RE = re.compile(r"^\s*orda\s+continue\s+([\w][\w\-]*)\b",
                              re.IGNORECASE)

STOPWORDS = frozenset(
    "a an the and or but of to in on for with is are was were be been "
    "it its this that these those i you he she we they my your his her "
    "our their me him us them what when where which who how do does did "
    "not no yes if then than so as at by from about into over after "
    "please thanks thank hi hello hey issue problem question help need "
    "there here out up down just can could should would will".split()
)


def tokenize(text):
    return [t for t in re.findall(r"[a-z0-9]+", text.lower())
            if t not in STOPWORDS]


def jaccard(a_tokens, b_tokens):
    a, b = set(a_tokens), set(b_tokens)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def find_explicit_slug(text):
    m = EXPLICIT_RE.match(text) or CONTINUE_VERB_RE.match(text)
    return m.group(1).lower() if m else None


def rank_candidates(message_text, sessions, k=TOPIC_SEARCH_K):
    """Rank session catalog entries. Returns top-K list of
    {slug, session_id, score, source} sorted by score desc."""
    cands = []
    slug = find_explicit_slug(message_text)
    if slug:
        for s in sessions:
            if s.get("slug", "").lower() == slug:
                return [{"slug": s["slug"],
                         "session_id": s["session_id"],
                         "score": 1.0,
                         "source": "explicit"}]
        # Explicit slug naming a missing session: still report it so the
        # router can create/route deliberately instead of guessing.
        return [{"slug": slug, "session_id": None, "score": 1.0,
                 "source": "explicit-missing"}]

    lowered = message_text.lower()
    msg_tokens = tokenize(message_text)
    for s in sessions:
        sess_slug = str(s.get("slug", ""))
        slug_words = sess_slug.lower().replace("-", " ").replace("_", " ")
        score, source = 0.0, "keyword"
        if sess_slug.lower() == lowered.strip():
            score, source = 0.9, "exact-slug"
        elif slug_words and slug_words in lowered:
            score, source = 0.9, "slug-substring"
        else:
            summary = str(s.get("summary", ""))
            j = jaccard(msg_tokens, tokenize(slug_words + " " + summary))
            score = j
        if score > 0.0:
            cands.append({"slug": sess_slug,
                          "session_id": s.get("session_id"),
                          "score": round(score, 4),
                          "source": source})
    cands.sort(key=lambda c: (-c["score"], c["slug"]))
    return cands[:k]
