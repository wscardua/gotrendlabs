import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gotrendlabs_mobile/src/core/api_client.dart';
import 'package:gotrendlabs_mobile/src/core/providers.dart';
import 'package:gotrendlabs_mobile/src/features/markets/markets_providers.dart';
import 'package:gotrendlabs_mobile/src/features/ranking/ranking_screen.dart';
import 'package:gotrendlabs_mobile/src/theme.dart';

void main() {
  testWidgets('RankingScreen uses handles and compact badge summary', (
    tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          apiClientProvider.overrideWithValue(
            ApiClient(tokenStore: MemoryTokenStore()),
          ),
          rankingPayloadProvider.overrideWith((ref, filters) async {
            return {
              'rows': [
                {
                  'position': 1,
                  'user_id': 10,
                  'handle': 'alpha',
                  'display_name': 'Alice Real',
                  'reputation_score': 42,
                  'accuracy_indicator': '70%',
                  'strong_category': 'Tecnologia',
                  'badges_total': 4,
                  'badges': [
                    {'code': 'founder', 'name': 'Fundador'},
                    {'code': 'streak', 'name': 'Sequência'},
                    {'code': 'top', 'name': 'Top 10'},
                  ],
                },
              ],
              'categories': [],
            };
          }),
        ],
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: const RankingScreen(),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('@alpha'), findsOneWidget);
    expect(find.text('Alice Real'), findsNothing);
    expect(find.text('+1'), findsOneWidget);
    expect(find.text('Tecnologia'), findsOneWidget);
  });
}
