// The Guided-Tour engine: a reusable, NO-FAIL, poke-and-watch player.
// A Tour is a list of Beats over a shared tape substrate. No verdict, no timer,
// no brown-out — the learner taps Next / scrubs, and the substrate reacts.
import 'package:flutter/material.dart';

import '../tape.dart';
import '../theme.dart';

class Gloss {
  final String term;
  final String def;
  const Gloss(this.term, this.def);
}

class Beat {
  final String caption;
  final int? readerIndex; // where the READER sits (null = not present)
  final bool showFront; // the FRONT tick at index 0
  final bool showRuler; // dashed ruler front -> reader
  final int steps; // STEPS meter value
  final String? code; // one code line to mirror the picture
  final List<Gloss> glosses;
  final bool freePlay; // interactive sandbox beat
  final bool isHandoff; // final "what's next" card

  const Beat({
    required this.caption,
    this.readerIndex,
    this.showFront = false,
    this.showRuler = false,
    this.steps = 0,
    this.code,
    this.glosses = const [],
    this.freePlay = false,
    this.isHandoff = false,
  });
}

class Tour {
  final String title;
  final String subtitle;
  final List<int> crates;
  final List<Beat> beats;
  final String handoffText;

  const Tour({
    required this.title,
    required this.subtitle,
    required this.crates,
    required this.beats,
    required this.handoffText,
  });
}

class TourPage extends StatefulWidget {
  final Tour tour;
  const TourPage({super.key, required this.tour});
  @override
  State<TourPage> createState() => _TourPageState();
}

class _TourPageState extends State<TourPage> {
  int _b = 0;
  // free-play state
  int? _freeReader;
  int _freeSteps = 0;
  bool _freeBump = false;

  Tour get t => widget.tour;
  Beat get beat => t.beats[_b];
  int get n => t.crates.length;

  void _go(int to) {
    setState(() {
      _b = to.clamp(0, t.beats.length - 1);
      if (beat.freePlay) {
        _freeReader = null;
        _freeSteps = 0;
        _freeBump = false;
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final b = beat;
    final readerIndex = b.freePlay ? _freeReader : b.readerIndex;
    final steps = b.freePlay ? _freeSteps : b.steps;

    return Scaffold(
      appBar: AppBar(
        backgroundColor: bg,
        elevation: 0,
        title: Text(t.title, style: const TextStyle(color: ink, fontSize: 16)),
        iconTheme: const IconThemeData(color: muted),
      ),
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 720),
            child: ListView(
              padding: const EdgeInsets.all(20),
              children: [
                Text(t.subtitle, style: const TextStyle(color: muted, fontSize: 12.5)),
                const SizedBox(height: 12),
                _caption(b.caption),
                const SizedBox(height: 14),
                _tapeCard(b, readerIndex),
                const SizedBox(height: 12),
                _stepsMeter(steps, readerIndex),
                if (b.glosses.isNotEmpty) ...[
                  const SizedBox(height: 12),
                  _glosses(b.glosses),
                ],
                if (b.code != null) ...[
                  const SizedBox(height: 12),
                  _code(b.code!),
                ],
                if (b.freePlay) ...[
                  const SizedBox(height: 12),
                  _freePlayHint(),
                ],
                const SizedBox(height: 16),
                _controls(),
                if (b.isHandoff) ...[
                  const SizedBox(height: 16),
                  _handoff(),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _caption(String text) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: panel,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: line),
      ),
      child: Text(text, style: const TextStyle(color: ink, fontSize: 14.5, height: 1.5)),
    );
  }

  Widget _tapeCard(Beat b, int? readerIndex) {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 22, 16, 10),
      decoration: BoxDecoration(
        color: panel,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: line),
      ),
      child: LayoutBuilder(builder: (context, c) {
        final w = c.maxWidth;
        final cw = w / n;
        const crateH = 66.0;
        const caretH = 34.0;
        final onTape = readerIndex != null && readerIndex >= 0 && readerIndex < n;
        return SizedBox(
          height: crateH + caretH + 8,
          child: Stack(
            clipBehavior: Clip.none,
            children: [
              CustomPaint(size: Size(w, crateH), painter: TapePainter(t.crates)),
              // FRONT tick at index 0
              if (b.showFront)
                Positioned(
                  left: 3,
                  top: -14,
                  child: Text('▏FRONT',
                      style: TextStyle(color: teal.withValues(alpha: 0.8), fontSize: 10, fontWeight: FontWeight.bold)),
                ),
              // dashed-ish ruler from front to reader
              if (b.showRuler && onTape)
                Positioned(
                  left: cw / 2,
                  top: 8,
                  child: Container(
                    height: 2,
                    width: (readerIndex * cw).clamp(1.0, w),
                    color: teal.withValues(alpha: 0.5),
                  ),
                ),
              // READER caret
              if (onTape)
                pointerCaret(index: readerIndex, crateWidth: cw, top: crateH, label: 'READER', color: teal),
              // free-play tap targets
              if (b.freePlay)
                Positioned.fill(
                  bottom: caretH,
                  child: Row(
                    children: List.generate(
                      n,
                      (i) => Expanded(
                        child: GestureDetector(
                          behavior: HitTestBehavior.translucent,
                          onTap: () => setState(() {
                            _freeReader = i;
                            _freeSteps++;
                            _freeBump = false;
                          }),
                        ),
                      ),
                    ),
                  ),
                ),
              // past-the-end banner
              if (_freeBump && b.freePlay)
                Positioned(
                  right: 0,
                  top: -14,
                  child: Text('index $n → past the end',
                      style: const TextStyle(color: magenta, fontSize: 10, fontWeight: FontWeight.bold)),
                ),
            ],
          ),
        );
      }),
    );
  }

