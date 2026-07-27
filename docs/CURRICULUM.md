# DEREF — Master Curriculum

From zero to interview-ready, as **Acts → Chapters → Levels**, basics → advanced.
Machine-readable manifest: [`curriculum/curriculum.json`](../curriculum/curriculum.json)
(regenerate with `python3 tools/build_curriculum.py`). Full design provenance in
[`docs/design/`](./design/).

## How it's structured

- **Act** = a stage of the journey. **Chapter** = one concept family. **Level** = one step.
- Every chapter opens with a **no-fail primer** (poke-and-watch, difficulty 1) that rebuilds
  its mechanism from zero, then ramps to a **boss** that fuses in an earlier pattern.
- Level kinds: `primer` (watch) → `tutorial` (watch a solve) → `guided` (fill one line) →
  `open` (write it cold) → `optimize` (beat the brown-out) → `boss` (combine patterns).
- A chapter unlocks only when its prerequisites are **cleared**, so difficulty never cliffs:
  the *mechanical* floor resets to 1 each chapter while the *conceptual* ceiling rises.

## Integration decision (merging the two design passes)

Both design passes produced "primer" tours for the pattern concepts. To avoid duplication:
**Act 0 keeps only the true primitives**; each pattern's tour becomes its chapter's **L1
primer**. Act 0 = Arrays & Indices · Pointers · *Walking the Tape* · Fast-vs-Slow (Big-O) ·
Why Sorting Helps · Hashing. (Two Pointers, Stack, Trees, etc. are chapters, not Act-0 tours.)

## The tree (156 levels)

### Act 0 — Foundations · *no problems, just poke and watch* (6 tours)
Arrays & Indices → Pointers → Walking the Tape → Fast-vs-Slow (Big-O) → Why Sorting Helps → Hashing

### Act I — Linear
| Chapter | Lv | L1 primer | Boss (fuses) |
|---|----|---|---|
| **Arrays & Hashing** — The Mailbox Wall | 11 | The Mailbox Wall | Longest Consecutive Sequence *(sorting→hash)* |
| **Two Pointers** — The Rendezvous ✅ | 8 | The Mirror Walk | 3Sum *(sorting)* |
| **Sliding Window** — The Moving Frame | 7 | The Window Frame | Minimum Window Substring *(hashing)* |
| **Stack** — Spring-Loaded Piles & Monotonic Walls | 11 | The Spring Platform | Largest Rectangle in Histogram *(two-pointers)* |
| **Binary Search** — Halving the Search Space | 10 | The Crate Hunt | Median of Two Sorted Arrays *(two-pointers)* |

### Act II — Linked & Recursive
| Chapter | Lv | L1 primer | Boss (fuses) |
|---|----|---|---|
| **Linked Lists** — The Cable Yard | 12 | The Cable Yard | LRU Cache *(hashing)* |
| **Recursion & the Call Stack** | 10 | The Tower of Frames | Merge Sort *(two-pointers)* |
| **Trees & BSTs** — The Recursive Grove | 14 | The Grove | Construct from Pre+Inorder *(hashing)* |
| **Heaps & Priority Queues** — The Loosely-Sorted Pile | 8 | The Bubble Pit | Design Twitter *(hashing)* |

### Act III — Search & Optimize
| Chapter | Lv | L1 primer | Boss (fuses) |
|---|----|---|---|
| **Backtracking** — Choose, Explore, Un-choose | 11 | Choose, Explore, Un-choose | N-Queens *(hashing)* |
| **Graphs (BFS/DFS)** — Floods, Dives, Frontiers | 14 | Signal in the Network | Word Ladder *(hashing)* |
| **Tries** — The Letter Warehouse *(moved from Act II — fixes a forward dep)* | 8 | The Letter Warehouse | Word Search II *(backtracking)* |
| **Greedy** — Commit and Never Look Back | 8 | The Committed Robot | Hand of Straights *(heaps)* |
| **Intervals** — Sort, Sweep, and the Frontier | 8 | The Overlap Lamp | Meeting Rooms II *(heaps)* |
| **Dynamic Programming** — The Memo Tape *(whole-game finale)* | 10 | The Recompute Trap | LIS O(n log n) *(binary-search)* |

**Verified linear order (acyclic; every prereq & boss target precedes its chapter):**
arrays-hashing → two-pointers → sliding-window → stack → binary-search → linked-list →
recursion → trees → heaps → backtracking → graphs → tries → greedy → intervals → dynamic-programming.

## Difficulty curve — the two cliffs to bridge

The curve is a **rising sawtooth** (floor resets to 1 each chapter). Two spots jump too hard
and get an inserted `tutorial` bridge (watch-and-scrub before writing cold):

1. **DP L6 (Word Break)** — first open DP needing an inner scan over all earlier cells.
   → insert **"Word Break, Watched"** before it.
2. **Graphs L12 (Course Schedule)** — directed edges + cycle detection dropped into an open level.
   → insert **"Watch the Cycle"** (DFS 3-colour marking) before it.

Hard ideas are pre-seeded one chapter early on purpose: memoization in Recursion L9 → DP;
two-pointer merge in Recursion L10 → Merge Sort/Binary Search; grid-DFS in Backtracking L10 →
Tries' Word Search II; BFS/queue in Trees L8 → Graphs.

## Data model

See `curriculum/curriculum.json`. `Act → Chapter → Level`; a Level carries `kind`,
`difficulty`, `engineLevelId` (the tracer scene the app loads), `targetComplexity`
(drives the brown-out budget on `optimize`/`boss`), and `passRequires`
(`viewed` | `correct` | `correct+withinBudget`). **TODO:** `targetComplexity` is currently
`null` and must be filled per level for the optimize/boss brown-out gates.

## Build order

1. **Act 0 tours: Arrays & Indices → Pointers (+ Walking the Tape)** — makes the Two-Pointer
   demo we already shipped actually *comprehensible* to a beginner. Reuses existing widgets;
   almost no new art. **← the next buildable slice.**
2. **Arrays & Hashing (keystone chapter)** — ships the reusable hash "mailbox-wall" substrate
   that ~12 later chapters need. Build L1 (primer) → L2 (Contains Duplicate) → L4 (Two Sum).
3. Cheap Act-I leaves: Binary Search (lo/hi/mid on the tape), Sliding Window (window overlay + freq map).
4. Stack (spring platform, reused by Recursion & Graphs) → Linked List → Recursion (reuses the
   stack as the call-stack tower) → Trees → Heaps → Act III (Backtracking → Graphs → Tries →
   Greedy → Intervals → DP), inserting the two bridge tutorials.

Before any of that, the reusable **Guided-Tour engine** (caption bubble, beat sequencing on the
existing scrubber, meter-dimming, chrome suppression, jargon-gloss chips, handoff card) is built
once alongside the first Act-0 tour.
