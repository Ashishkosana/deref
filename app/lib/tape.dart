// The shared substrate: a tape of numbered crates, plus a pointer caret.
// Reused by the Guided Tour (sortedness off) and the problem player (on).
import 'package:flutter/material.dart';

import 'theme.dart';

class TapePainter extends CustomPainter {
  final List<int> values;
  final bool showGradient; // amber "small->big" tint (only meaningful when sorted)
  final int highlight; // index to ring, or -1

  TapePainter(this.values, {this.showGradient = false, this.highlight = -1});

  @override
  void paint(Canvas canvas, Size size) {
    final n = values.length;
    if (n == 0) return;
    final cw = size.width / n;
    for (int i = 0; i < n; i++) {
      final rect = RRect.fromRectAndRadius(
        Rect.fromLTWH(i * cw + 3, 0, cw - 6, size.height),
        const Radius.circular(8),
      );
      final t = (showGradient && n > 1) ? i / (n - 1) : 0.0;
      canvas.drawRRect(
        rect,
        Paint()..color = Color.lerp(crateColor, const Color(0xFF3A3320), t)!,
      );
      final ringed = i == highlight;
      canvas.drawRRect(
        rect,
        Paint()
          ..style = PaintingStyle.stroke
          ..strokeWidth = ringed ? 2.5 : 1
          ..color = ringed
              ? teal
              : Color.lerp(const Color(0xFF3A424E), amber, t * 0.7)!,
      );
      _text(canvas, '${values[i]}', i * cw + cw / 2, size.height / 2 - 9, 18, ink, FontWeight.bold);
      _text(canvas, '$i', i * cw + cw / 2, size.height - 16, 11, muted, FontWeight.normal);
    }
  }

  void _text(Canvas c, String s, double cx, double cy, double size, Color color, FontWeight w) {
    final tp = TextPainter(
      text: TextSpan(text: s, style: TextStyle(color: color, fontSize: size, fontWeight: w)),
      textDirection: TextDirection.ltr,
    )..layout();
    tp.paint(c, Offset(cx - tp.width / 2, cy));
  }

  @override
  bool shouldRepaint(covariant TapePainter old) =>
      old.values != values || old.highlight != highlight || old.showGradient != showGradient;
}

/// A pointer robot caret (arrow + label) that glides between crates.
Widget pointerCaret({
  required int index,
  required double crateWidth,
  required double top,
  required String label,
  required Color color,
}) {
  return AnimatedPositioned(
    duration: const Duration(milliseconds: 550),
    curve: Curves.easeInOutCubic,
    left: index * crateWidth,
    top: top + 2,
    width: crateWidth,
    child: Column(
      children: [
        Icon(Icons.arrow_drop_up, color: color, size: 26),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 1),
          decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(5)),
          child: Text(label,
              style: const TextStyle(color: bg, fontWeight: FontWeight.bold, fontSize: 10)),
        ),
      ],
    ),
  );
}
