import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gotrendlabs_mobile/src/features/auth/auth_controller.dart';
import 'package:gotrendlabs_mobile/src/features/auth/auth_models.dart';
import 'package:gotrendlabs_mobile/src/features/markets/market_models.dart';
import 'package:gotrendlabs_mobile/src/features/markets/market_presentation.dart';
import 'package:gotrendlabs_mobile/src/features/markets/markets_providers.dart';
import 'package:gotrendlabs_mobile/src/features/markets/markets_screen.dart';
import 'package:gotrendlabs_mobile/src/theme.dart';

void main() {
  test('Novo uses API creation and the exact 48 hour boundary', () {
    final now = DateTime.utc(2026, 11, 7, 12);
    for (final entry in [
      ('open', '2026-11-05T12:00:00.001Z', true),
      ('open', '2026-11-05T12:00:00Z', false),
      ('open', '2026-11-05T11:59:59Z', false),
      ('open', '2026-11-07T12:00:00Z', true),
      ('open', '2026-11-07T12:00:00.001Z', false),
      ('locked', '2026-11-07T10:00:00Z', false),
      ('resolved', '2026-11-07T10:00:00Z', false),
      ('sealed', '2026-11-07T10:00:00Z', false),
    ]) {
      expect(
        _market(
          slug: 'badge',
          title: 'Selo',
          status: entry.$1,
          createdAt: entry.$2,
        ).isNewAt(now),
        entry.$3,
      );
    }
  });

  testWidgets('ongoing keeps API open order and expands pending on return', (
    tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authControllerProvider.overrideWith(_AuthenticatedAuthController.new),
          marketClockProvider.overrideWithValue(
            () => DateTime.utc(2026, 11, 7, 12),
          ),
          marketsProvider.overrideWith(
            (ref) async => [
              _market(
                slug: 'locked-old',
                title: 'Apuração antiga',
                status: 'locked',
                closeAt: '2026-11-01T12:00:00Z',
              ),
              _market(slug: 'open-first', title: 'Aberto primeiro na API'),
              _market(
                slug: 'locked-new',
                title: 'Apuração recente',
                status: 'locked',
                closeAt: '2026-11-06T12:00:00Z',
              ),
              _market(
                slug: 'open-new',
                title: 'Aberto novo na API',
                createdAt: '2026-11-07T10:00:00Z',
              ),
            ],
          ),
        ],
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: const Scaffold(body: MarketsScreen()),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('NOVO'), findsOneWidget);
    expect(
      tester.getTopLeft(find.text('Aberto primeiro na API')).dy,
      lessThan(tester.getTopLeft(find.text('Aberto novo na API')).dy),
    );
    final toggle = find.byKey(const ValueKey('pending-markets-toggle'));
    await tester.ensureVisible(toggle);
    await tester.scrollUntilVisible(
      find.text('Apuração antiga'),
      100,
      scrollable: find.byType(Scrollable).last,
    );
    expect(
      tester.getTopLeft(find.text('Apuração recente')).dy,
      lessThan(tester.getTopLeft(find.text('Apuração antiga')).dy),
    );
    await tester.ensureVisible(toggle);
    await tester.tap(toggle);
    await tester.pumpAndSettle();
    expect(find.text('Apuração recente'), findsNothing);
    await tester.tap(find.text('Resolvidos'));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.text('Em andamento'));
    await tester.tap(find.text('Em andamento'));
    await tester.pumpAndSettle();
    await tester.ensureVisible(toggle);
    expect(find.text('Apuração recente'), findsOneWidget);
  });

  testWidgets(
    'no opens keeps pending accessible and no active links to results',
    (tester) async {
      final items = [
        _market(slug: 'locked-only', status: 'locked', title: 'Só apuração'),
      ];
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            authControllerProvider.overrideWith(
              _UnauthenticatedAuthController.new,
            ),
            marketsProvider.overrideWith((ref) async => items),
          ],
          child: MaterialApp(
            theme: buildGoTrendLabsTheme(),
            home: const Scaffold(body: MarketsScreen()),
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.text('Nenhum mercado aberto no momento.'), findsOneWidget);
      expect(find.text('Em apuração — 1 mercado'), findsOneWidget);
      expect(find.text('Só apuração'), findsOneWidget);
      await tester.tap(find.byKey(const ValueKey('pending-markets-toggle')));
      await tester.pumpAndSettle();
      expect(find.text('Só apuração'), findsNothing);
    },
  );

  testWidgets(
    'narrow layout and enlarged text retain controls without overflow',
    (tester) async {
      tester.view.physicalSize = const Size(390, 844);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            authControllerProvider.overrideWith(
              _AuthenticatedAuthController.new,
            ),
            marketClockProvider.overrideWithValue(
              () => DateTime.utc(2026, 11, 7, 12),
            ),
            marketsProvider.overrideWith(
              (ref) async => [
                _market(
                  slug: 'long-open',
                  title:
                      'Uma pergunta longa para conferir leitura com fonte ampliada no app',
                  createdAt: '2026-11-07T10:00:00Z',
                ),
                _market(
                  slug: 'pending-long',
                  title: 'Acompanhamento em apuração',
                  status: 'locked',
                ),
              ],
            ),
          ],
          child: MaterialApp(
            theme: buildGoTrendLabsTheme(),
            builder: (context, child) => MediaQuery(
              data: MediaQuery.of(
                context,
              ).copyWith(textScaler: TextScaler.linear(1.4)),
              child: child!,
            ),
            home: const Scaffold(body: MarketsScreen()),
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      expect(find.text('NOVO'), findsOneWidget);
      final toggle = find.byKey(const ValueKey('pending-markets-toggle'));
      await tester.ensureVisible(toggle);
      expect(find.text('Acompanhamento em apuração'), findsOneWidget);
      await tester.tap(toggle);
      await tester.pumpAndSettle();
      expect(find.text('Acompanhamento em apuração'), findsNothing);
      expect(tester.takeException(), isNull);
      await tester.ensureVisible(find.text('Minhas previsões'));
      await tester.tap(find.text('Minhas previsões'));
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'no active markets offers resolved history without an empty expander',
    (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            authControllerProvider.overrideWith(
              _UnauthenticatedAuthController.new,
            ),
            marketsProvider.overrideWith(
              (ref) async => [
                _market(
                  slug: 'sealed',
                  title: 'Resultado verificável',
                  status: 'sealed',
                  statusLabel: 'Selado',
                ),
              ],
            ),
          ],
          child: MaterialApp(
            theme: buildGoTrendLabsTheme(),
            home: const Scaffold(body: MarketsScreen()),
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(
        find.byKey(const ValueKey('pending-markets-toggle')),
        findsNothing,
      );
      expect(find.text('Favoritos'), findsNothing);
      await tester.tap(find.text('Ver resolvidos'));
      await tester.pumpAndSettle();
      expect(find.text('Resultado verificável'), findsOneWidget);
    },
  );

  testWidgets(
    'TodayScreen keeps open engagement order before pending markets',
    (tester) async {
      await tester.binding.setSurfaceSize(const Size(450, 2000));
      addTearDown(() => tester.binding.setSurfaceSize(null));
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            authControllerProvider.overrideWith(
              _UnauthenticatedAuthController.new,
            ),
            marketsProvider.overrideWith((ref) async {
              return [
                _market(
                  slug: 'fechado',
                  title: 'Mercado em apuração',
                  status: 'locked',
                  statusLabel: 'Fechado',
                ),
                _market(
                  slug: 'popular',
                  title: 'Mercado aberto popular',
                  participants: 20,
                  volume: 900,
                ),
                _market(slug: 'aberto', title: 'Mercado aberto comum'),
                _market(
                  slug: 'terceiro',
                  title: 'Terceiro aberto',
                  participants: 1,
                  volume: 1,
                ),
                _market(
                  slug: 'quarto',
                  title: 'Último aberto',
                  participants: 0,
                  volume: 0,
                ),
              ];
            }),
          ],
          child: MaterialApp(
            theme: buildGoTrendLabsTheme(),
            home: const Scaffold(body: TodayScreen()),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('Mercado aberto popular'), findsOneWidget);
      expect(find.text('Mercado aberto comum'), findsOneWidget);
      expect(
        tester.getTopLeft(find.text('Mercado aberto popular')).dy,
        lessThan(tester.getTopLeft(find.text('Mercado aberto comum')).dy),
      );
      await tester.scrollUntilVisible(
        find.text('Mercado em apuração'),
        200,
        scrollable: find.byType(Scrollable).last,
      );
      expect(find.text('Mercado em apuração'), findsOneWidget);
      expect(find.text('Em apuração'), findsWidgets);
      final sectionTitles = ['Para prever', 'Tendências', 'Mais mercados'];
      for (var i = 1; i < sectionTitles.length; i++) {
        expect(
          tester.getTopLeft(find.text(sectionTitles[i - 1])).dy,
          lessThan(tester.getTopLeft(find.text(sectionTitles[i])).dy),
        );
      }
      expect(
        tester.getTopLeft(find.text('Último aberto')).dy,
        lessThan(tester.getTopLeft(find.text('Mercado em apuração')).dy),
      );
    },
  );

  testWidgets('TodayScreen shows pending without opens, in deadline order', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(450, 2000));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authControllerProvider.overrideWith(
            _UnauthenticatedAuthController.new,
          ),
          marketsProvider.overrideWith(
            (ref) async => [
              _market(
                slug: 'old',
                title: 'Apuração antiga',
                status: 'locked',
                closeAt: '2026-11-01T00:00:00Z',
              ),
              _market(slug: 'new', title: 'Apuração recente', status: 'locked'),
              _market(
                slug: 'tie',
                title: 'Apuração empatada',
                status: 'locked',
              ),
              _market(
                slug: 'missing',
                title: 'Apuração sem data',
                status: 'locked',
                closeAt: '',
              ),
              for (final status in ['resolved', 'sealed', 'draft', 'canceled'])
                _market(slug: status, title: 'Oculto $status', status: status),
            ],
          ),
        ],
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: const Scaffold(body: TodayScreen()),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(
      find.text('Nenhum mercado aberto disponível agora.'),
      findsOneWidget,
    );
    final titles = [
      'Apuração recente',
      'Apuração empatada',
      'Apuração antiga',
      'Apuração sem data',
    ];
    for (var i = 0; i < titles.length; i++) {
      expect(find.text(titles[i]), findsOneWidget);
      if (i > 0) {
        expect(
          tester.getTopLeft(find.text(titles[i - 1])).dy,
          lessThan(tester.getTopLeft(find.text(titles[i])).dy),
        );
      }
    }
    for (final status in ['resolved', 'sealed', 'draft', 'canceled']) {
      expect(find.text('Oculto $status'), findsNothing);
    }
    expect(find.text('Tendências'), findsNothing);
    expect(find.text('Mais mercados'), findsNothing);
    expect(find.text('Ver todos em apuração'), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('MarketsScreen filters favorites and user positions', (
    tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authControllerProvider.overrideWith(_AuthenticatedAuthController.new),
          marketsProvider.overrideWith((ref) async {
            return [
              _market(
                slug: 'favorito',
                title: 'Mercado salvo pelo usuário',
                favorite: true,
              ),
              _market(
                slug: 'posicao',
                title: 'Mercado com posição ativa',
                prediction: true,
                activePosition: true,
              ),
              _market(
                slug: 'historico',
                title: 'Mercado com participação histórica',
                status: 'sealed',
                statusLabel: 'Selado',
                prediction: true,
              ),
              _market(slug: 'geral', title: 'Mercado geral'),
            ];
          }),
        ],
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: const Scaffold(body: MarketsScreen()),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Mercado salvo pelo usuário'), findsOneWidget);
    expect(find.text('Mercado com posição ativa'), findsOneWidget);
    expect(find.text('Mercado com participação histórica'), findsNothing);

    await tester.tap(find.text('Favoritos'));
    await tester.pumpAndSettle();

    expect(find.text('Mercado salvo pelo usuário'), findsOneWidget);
    expect(find.text('Mercado com posição ativa'), findsNothing);
    expect(find.text('Mercado com participação histórica'), findsNothing);
    expect(find.text('Mercado geral'), findsNothing);

    await tester.tap(find.text('Posições ativas'));
    await tester.pumpAndSettle();

    expect(find.text('Mercado salvo pelo usuário'), findsNothing);
    expect(find.text('Mercado com posição ativa'), findsOneWidget);
    expect(find.text('Mercado com participação histórica'), findsNothing);
    expect(find.text('Mercado geral'), findsNothing);

    await tester.ensureVisible(find.text('Minhas previsões'));
    await tester.tap(find.text('Minhas previsões'));
    await tester.pumpAndSettle();
    expect(find.text('Mercado com participação histórica'), findsOneWidget);
    expect(find.text('Mercado com posição ativa'), findsOneWidget);
  });

  testWidgets('MarketsScreen separates open discovery and resolved history', (
    tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authControllerProvider.overrideWith(_AuthenticatedAuthController.new),
          marketsProvider.overrideWith(
            (ref) async => [
              _market(
                slug: 'sealed',
                title: 'Histórico selado',
                status: 'sealed',
                statusLabel: 'Selado',
                favorite: true,
                prediction: true,
              ),
              _market(
                slug: 'locked',
                title: 'Mercado em apuração',
                status: 'locked',
                statusLabel: 'Em apuração',
              ),
              _market(
                slug: 'resolved',
                title: 'Resultado em finalização',
                status: 'resolved',
                statusLabel: 'Resolvido',
              ),
              _market(slug: 'open', title: 'Mercado aberto'),
            ],
          ),
        ],
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: const Scaffold(body: MarketsScreen()),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('Mercado aberto'), findsOneWidget);
    expect(find.text('Histórico selado'), findsNothing);
    expect(find.text('Mercado em apuração'), findsOneWidget);
    await tester.tap(find.text('Resolvidos'));
    await tester.pumpAndSettle();
    expect(find.text('Histórico selado'), findsOneWidget);
    expect(find.text('Resultado em finalização'), findsOneWidget);
    expect(find.text('Mercado aberto'), findsNothing);
    await tester.tap(find.text('Favoritos'));
    await tester.pumpAndSettle();
    expect(find.text('Histórico selado'), findsOneWidget);
    await tester.ensureVisible(find.text('Minhas previsões'));
    await tester.tap(find.text('Minhas previsões'));
    await tester.pumpAndSettle();
    expect(find.text('Histórico selado'), findsOneWidget);
    await tester.ensureVisible(find.text('Em andamento'));
    await tester.tap(find.text('Em andamento'));
    await tester.pumpAndSettle();
    expect(find.text('Mercado aberto'), findsOneWidget);
    expect(find.text('Histórico selado'), findsNothing);
    expect(find.text('Mercado em apuração'), findsOneWidget);
  });

  testWidgets('TodayScreen desk counts active positions, not history', (
    tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authControllerProvider.overrideWith(_AuthenticatedAuthController.new),
          marketsProvider.overrideWith((ref) async {
            return [
              _market(
                slug: 'ativa',
                title: 'Mercado aberto com posição ativa',
                prediction: true,
                activePosition: true,
              ),
              _market(
                slug: 'historica',
                title: 'Mercado aberto só com histórico',
                prediction: true,
              ),
              _market(
                slug: 'favorito',
                title: 'Mercado favorito',
                favorite: true,
              ),
            ];
          }),
        ],
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: const Scaffold(body: TodayScreen()),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Sua mesa'), findsOneWidget);
    expect(find.text('Encerram'), findsNothing);
    expect(find.text('Abertas'), findsOneWidget);
    expect(
      find.descendant(
        of: find.byKey(const ValueKey('desk-tile-positions')),
        matching: find.text('1'),
      ),
      findsOneWidget,
    );
    expect(
      find.descendant(
        of: find.byKey(const ValueKey('desk-tile-open-positions')),
        matching: find.text('1'),
      ),
      findsOneWidget,
    );
    expect(
      find.descendant(
        of: find.byKey(const ValueKey('desk-tile-favorites')),
        matching: find.text('1'),
      ),
      findsOneWidget,
    );
    final positionsTile = find.byKey(const ValueKey('desk-tile-positions'));
    final positionsLabel = find.descendant(
      of: positionsTile,
      matching: find.text('Posições'),
    );
    final positionsIcon = find.descendant(
      of: positionsTile,
      matching: find.byIcon(Icons.stacked_line_chart),
    );
    final positionsValue = find.descendant(
      of: positionsTile,
      matching: find.text('1'),
    );
    expect(tester.getSize(positionsTile).height, lessThan(90));
    expect(
      (tester.getTopLeft(positionsValue).dy -
              tester.getTopLeft(positionsIcon).dy)
          .abs(),
      lessThan(4),
    );
    expect(
      tester.getTopLeft(positionsLabel).dy,
      lessThan(tester.getTopLeft(positionsIcon).dy),
    );
  });

  testWidgets('TodayScreen pull refresh waits for fresh market data', (
    tester,
  ) async {
    var calls = 0;
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authControllerProvider.overrideWith(
            _UnauthenticatedAuthController.new,
          ),
          marketsProvider.overrideWith((ref) async {
            calls += 1;
            return [
              _market(
                slug: 'mercado-$calls',
                title: calls == 1
                    ? 'Mercado antes do refresh'
                    : 'Mercado depois do refresh',
              ),
            ];
          }),
        ],
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: const Scaffold(body: TodayScreen()),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(calls, 1);
    expect(find.text('Mercado antes do refresh'), findsOneWidget);

    await tester.drag(find.byType(ListView).last, const Offset(0, 360));
    await tester.pump();
    await tester.pumpAndSettle();

    expect(calls, 2);
    expect(find.text('Mercado depois do refresh'), findsOneWidget);
    expect(find.text('Mercado antes do refresh'), findsNothing);
  });

  testWidgets('TodayScreen empty state can be pulled to refresh', (
    tester,
  ) async {
    var calls = 0;
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authControllerProvider.overrideWith(
            _UnauthenticatedAuthController.new,
          ),
          marketsProvider.overrideWith((ref) async {
            calls += 1;
            if (calls == 1) {
              return <Market>[];
            }
            return [
              _market(
                slug: 'mercado-atualizado',
                title: 'Mercado apareceu depois do refresh',
              ),
            ];
          }),
        ],
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: const Scaffold(body: TodayScreen()),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(calls, 1);
    expect(
      find.text('Nenhum mercado aberto disponível agora.'),
      findsOneWidget,
    );

    await tester.drag(find.byType(ListView).last, const Offset(0, 360));
    await tester.pump();
    await tester.pumpAndSettle();

    expect(calls, 2);
    expect(find.text('Mercado apareceu depois do refresh'), findsOneWidget);
  });

  testWidgets('MarketsScreen empty filter state can be pulled to refresh', (
    tester,
  ) async {
    var calls = 0;
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authControllerProvider.overrideWith(_AuthenticatedAuthController.new),
          marketsProvider.overrideWith((ref) async {
            calls += 1;
            if (calls == 1) {
              return <Market>[];
            }
            return [
              _market(
                slug: 'mercado-atualizado',
                title: 'Mercado atualizado no browse',
              ),
            ];
          }),
        ],
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: const Scaffold(body: MarketsScreen()),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(calls, 1);
    expect(find.text('Nenhum mercado aberto no momento.'), findsOneWidget);

    await tester.drag(find.byType(ListView).last, const Offset(0, 360));
    await tester.pump();
    await tester.pumpAndSettle();

    expect(calls, 2);
    expect(find.text('Mercado atualizado no browse'), findsOneWidget);
  });
}