  Widget _stepsMeter(int steps, int? readerIndex) {
    final reading = (readerIndex != null && readerIndex >= 0 && readerIndex < n)
        ? 'nums[$readerIndex] = ${t.crates[readerIndex]}'
        : '—';
    return Row(
      children: [
        _stat('STEPS (work done)', '$steps'),
        const SizedBox(width: 16),
        _stat('READING', reading),
      ],
    );
  }

  Widget _freePlayHint() {
    return Row(
      children: [
        const Expanded(
          child: Text('Tap any crate — STEPS ticks +1 every time, however far. Nothing to solve.',
              style: TextStyle(color: muted, fontSize: 12.5, height: 1.4)),
        ),
        const SizedBox(width: 10),
        OutlinedButton(
          onPressed: () => setState(() {
            _freeBump = true;
            _freeSteps++;
            _freeReader = null;
          }),
          style: OutlinedButton.styleFrom(
            foregroundColor: magenta,
            side: const BorderSide(color: magenta),
            padding: const EdgeInsets.symmetric(horizontal: 10),
          ),
          child: const Text('try index past the end', style: TextStyle(fontSize: 11)),
        ),
      ],
    );
  }

  Widget _glosses(List<Gloss> glosses) {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: glosses
          .map((g) => Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                decoration: BoxDecoration(
                  color: amber.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: amber.withValues(alpha: 0.4)),
                ),
                child: RichText(
                  text: TextSpan(children: [
                    TextSpan(
                        text: '${g.term}  ',
                        style: const TextStyle(color: amber, fontWeight: FontWeight.bold, fontSize: 12)),
                    TextSpan(text: g.def, style: const TextStyle(color: ink, fontSize: 12)),
                  ]),
                ),
              ))
          .toList(),
    );
  }

  Widget _code(String codeLine) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: panel,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: line),
      ),
      child: Text(codeLine,
          style: const TextStyle(color: teal, fontFamily: 'monospace', fontSize: 13.5)),
    );
  }

  Widget _controls() {
    return Row(
      children: [
        TextButton.icon(
          onPressed: _b > 0 ? () => _go(_b - 1) : null,
          icon: const Icon(Icons.chevron_left, size: 20),
          label: const Text('Back'),
          style: TextButton.styleFrom(foregroundColor: muted),
        ),
        Expanded(
          child: Slider(
            value: _b.toDouble(),
            min: 0,
            max: (t.beats.length - 1).toDouble(),
            divisions: t.beats.length - 1,
            activeColor: teal,
            inactiveColor: crateColor,
            onChanged: (v) => _go(v.round()),
          ),
        ),
        if (_b < t.beats.length - 1)
          FilledButton(
            onPressed: () => _go(_b + 1),
            style: FilledButton.styleFrom(backgroundColor: teal, foregroundColor: bg),
            child: const Text('Next'),
          )
        else
          Text('${_b + 1}/${t.beats.length}', style: const TextStyle(color: muted, fontSize: 12)),
      ],
    );
  }

  Widget _handoff() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: teal.withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: teal.withValues(alpha: 0.5)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(t.handoffText, style: const TextStyle(color: ink, fontSize: 14, height: 1.5)),
          const SizedBox(height: 12),
          Row(
            children: [
              FilledButton.icon(
                onPressed: () => _go(0),
                icon: const Icon(Icons.replay, size: 18),
                label: const Text('Replay'),
                style: FilledButton.styleFrom(backgroundColor: teal, foregroundColor: bg),
              ),
              const SizedBox(width: 10),
              OutlinedButton(
                onPressed: () => Navigator.of(context).maybePop(),
                style: OutlinedButton.styleFrom(foregroundColor: muted, side: const BorderSide(color: muted)),
                child: const Text('Back to menu'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _stat(String label, String value) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(color: muted, fontSize: 10, letterSpacing: 1)),
        const SizedBox(height: 2),
        Text(value, style: const TextStyle(color: ink, fontSize: 17, fontWeight: FontWeight.bold)),
      ],
    );
  }
}
