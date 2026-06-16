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
}

class _UnauthenticatedAuthController extends AuthController {
  @override
  AuthState build() {
    return const AuthState();
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
