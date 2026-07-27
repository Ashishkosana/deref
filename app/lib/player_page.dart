// The problem player: plays a graded run's frame JSON (the two-pointer demo).
import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show rootBundle;

import 'tape.dart';
import 'theme.dart';

class Frame {
  final int tick;
  final int line;
  final int? l, r, s;
  final int spaceHi;
  Frame(this.tick, this.line, this.l, this.r, this.s, this.spaceHi);
  factory Frame.fromJson(Map<String, dynamic> j) {
    final v = (j['vars'] as Map).cast<String, dynamic>();
    return Frame(j['tick'], j['line'], v['L'], v['R'], v['s'], j['space_hi']);
  }
}

class Demo {
  final String title, prompt, targetClass, source, solution;
  final List<int> nums;
  final int target;
  final bool solved;
  final String fittedClass;
  final List<Frame> frames;
  Demo(this.title, this.prompt, this.targetClass, this.source, this.solution, this.nums,
      this.target, this.solved, this.fittedClass, this.frames);
  factory Demo.fromJson(Map<String, dynamic> j) {
    final input = (j['input'] as Map).cast<String, dynamic>();
    final verdict = (j['verdict'] as Map).cast<String, dynamic>();
    return Demo(
      j['title'], j['prompt'], j['targetClass'], j['source'], j['solution'],
      (input['nums'] as List).map((e) => e as int).toList(),
      input['target'], verdict['solved'], verdict['fittedClass'],
      (j['frames'] as List).map((e) => Frame.fromJson((e as Map).cast<String, dynamic>())).toList(),
    );
  }
}

class PlayerPage extends StatefulWidget {
  const PlayerPage({super.key});
  @override
  State<PlayerPage> createState() => _PlayerPageState();
}

