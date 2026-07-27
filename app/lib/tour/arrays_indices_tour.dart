// Act 0 · Foundations — the first Guided Tour, "Arrays & Indices".
// No problem to solve: meet the tape, learn what an index is, watch that reading
// any crate is one step (O(1)), then bridge to the Python nums[i].
import 'tour.dart';

// Values are deliberately UNSORTED so "index" (position) never gets confused with
// "value" (what's inside).
const _crates = [7, 2, 9, 4, 5];

final arraysIndicesTour = Tour(
  title: 'Arrays & Indices',
  subtitle: 'Act 0 · Foundations — no problem to solve, just poke and watch.',
  crates: _crates,
  handoffText:
      "Reading one crate is instant — one step, no matter how far away it is. "
      "Next tour: what happens when you have to visit them ALL? (that's where 'fast vs slow' begins).",
  beats: [
    Beat(
      caption:
          "This is an array — a fixed row of crates. Here there are five. The row's length is "
          "locked: nothing gets added or removed. Each crate holds a number.",
      glosses: [Gloss('array', 'a fixed row of boxes, in order')],
    ),
    Beat(
      caption:
          "Every crate has an index — its position, and we count from 0. So the first crate is "
          "index 0, and the last of five is index 4. (The small grey number under each crate.)",
      glosses: [Gloss('index', "a crate's position number, starting at 0")],
    ),
    Beat(
      caption:
          "Here's the secret the machine keeps: it only remembers ONE thing — where the FRONT of "
          "the row is (index 0). Everything is measured from there.",
      showFront: true,
    ),
    Beat(
      caption:
          "To read index 3, the machine jumps STRAIGHT there from the front — it does not walk "
          "past 0, 1, 2. One jump. The STEPS meter ticks once. A step = one piece of work; fewer "
          "steps = faster.",
      showFront: true,
      showRuler: true,
      readerIndex: 3,
      steps: 1,
      glosses: [Gloss('step', 'one piece of work the machine does')],
    ),
    Beat(
      caption:
          "Read index 0 instead? Still one jump, +1 step. The far end, index 4? Also one jump, "
          "+1 step. Distance never changes the cost — any crate is reachable in a single step. "
          "That 'always one step' is what we'll later call O(1).",
      showFront: true,
      showRuler: true,
      readerIndex: 0,
      steps: 2,
    ),
    Beat(
      caption:
          "In Python you write this as nums[3] — read it as 'the crate at index 3'. The square "
          "brackets mean 'look up the box at this index', and nums is the name of the whole row. "
          "The picture you just watched IS this line of code.",
      showFront: true,
      readerIndex: 3,
      steps: 3,
      code: 'x = nums[3]   # the crate at index 3',
      glosses: [Gloss('nums[i]', "the crate at index i of the row named nums")],
    ),
    Beat(
      caption:
          "Your turn. Tap any crate and watch the READER jump straight to it — STEPS ticks +1 "
          "each time, however far you jump. There's no goal here; just feel that every read costs "
          "exactly one.",
      showFront: true,
      freePlay: true,
    ),
    Beat(
      caption:
          "One trap to see clearly: nums[3] is the FOURTH crate (we count from 0), and it hands "
          "you the VALUE inside it — here that's 4 — not the number 3. And nums[5]? There's no "
          "index 5 in five crates; that's past the end (this is where a real IndexError comes from).",
      showFront: true,
      readerIndex: 3,
      steps: 3,
      glosses: [
        Gloss('value', "what's inside a crate (e.g. 4)"),
        Gloss('vs index', 'where the crate sits (e.g. 3)'),
      ],
    ),
    Beat(
      caption:
          "That's the whole idea: an array is a fixed row, each crate has an index from 0, and "
          "reading any one is a single step. You now know what every later tour stands on.",
      showFront: true,
      isHandoff: true,
    ),
  ],
);
