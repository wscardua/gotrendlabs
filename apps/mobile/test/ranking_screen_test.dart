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

  testWidgets('RankingScreen refetches cached ranking when opened', (
    tester,
  ) async {
    var calls = 0;
    final container = ProviderContainer(
      overrides: [
        apiClientProvider.overrideWithValue(
          ApiClient(tokenStore: MemoryTokenStore()),
        ),
        rankingPayloadProvider.overrideWith((ref, filters) async {
          calls += 1;
          return _payload(
            handle: calls == 1 ? 'stale' : 'fresh',
            strongCategory: calls == 1 ? 'Antigo' : 'Atualizado',
          );
        }),
      ],
    );
    addTearDown(container.dispose);

    await container.read(rankingPayloadProvider(const RankingFilters()).future);
    expect(calls, 1);

    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: const RankingScreen(),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(calls, 2);
    expect(find.text('@fresh'), findsOneWidget);
    expect(find.text('Atualizado'), findsOneWidget);
    expect(find.text('@stale'), findsNothing);
  });

  testWidgets('RankingScreen pull refresh waits for fresh ranking data', (
    tester,
  ) async {
    var calls = 0;
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          apiClientProvider.overrideWithValue(
            ApiClient(tokenStore: MemoryTokenStore()),
          ),
          rankingPayloadProvider.overrideWith((ref, filters) async {
            calls += 1;
            return _payload(
              handle: calls == 1 ? 'before-refresh' : 'after-refresh',
              strongCategory: calls == 1 ? 'Antes' : 'Depois',
            );
          }),
        ],
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: const RankingScreen(),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('@before-refresh'), findsOneWidget);

    await tester.drag(find.byType(ListView), const Offset(0, 360));
    await tester.pump();
    await tester.pumpAndSettle();

    expect(calls, 2);
    expect(find.text('@after-refresh'), findsOneWidget);
    expect(find.text('@before-refresh'), findsNothing);
  });

  testWidgets('RankingScreen empty state can be pulled to refresh', (
    tester,
  ) async {
    var calls = 0;
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          apiClientProvider.overrideWithValue(
            ApiClient(tokenStore: MemoryTokenStore()),
          ),
          rankingPayloadProvider.overrideWith((ref, filters) async {
            calls += 1;
            if (calls == 1) {
              return _payload(rows: const []);
            }
            return _payload(handle: 'fresh-empty-state');
          }),
        ],
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: const RankingScreen(),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Sem previsões resolvidas'), findsOneWidget);

    await tester.drag(find.byType(ListView), const Offset(0, 360));
    await tester.pump();
    await tester.pumpAndSettle();

    expect(calls, 2);
    expect(find.text('@fresh-empty-state'), findsOneWidget);
  });

  testWidgets('RankingScreen refetches ranking when filters change', (
    tester,
  ) async {
    final seenFilters = <RankingFilters>[];
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          apiClientProvider.overrideWithValue(
            ApiClient(tokenStore: MemoryTokenStore()),
          ),
          rankingPayloadProvider.overrideWith((ref, filters) async {
            seenFilters.add(filters);
            return _payload(rows: const [], categories: _categories());
          }),
        ],
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: const RankingScreen(),
        ),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byType(DropdownButtonFormField<String>).at(0));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Tecnologia').last);
    await tester.pumpAndSettle();

    await tester.tap(find.byType(DropdownButtonFormField<String>).at(1));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Apps').last);
    await tester.pumpAndSettle();

    await tester.tap(find.byType(DropdownButtonFormField<String>).at(2));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Geral').last);
    await tester.pumpAndSettle();

    expect(seenFilters, contains(const RankingFilters(category: 'tech')));
    expect(
      seenFilters,
      contains(const RankingFilters(category: 'tech', subcategory: 'apps')),
    );
    expect(
      seenFilters,
      contains(
        const RankingFilters(
          category: 'tech',
          subcategory: 'apps',
          event: 'geral',
        ),
      ),
    );
  });
}

Map<String, dynamic> _payload({
  String handle = 'alpha',
  String strongCategory = 'Tecnologia',
  List<Map<String, dynamic>>? rows,
  List<Map<String, dynamic>>? categories,
}) {
  return {
    'rows':
        rows ??
        [
          {
            'position': 1,
            'user_id': 10,
            'handle': handle,
            'display_name': 'Alice Real',
            'reputation_score': 42,
            'accuracy_indicator': '70%',
            'strong_category': strongCategory,
            'badges_total': 0,
            'badges': <Map<String, dynamic>>[],
          },
        ],
    'categories': categories ?? <Map<String, dynamic>>[],
  };
}

List<Map<String, dynamic>> _categories() {
  return [
    {
      'name': 'Tecnologia',
      'slug': 'tech',
      'subcategories': [
        {
          'name': 'Apps',
          'slug': 'apps',
          'events': [
            {'name': 'Geral', 'slug': 'geral'},
          ],
        },
      ],
    },
  ];
}