class _PlayerPageState extends State<PlayerPage> {
  Demo? _demo;
  int _i = 0;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final raw = await rootBundle.loadString('assets/rendezvous.json');
    setState(() => _demo = Demo.fromJson(jsonDecode(raw)));
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  void _togglePlay() {
    final d = _demo!;
    if (_timer != null) {
      _timer!.cancel();
      setState(() => _timer = null);
      return;
    }
    if (_i >= d.frames.length - 1) _i = 0;
    setState(() {
      _timer = Timer.periodic(const Duration(milliseconds: 900), (t) {
        if (_i >= d.frames.length - 1) {
          t.cancel();
          setState(() => _timer = null);
        } else {
          setState(() => _i++);
        }
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    final d = _demo;
    if (d == null) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    final f = d.frames[_i];
    return Scaffold(
      appBar: AppBar(
        backgroundColor: bg,
        elevation: 0,
        title: const Text('The Rendezvous', style: TextStyle(color: ink, fontSize: 16)),
        iconTheme: const IconThemeData(color: muted),
      ),
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 720),
            child: ListView(
              padding: const EdgeInsets.all(20),
              children: [
                _header(d),
                const SizedBox(height: 18),
                _tapeCard(d, f),
                const SizedBox(height: 14),
                _meters(d, f),
                const SizedBox(height: 6),
                _controls(d),
                const SizedBox(height: 16),
                _codeCard(d, f),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _header(Demo d) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(children: [
          _chip('TARGET ${d.target}', amber),
          const SizedBox(width: 8),
          _chip(d.solved ? 'SOLVED · ${d.fittedClass}' : d.fittedClass, d.solved ? green : magenta),
        ]),
        const SizedBox(height: 10),
        Text(d.title,
            style: const TextStyle(color: ink, fontSize: 22, fontWeight: FontWeight.bold, letterSpacing: 1)),
        const SizedBox(height: 6),
        Text(d.prompt, style: const TextStyle(color: muted, fontSize: 12.5, height: 1.4)),
      ],
    );
  }

  Widget _tapeCard(Demo d, Frame f) {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 18, 16, 10),
      decoration: BoxDecoration(color: panel, borderRadius: BorderRadius.circular(14), border: Border.all(color: line)),
      child: LayoutBuilder(builder: (context, c) {
        final w = c.maxWidth;
        final cw = w / d.nums.length;
        const crateH = 64.0;
        const caretH = 34.0;
        return SizedBox(
          height: crateH + caretH + 6,
          child: Stack(
            children: [
              CustomPaint(size: Size(w, crateH), painter: TapePainter(d.nums, showGradient: true)),
              if (f.l != null) pointerCaret(index: f.l!, crateWidth: cw, top: crateH, label: 'L', color: teal),
              if (f.r != null) pointerCaret(index: f.r!, crateWidth: cw, top: crateH, label: 'R', color: magenta),
            ],
          ),
        );
      }),
    );
  }

  Widget _meters(Demo d, Frame f) {
    final maxTick = d.frames.last.tick == 0 ? 1 : d.frames.last.tick;
    return Row(
      children: [
        _stat('STEPS (ops)', '${f.tick}'),
        const SizedBox(width: 10),
        _stat('SUM', f.s == null ? '—' : '${f.s}'),
        const SizedBox(width: 10),
        _stat('AUX SPACE', '${f.spaceHi}'),
        const Spacer(),
        SizedBox(
          width: 120,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              const Text('POWER', style: TextStyle(color: muted, fontSize: 10, letterSpacing: 1)),
              const SizedBox(height: 4),
              ClipRRect(
                borderRadius: BorderRadius.circular(4),
                child: LinearProgressIndicator(
                  value: f.tick / (maxTick * 1.2),
                  minHeight: 8,
                  backgroundColor: crateColor,
                  valueColor: const AlwaysStoppedAnimation(teal),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _controls(Demo d) {
    return Row(
      children: [
        IconButton(
          onPressed: _togglePlay,
          icon: Icon(_timer != null ? Icons.pause_circle : Icons.play_circle, size: 34, color: teal),
        ),
        Expanded(
          child: Slider(
            value: _i.toDouble(),
            min: 0,
            max: (d.frames.length - 1).toDouble(),
            divisions: d.frames.length - 1,
            activeColor: teal,
            inactiveColor: crateColor,
            onChanged: (v) {
              _timer?.cancel();
              setState(() {
                _timer = null;
                _i = v.round();
              });
            },
          ),
        ),
        Text('${_i + 1}/${d.frames.length}', style: const TextStyle(color: muted, fontSize: 12)),
      ],
    );
  }

  Widget _codeCard(Demo d, Frame f) {
    final lines = d.source.split('\n');
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
      decoration: BoxDecoration(color: panel, borderRadius: BorderRadius.circular(14), border: Border.all(color: line)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          for (int ln = 0; ln < lines.length; ln++)
            Container(
              width: double.infinity,
              color: (ln == f.line - 1) ? teal.withValues(alpha: 0.16) : Colors.transparent,
              padding: const EdgeInsets.symmetric(vertical: 1, horizontal: 8),
              child: Row(children: [
                SizedBox(width: 26, child: Text('${ln + 1}', style: const TextStyle(color: muted, fontSize: 12))),
                Expanded(
                  child: Text(lines[ln].isEmpty ? ' ' : lines[ln],
                      style: TextStyle(color: (ln == f.line - 1) ? teal : ink, fontSize: 12.5, height: 1.35)),
                ),
              ]),
            ),
        ],
      ),
    );
  }

  Widget _chip(String text, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.16),
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: color.withValues(alpha: 0.5)),
      ),
      child: Text(text, style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 11)),
    );
  }

  Widget _stat(String label, String value) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(color: muted, fontSize: 10, letterSpacing: 1)),
        const SizedBox(height: 2),
        Text(value, style: const TextStyle(color: ink, fontSize: 18, fontWeight: FontWeight.bold)),
      ],
    );
  }
}
