import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gotrendlabs_mobile/src/features/markets/resolution_criteria_card.dart';
import 'package:gotrendlabs_mobile/src/theme.dart';

void main() {
  for (final scale in [1.0, 2.0]) {
    testWidgets(
      'long criteria preview opens complete scrollable text at scale $scale',
      (tester) async {
        final criteria = List.generate(
          40,
          (i) => 'Condição $i: verificar a fonte oficial antes da resolução.',
        ).join('\n');
        await tester.pumpWidget(
          MaterialApp(
            theme: buildGoTrendLabsTheme(),
            home: MediaQuery(
              data: MediaQueryData(textScaler: TextScaler.linear(scale)),
              child: Scaffold(
                body: Padding(
                  padding: const EdgeInsets.all(20),
                  child: ResolutionCriteriaText(criteria: criteria),
                ),
              ),
            ),
          ),
        );
        final preview = tester.widget<Text>(find.text(criteria));
        expect(preview.maxLines, 3);
        expect(preview.overflow, TextOverflow.ellipsis);
        expect(tester.getSize(find.text(criteria)).height, lessThan(170));
        await tester.tap(find.text('Ver critério de resolução completo'));
        await tester.pumpAndSettle();
        expect(
          tester.widget<SelectableText>(find.byType(SelectableText)).data,
          criteria,
        );
        await tester.drag(
          find.byType(SingleChildScrollView),
          const Offset(0, -350),
        );
        await tester.pumpAndSettle();
        expect(tester.takeException(), isNull);
        await tester.tap(find.byTooltip('Fechar'));
        await tester.pumpAndSettle();
        expect(find.byType(SelectableText), findsNothing);
      },
    );
  }
  for (final criteria in ['Fonte oficial.', '']) {
    testWidgets(
      'short or empty criteria stays complete without extra action: $criteria',
      (tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(body: ResolutionCriteriaText(criteria: criteria)),
          ),
        );
        expect(
          find.text(criteria.isEmpty ? 'Critério não informado.' : criteria),
          findsOneWidget,
        );
        expect(find.text('Ver critério de resolução completo'), findsNothing);
      },
    );
  }
}
