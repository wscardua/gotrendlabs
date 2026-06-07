import 'package:flutter_test/flutter_test.dart';
import 'package:gotrendlabs_mobile/src/core/formatters.dart';

void main() {
  test('formats GTL and probability for mobile labels', () {
    expect(formatGtl(42), '42 GT₵');
    expect(formatProbability(77.7), '78%');
  });

  test('compacts long copy without changing short text', () {
    expect(compactText('Mercado aberto', max: 20), 'Mercado aberto');
    expect(compactText('a' * 30, max: 10), '${'a' * 9}…');
  });
}
