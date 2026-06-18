import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gotrendlabs_mobile/src/features/auth/auth_controller.dart';
import 'package:gotrendlabs_mobile/src/features/auth/auth_models.dart';
import 'package:gotrendlabs_mobile/src/features/markets/market_models.dart';
import 'package:gotrendlabs_mobile/src/features/markets/markets_providers.dart';
import 'package:gotrendlabs_mobile/src/features/shell/shell_screen.dart';
import 'package:gotrendlabs_mobile/src/theme.dart';

void main() {
  testWidgets('Shell puts Ranking in the bottom nav and removes Insights', (
    tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authControllerProvider.overrideWith(
            _UnauthenticatedAuthController.new,
          ),
          marketsProvider.overrideWith((ref) async => [_market()]),
          rankingPayloadProvider.overrideWith((ref, filters) async {
            return {
              'rows': <Map<String, dynamic>>[],
              'categories': <Map<String, dynamic>>[],
            };
          }),
        ],
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: const ShellScreen(),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Ranking'), findsOneWidget);
    expect(find.text('Insights'), findsNothing);

    await tester.tap(find.byIcon(Icons.more_horiz));
    await tester.pumpAndSettle();

    expect(find.text('Insights'), findsNothing);
    expect(find.text('Ranking'), findsOneWidget);
    expect(find.text('Sugerir mercado'), findsOneWidget);
    expect(find.text('Suporte'), findsOneWidget);
    final menuLabels = [
      'Wallet',
      'Badges',
      'Desempenho',
      'Suporte',
      'Sugerir mercado',
      'Política e segurança',
      'Sobre',
    ];
    for (var index = 1; index < menuLabels.length; index += 1) {
      expect(
        tester.getTopLeft(find.text(menuLabels[index - 1])).dy,
        lessThan(tester.getTopLeft(find.text(menuLabels[index])).dy),
      );
    }
  });

  testWidgets('Shell refreshes live market and wallet data on app resume', (
    tester,
  ) async {
    var marketCalls = 0;
    var rankingCalls = 0;
    var notificationCalls = 0;
    var ledgerCalls = 0;
    var walletCalls = 0;
    var rechargeCalls = 0;
    final container = ProviderContainer(
      overrides: [
        authControllerProvider.overrideWith(_AuthenticatedAuthController.new),
        marketsProvider.overrideWith((ref) async {
          marketCalls += 1;
          return [_market()];
        }),
        notificationsProvider.overrideWith((ref) async {
          notificationCalls += 1;
          return <dynamic>[];
        }),
        ledgerProvider.overrideWith((ref) async {
          ledgerCalls += 1;
          return {'wallet': <String, dynamic>{}, 'entries': <dynamic>[]};
        }),
        walletProvider.overrideWith((ref) async {
          walletCalls += 1;
          return <String, dynamic>{};
        }),
        walletRechargeRequestsProvider.overrideWith((ref) async {
          rechargeCalls += 1;
          return <String, dynamic>{'requests': <dynamic>[]};
        }),
        rankingPayloadProvider.overrideWith((ref, filters) async {
          rankingCalls += 1;
          return {
            'rows': <Map<String, dynamic>>[],
            'categories': <Map<String, dynamic>>[],
          };
        }),
      ],
    );
    addTearDown(container.dispose);

    await container.read(ledgerProvider.future);
    await container.read(walletProvider.future);
    await container.read(walletRechargeRequestsProvider.future);

    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: const ShellScreen(),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(marketCalls, 1);
    expect(notificationCalls, 1);
    expect(ledgerCalls, 1);
    expect(walletCalls, 1);
    expect(rechargeCalls, 1);
    expect(rankingCalls, 0);

    await tester.tap(find.text('Ranking').last);
    await tester.pumpAndSettle();
    final rankingCallsAfterOpen = rankingCalls;
    expect(rankingCallsAfterOpen, 1);

    tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.resumed);
    await tester.pumpAndSettle();
    await container.read(ledgerProvider.future);
    await container.read(walletProvider.future);
    await container.read(walletRechargeRequestsProvider.future);

    expect(marketCalls, 2);
    expect(notificationCalls, 2);
    expect(ledgerCalls, 2);
    expect(walletCalls, 2);
    expect(rechargeCalls, 2);
    expect(rankingCalls, greaterThan(rankingCallsAfterOpen));
  });

  testWidgets('Shell refreshes ranking when Ranking tab is selected', (
    tester,
  ) async {
    var rankingCalls = 0;
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authControllerProvider.overrideWith(
            _UnauthenticatedAuthController.new,
          ),
          marketsProvider.overrideWith((ref) async => [_market()]),
          rankingPayloadProvider.overrideWith((ref, filters) async {
            rankingCalls += 1;
            return {
              'rows': <Map<String, dynamic>>[],
              'categories': <Map<String, dynamic>>[],
            };
          }),
        ],
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: const ShellScreen(),
        ),
      ),
    );
    await tester.pumpAndSettle();

    final rankingCallsAfterOpen = rankingCalls;
    expect(rankingCallsAfterOpen, 0);

    await tester.tap(find.text('Ranking').last);
    await tester.pumpAndSettle();

    expect(rankingCalls, 1);
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

Market _market() {
  return Market.fromJson({
    'slug': 'mercado-shell',
    'title': 'Mercado para teste de shell',
    'category': 'Tecnologia',
    'subcategory': 'Apps',
    'event': 'Geral',
    'kind': 'binary',
    'status': 'open',
    'status_label': 'Aberto',
    'primary_outcome': 'SIM',
    'primary_probability': 64,
    'primary_probability_exact': 64.0,
    'human_volume_gtl': 120,
    'human_participants': 8,
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
    'options': [],
  });
}