class _UnauthenticatedAuthController extends AuthController {
  @override
  AuthState build() {
    return const AuthState();
  }
}

class _AuthenticatedAuthController extends AuthController {
  @override
  AuthState build() {
    return const AuthState(
      user: GtlUser(
        id: 1,
        handle: 'tester',
        email: 'tester@example.com',
        displayName: 'Tester',
        emailConfirmed: true,
        isStaff: false,
      ),
    );
  }
}

Market _market({
  required String slug,
  required String title,
  String status = 'open',
  String statusLabel = 'Aberto',
  String createdAt = '2026-01-01T00:00:00Z',
  String closeAt = '2026-11-06T00:00:00Z',
  int participants = 8,
  int volume = 120,
  bool favorite = false,
  bool prediction = false,
  bool activePosition = false,
}) {
  return Market.fromJson({
    'slug': slug,
    'title': title,
    'category': 'Tecnologia',
    'subcategory': 'Apps',
    'event': 'Geral',
    'kind': 'binary',
    'status': status,
    'status_label': statusLabel,
    'created_at': createdAt,
    'close_at': closeAt,
    'primary_outcome': 'SIM',
    'primary_probability': 64,
    'primary_probability_exact': 64.0,
    'human_volume_gtl': volume,
    'human_participants': participants,
    'total_participants': participants,
    'comment_count': 2,
    'market_like_count': 1,
    'view_count': 10,
    'share_count': 0,
    'closes_in': '3d',
    'close_label': 'Fecha em 3 dias',
    'image_url': '',
    'thumb': 'GT',
    'thumb_color': '#35A7FF',
    'summary': 'Resumo',
    'resolution_criteria': 'Critério',
    'viewer_has_favorite': favorite,
    'viewer_has_prediction': prediction,
    'viewer_position': {
      'has_position': activePosition,
      'option_id': activePosition ? 1 : null,
      'option_label': activePosition ? 'SIM' : '',
      'active_stake_amount': activePosition ? 100 : 0,
      'potential_payout_total': activePosition ? 150 : 0,
      'position_count': activePosition ? 1 : 0,
      'reinforcement_count': 0,
      'reinforcement_remaining': activePosition ? 2 : 0,
      'reinforcement_max_count': 2,
      'revision_count': 0,
      'revision_remaining': activePosition ? 1 : 0,
      'revision_penalty_percent': 15,
      'revision_penalty_amount': 0,
      'revision_new_stake_amount': 0,
      'can_reinforce': activePosition,
      'can_revise': activePosition,
      'reinforcement_blocked_reason': '',
      'revision_blocked_reason': '',
      'active_entries': [],
      'history': [],
    },
    'options': [],
  });
}
