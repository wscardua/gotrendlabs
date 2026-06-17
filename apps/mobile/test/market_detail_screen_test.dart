import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gotrendlabs_mobile/src/core/api_client.dart';
import 'package:gotrendlabs_mobile/src/features/auth/auth_controller.dart';
import 'package:gotrendlabs_mobile/src/features/auth/auth_models.dart';
import 'package:gotrendlabs_mobile/src/features/markets/market_detail_screen.dart';
import 'package:gotrendlabs_mobile/src/features/markets/market_models.dart';
import 'package:gotrendlabs_mobile/src/features/markets/markets_providers.dart';
import 'package:gotrendlabs_mobile/src/features/markets/markets_repository.dart';

void main() {
  testWidgets('MarketDetailScreen opens community tab from initial tab', (
    tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authControllerProvider.overrideWith(
            _UnauthenticatedAuthController.new,
          ),
          marketDetailProvider.overrideWith((ref, slug) async => _market()),
          marketsRepositoryProvider.overrideWithValue(_NoopMarketsRepository()),
        ],
        child: const MaterialApp(
          home: MarketDetailScreen(
            slug: 'mercado-longo',
            initialTab: MarketDetailTab.community,
          ),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Comentário público completo'), findsOneWidget);
    expect(find.text('Entrar para comentar'), findsOneWidget);
  });

  testWidgets('MarketDetailScreen renders full title and summary in overview', (
    tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authControllerProvider.overrideWith(
            _UnauthenticatedAuthController.new,
          ),
          marketDetailProvider.overrideWith((ref, slug) async => _market()),
          marketsRepositoryProvider.overrideWithValue(_NoopMarketsRepository()),
        ],
        child: const MaterialApp(
          home: MarketDetailScreen(slug: 'mercado-longo'),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text(_longTitle), findsWidgets);
    expect(find.text(_longSummary), findsWidgets);
  });

  testWidgets('MarketDetailScreen refetches cached detail when opened', (
    tester,
  ) async {
    var detailCalls = 0;
    final container = ProviderContainer(
      overrides: [
        authControllerProvider.overrideWith(_UnauthenticatedAuthController.new),
        marketDetailProvider.overrideWith((ref, slug) async {
          detailCalls += 1;
          return _market(
            status: detailCalls == 1 ? 'open' : 'locked',
            statusLabel: detailCalls == 1 ? 'Aberto' : 'Fechado',
          );
        }),
        marketsRepositoryProvider.overrideWithValue(_NoopMarketsRepository()),
      ],
    );
    addTearDown(container.dispose);

    await container.read(marketDetailProvider('mercado-longo').future);
    expect(detailCalls, 1);

    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: const MaterialApp(
          home: MarketDetailScreen(slug: 'mercado-longo'),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(detailCalls, 2);
    expect(find.text('Fechado'), findsWidgets);
  });
}

class _UnauthenticatedAuthController extends AuthController {
  @override
  AuthState build() {
    return const AuthState();
  }
}

class _NoopMarketsRepository extends MarketsRepository {
  _NoopMarketsRepository() : super(ApiClient(tokenStore: MemoryTokenStore()));

  @override
  Future<void> trackView(String slug) async {}
}

const _longTitle =
    'O mercado de teste com uma pergunta longa deve permanecer totalmente legível no detalhe mobile?';
const _longSummary =
    'Resumo completo do mercado com contexto suficiente para o usuário entender a condição antes de escolher uma opção.';

Market _market({String status = 'open', String statusLabel = 'Aberto'}) {
  return Market.fromJson({
    'slug': 'mercado-longo',
    'title': _longTitle,
    'category': 'Tecnologia',
    'subcategory': 'Apps',
    'event': 'Geral',
    'kind': 'binary',
    'status': status,
    'status_label': statusLabel,
    'primary_outcome': 'SIM',
    'primary_probability': 64,
    'primary_probability_exact': 64.0,
    'human_volume_gtl': 120,
    'human_participants': 8,
    'comment_count': 1,
    'market_like_count': 1,
    'view_count': 10,
    'share_count': 0,
    'closes_in': '3d',
    'close_label': 'Fecha em 3 dias',
    'image_url': '',
    'thumb': 'GT',
    'thumb_color': '#35A7FF',
    'summary': _longSummary,
    'resolution_criteria': 'Critério',
    'viewer_has_favorite': false,
    'viewer_has_prediction': false,
    'options': [
      {'id': 1, 'label': 'SIM', 'probability': 64, 'probability_exact': 64.0},
      {'id': 2, 'label': 'NÃO', 'probability': 36, 'probability_exact': 36.0},
    ],
    'comments': [
      {
        'id': 1,
        'author_handle': 'tester',
        'author_display_name': 'Tester',
        'author_is_bot': false,
        'body': 'Comentário público completo',
        'created_at_label': 'agora',
        'like_count': 0,
        'dislike_count': 0,
      },
    ],
  });
}
