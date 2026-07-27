// DEREF — learn DSA by watching your code walk a data structure.
// Home menu -> Guided Tour (Act 0) or the problem player.
import 'package:flutter/material.dart';

import 'player_page.dart';
import 'theme.dart';
import 'tour/arrays_indices_tour.dart';
import 'tour/tour.dart';

void main() => runApp(const DerefApp());

class DerefApp extends StatelessWidget {
  const DerefApp({super.key});
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'DEREF',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(brightness: Brightness.dark, scaffoldBackgroundColor: bg, fontFamily: 'monospace'),
      home: const HomePage(),
    );
  }
}

class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 560),
            child: ListView(
              padding: const EdgeInsets.all(24),
              children: [
                const SizedBox(height: 12),
                const Text('DEREF',
                    style: TextStyle(color: teal, fontSize: 30, fontWeight: FontWeight.bold, letterSpacing: 6)),
                const SizedBox(height: 6),
                const Text('Learn DSA by watching your code walk the data.',
                    style: TextStyle(color: muted, fontSize: 13)),
                const SizedBox(height: 28),
                _tile(
                  context,
                  tag: 'ACT 0 · FOUNDATIONS',
                  title: 'Arrays & Indices',
                  subtitle: 'A no-fail guided tour. Start here — learn what an array and an index are from zero.',
                  color: teal,
                  onTap: () => Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => TourPage(tour: arraysIndicesTour)),
                  ),
                ),
                const SizedBox(height: 14),
                _tile(
                  context,
                  tag: 'ACT I · TWO POINTERS',
                  title: 'The Rendezvous',
                  subtitle: 'The problem player: watch a real two-pointer solution run, step by step.',
                  color: magenta,
                  onTap: () => Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => const PlayerPage()),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _tile(BuildContext context,
      {required String tag,
      required String title,
      required String subtitle,
      required Color color,
      required VoidCallback onTap}) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(
          color: panel,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: line),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(tag, style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 1.5)),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: Text(title,
                      style: const TextStyle(color: ink, fontSize: 20, fontWeight: FontWeight.bold)),
                ),
                Icon(Icons.arrow_forward, color: color, size: 20),
              ],
            ),
            const SizedBox(height: 6),
            Text(subtitle, style: const TextStyle(color: muted, fontSize: 12.5, height: 1.4)),
          ],
        ),
      ),
    );
  }
}
