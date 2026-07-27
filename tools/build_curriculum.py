"""Merge the two design outputs into the app-facing curriculum manifest.

Reads the design provenance (docs/design/*.raw.json) and emits
curriculum/curriculum.json — the single file the Flutter app reads at boot to
render the Act -> Chapter -> Level map and gate unlocks.

Integration decisions applied here (see docs/CURRICULUM.md):
  * Act 0 keeps only the true primitives; pattern "tours" become each chapter's
    L1 primer (designed by the chapters workflow), so nothing is duplicated.
  * A synthetic "walking-the-tape" tour is inserted after pointers (the linear
    scan the primers assumed but none taught).
  * Tries is placed in Act III (after backtracking) — the dependency fix the
    chapters synthesis verified.
"""

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOUND = os.path.join(ROOT, "docs/design/foundations.raw.json")
CHAP = os.path.join(ROOT, "docs/design/chapters.raw.json")
OUT = os.path.join(ROOT, "curriculum/curriculum.json")

# Act 0 keeps only the pre-pattern primitives (the rest are chapter L1 primers).
FOUNDATION_TOURS = [
    ("arrays-and-indices", "Arrays & Indices", "A fixed row of numbered crates; reading one by its index is instant."),
    ("pointers-cursors", "Pointers", "A pointer is just a stored number that marks a position; moving it is i = i + 1."),
    ("walking-the-tape", "Walking the Tape", "One robot visits every crate once; the STEPS meter counts to N. Grounds step / work / N."),
    ("fast-vs-slow-bigo", "Fast vs Slow (Big-O)", "Touch each thing once (O(n)) vs check every pair (O(n^2)); why it matters only when N is big."),
    ("why-sorting-helps", "Why Sorting Helps", "On sorted data one comparison rules out a whole region."),
    ("hashing-o1-lookup", "Hashing", "A wall of labelled mailboxes: 'have I seen X?' is instant instead of a re-scan; pay memory, buy speed."),
]

# Acts I-III chapter membership + order (topo-fixed: tries in Act III).
ACTS = [
    {"id": "foundations", "order": 0, "title": "Act 0 - Foundations",
     "subtitle": "How data is stored, read, and measured", "chapters": ["foundations"]},
    {"id": "linear", "order": 1, "title": "Act I - Linear",
     "subtitle": "Tapes, windows, piles, halving",
     "chapters": ["arrays-hashing", "two-pointers", "sliding-window", "stack", "binary-search"]},
    {"id": "linked-recursive", "order": 2, "title": "Act II - Linked & Recursive",
     "subtitle": "Nodes, self-reference, trees, heaps",
     "chapters": ["linked-list", "recursion", "trees", "heaps"]},
    {"id": "search-optimize", "order": 3, "title": "Act III - Search & Optimize",
     "subtitle": "Explore, prune, memoize, commit",
     "chapters": ["backtracking", "graphs", "tries", "greedy", "intervals", "dynamic-programming"]},
]

PASS_BY_KIND = {
    "primer": "viewed", "tutorial": "viewed",
    "guided": "correct", "open": "correct",
    "optimize": "correct+withinBudget", "boss": "correct+withinBudget",
}


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def load(path):
    with open(path) as fh:
        return json.load(fh)["result"]


def build_foundations():
    primers = {p["concept"]: p for p in load(FOUND).get("primers", [])}
    levels = []
    for i, (key, title, teaches) in enumerate(FOUNDATION_TOURS, start=1):
        p = primers.get(key, {})
        levels.append({
            "id": "foundations.l%d" % i,
            "order": i,
            "name": title,
            "kind": "primer",
            "difficulty": 1,
            "problemText": p.get("plainDefinition", teaches),
            "teaches": teaches,
            "engineLevelId": "foundations/%s" % key,
            "targetComplexity": None,
            "passRequires": "viewed",
        })
    return {
        "id": "foundations", "actId": "foundations", "order": 1,
        "title": "Foundations: The Tape, the Robot, the Cost",
        "oneLineGoal": "Understand arrays, indices, pointers, cost, and hashing from zero - no problems, just poke and watch.",
        "mechanism": "Everything downstream is a tape of crates read by pointer-robots; a step is one unit of work.",
        "prereqChapters": [], "bossCombinesWith": [],
        "unlockRule": "free", "levelUnlockRule": "sequential",
        "levels": levels,
    }


def build_pattern_chapters():
    raw = {c["chapterKey"]: c for c in load(CHAP).get("fullChapters", [])}
    act_of = {}
    for act in ACTS:
        for ck in act["chapters"]:
            act_of[ck] = act["id"]

    chapters = []
    for act in ACTS:
        order_in_act = 0
        for ck in act["chapters"]:
            if ck == "foundations":
                continue
            c = raw.get(ck)
            if not c:
                continue
            order_in_act += 1
            levels = []
            for lv in sorted(c.get("levels", []), key=lambda x: x.get("order", 0)):
                kind = lv.get("kind", "open")
                levels.append({
                    "id": "%s.l%s" % (ck, lv.get("order")),
                    "order": lv.get("order"),
                    "name": lv.get("name"),
                    "kind": kind,
                    "difficulty": lv.get("difficulty"),
                    "problemText": lv.get("problem"),
                    "teaches": lv.get("teaches"),
                    "engineLevelId": "%s/%s" % (ck, slug(lv.get("name", ""))),
                    "targetComplexity": None,  # TODO: fill per-level for optimize/boss brown-out
                    "passRequires": PASS_BY_KIND.get(kind, "correct"),
                })
            chapters.append({
                "id": ck,
                "actId": act["id"],
                "order": order_in_act,
                "title": c.get("title"),
                "oneLineGoal": c.get("oneLineGoal"),
                "mechanism": c.get("mechanismInOneSentence"),
                "prereqChapters": c.get("prereqChapters", []),
                "bossCombinesWith": [c.get("bossCombinesWith", "")] if c.get("bossCombinesWith") else [],
                "unlockRule": "allPrereqsCleared",
                "levelUnlockRule": "sequential",
                "levels": levels,
            })
    return chapters


def main():
    foundations = build_foundations()
    pattern = build_pattern_chapters()
    all_chapters = [foundations] + pattern

    manifest = {
        "version": 1,
        "acts": [{k: a[k] for k in ("id", "order", "title", "subtitle", "chapters")} for a in ACTS],
        "chapters": all_chapters,
    }
    with open(OUT, "w") as fh:
        json.dump(manifest, fh, indent=2)

    total_levels = sum(len(c["levels"]) for c in all_chapters)
    print("wrote %s" % OUT)
    print("  acts:     %d" % len(manifest["acts"]))
    print("  chapters: %d" % len(all_chapters))
    print("  levels:   %d" % total_levels)
    for c in all_chapters:
        print("    %-20s %2d levels  (act %s)" % (c["id"], len(c["levels"]), c["actId"]))


if __name__ == "__main__":
    main()
