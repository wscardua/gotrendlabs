import 'package:flutter_test/flutter_test.dart';
import 'package:gotrendlabs_mobile/src/core/birth_date_input.dart';

void main() {
  test('formats birth date as DD/MM/AAAA while typing', () {
    const formatter = BirthDateInputFormatter();

    final result = formatter.formatEditUpdate(
      TextEditingValue.empty,
      const TextEditingValue(text: '18061990'),
    );

    expect(result.text, '18/06/1990');
    expect(result.selection.baseOffset, result.text.length);
  });

  test('normalizes Brazilian birth date for the API', () {
    expect(normalizeBirthDateForApi('18/06/1990'), '1990-06-18');
  });

  test('rejects impossible or American-formatted birth dates', () {
    expect(normalizeBirthDateForApi('31/02/1990'), isNull);
    expect(normalizeBirthDateForApi('1990-06-18'), isNull);
  });
}
