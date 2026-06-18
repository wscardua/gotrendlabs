import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gotrendlabs_mobile/src/features/auth/auth_controller.dart';
import 'package:gotrendlabs_mobile/src/features/auth/auth_models.dart';
import 'package:gotrendlabs_mobile/src/features/markets/market_models.dart';
import 'package:gotrendlabs_mobile/src/features/markets/markets_providers.dart';
import 'package:gotrendlabs_mobile/src/features/markets/markets_screen.dart';
import 'package:gotrendlabs_mobile/src/theme.dart';

void main() {
  testWidgets('TodayScreen shows only open markets ordered by engagement', (
    tester,
  ) async {
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
                title: 'Mercado fechado não deve aparecer',
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
    expect(find.text('Mercado fechado não deve aparecer'), findsNothing);
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
    expect(find.text('Mercado com participação histórica'), findsOneWidget);

    await tester.tap(find.text('Favoritos'));
    await tester.pumpAndSettle();

    expect(find.text('Mercado salvo pelo usuário'), findsOneWidget);
    expect(find.text('Mercado com posição ativa'), findsNothing);
    expect(find.text('Mercado com participação histórica'), findsNothing);
    expect(find.text('Mercado geral'), findsNothing);

    await tester.tap(find.text('Posições'));
    await tester.pumpAndSettle();

    expect(find.text('Mercado salvo pelo usuário'), findsNothing);
    expect(find.text('Mercado com posição ativa'), findsOneWidget);
    expect(find.text('Mercado com participação histórica'), findsNothing);
    expect(find.text('Mercado geral'), findsNothing);
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
    expect(find.text('Nenhum mercado neste recorte.'), findsOneWidget);

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
    'primary_outcome': 'SIM',
    'primary_probability': 64,
    'primary_probability_exact': 64.0,
    'human_volume_gtl': volume,
    'human_participants': participants,
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
