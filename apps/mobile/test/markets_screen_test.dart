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
    expect(find.text('Mercado geral'), findsOneWidget);

    await tester.tap(find.text('Favoritos'));
    await tester.pumpAndSettle();

    expect(find.text('Mercado salvo pelo usuário'), findsOneWidget);
    expect(find.text('Mercado com posição ativa'), findsNothing);
    expect(find.text('Mercado geral'), findsNothing);

    await tester.tap(find.text('Posições'));
    await tester.pumpAndSettle();

    expect(find.text('Mercado salvo pelo usuário'), findsNothing);
    expect(find.text('Mercado com posição ativa'), findsOneWidget);
    expect(find.text('Mercado geral'), findsNothing);
  });
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
  bool favorite = false,
  bool prediction = false,
}) {
  return Market.fromJson({
    'slug': slug,
    'title': title,
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
    'viewer_has_favorite': favorite,
    'viewer_has_prediction': prediction,
    'options': [],
  });
}
