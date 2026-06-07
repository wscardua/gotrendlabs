import 'package:flutter/material.dart';

import '../../theme.dart';

class SparklinePath extends StatelessWidget {
  const SparklinePath({super.key, required this.path, this.height = 42});

  final String path;
  final double height;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: height,
      width: double.infinity,
      child: CustomPaint(painter: _SparklinePainter(path)),
    );
  }
}

class _SparklinePainter extends CustomPainter {
  _SparklinePainter(this.rawPath);

  final String rawPath;

  @override
  void paint(Canvas canvas, Size size) {
    final points = _parsePoints(rawPath);
    if (points.length < 2) {
      final paint = Paint()
        ..color = GtlColors.border
        ..strokeWidth = 1.4
        ..style = PaintingStyle.stroke;
      canvas.drawLine(
        Offset(0, size.height / 2),
        Offset(size.width, size.height / 2),
        paint,
      );
      return;
    }
    final minX = points.map((p) => p.dx).reduce((a, b) => a < b ? a : b);
    final maxX = points.map((p) => p.dx).reduce((a, b) => a > b ? a : b);
    final minY = points.map((p) => p.dy).reduce((a, b) => a < b ? a : b);
    final maxY = points.map((p) => p.dy).reduce((a, b) => a > b ? a : b);
    Offset scale(Offset point) {
      final x = maxX == minX
          ? 0.0
          : (point.dx - minX) / (maxX - minX) * size.width;
      final y = maxY == minY
          ? size.height / 2
          : (point.dy - minY) / (maxY - minY) * size.height;
      return Offset(x, y);
    }

    final path = Path()..moveTo(scale(points.first).dx, scale(points.first).dy);
    for (final point in points.skip(1)) {
      final scaled = scale(point);
      path.lineTo(scaled.dx, scaled.dy);
    }
    final glow = Paint()
      ..color = GtlColors.accentBlue.withValues(alpha: 0.2)
      ..strokeWidth = 6
      ..strokeCap = StrokeCap.round
      ..style = PaintingStyle.stroke;
    final line = Paint()
      ..color = GtlColors.accentBlue
      ..strokeWidth = 2
      ..strokeCap = StrokeCap.round
      ..style = PaintingStyle.stroke;
    canvas.drawPath(path, glow);
    canvas.drawPath(path, line);
  }

  List<Offset> _parsePoints(String value) {
    final matches = RegExp(
      r'[ML]\s*(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)',
    ).allMatches(value);
    return [
      for (final match in matches)
        Offset(double.parse(match.group(1)!), double.parse(match.group(2)!)),
    ];
  }

  @override
  bool shouldRepaint(covariant _SparklinePainter oldDelegate) =>
      oldDelegate.rawPath != rawPath;
}
