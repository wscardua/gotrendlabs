import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:gotrendlabs_mobile/src/core/api_client.dart';
import 'package:gotrendlabs_mobile/src/features/markets/market_cards.dart';
import 'package:gotrendlabs_mobile/src/features/markets/market_models.dart';
import 'package:gotrendlabs_mobile/src/features/markets/sparkline_painter.dart';
import 'package:gotrendlabs_mobile/src/theme.dart';

void main() {
  testWidgets('MarketHeroCard renders title and probability', (tester) async {
    final market = _market();

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: MarketHeroCard(
            market: market,
            api: ApiClient(tokenStore: MemoryTokenStore()),
          ),
        ),
      ),
    );

    expect(find.text('O mercado teste ficará aberto?'), findsOneWidget);
    expect(find.text('64%'), findsOneWidget);
  });

  testWidgets('MarketHeroCard does not invent category initials', (
    tester,
  ) async {
    final market = _market(category: 'Brasil', thumb: '');

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: MarketHeroCard(
            market: market,
            api: ApiClient(tokenStore: MemoryTokenStore()),
          ),
        ),
      ),
    );

    expect(find.byIcon(Icons.auto_graph), findsOneWidget);
    expect(find.text('BR'), findsNothing);
  });

  testWidgets('MarketCompactCard shows viewer favorite and position badges', (
    tester,
  ) async {
    final market = _market(favorite: true, prediction: true);

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: MarketCompactCard(
            market: market,
            api: ApiClient(tokenStore: MemoryTokenStore()),
          ),
        ),
      ),
    );

    expect(find.text('Posição'), findsOneWidget);
    expect(find.text('Favorito'), findsOneWidget);
  });

  testWidgets('MarketCompactCard shows compact time remaining', (tester) async {
    final market = _market();

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: MarketCompactCard(
            market: market,
            api: ApiClient(tokenStore: MemoryTokenStore()),
            showStatus: false,
          ),
        ),
      ),
    );

    expect(find.text('3d'), findsWidgets);
    expect(find.byType(LinearProgressIndicator), findsOneWidget);
  });

  testWidgets('MarketCompactCard comment count opens community tab', (
    tester,
  ) async {
    final router = GoRouter(
      routes: [
        GoRoute(
          path: '/',
          builder: (context, state) => Scaffold(
            body: MarketCompactCard(
              market: _market(),
              api: ApiClient(tokenStore: MemoryTokenStore()),
            ),
          ),
        ),
        GoRoute(
          path: '/markets/:slug',
          builder: (context, state) => Text(
            '${state.pathParameters['slug']} ${state.uri.queryParameters['tab']}',
          ),
        ),
      ],
    );

    await tester.pumpWidget(MaterialApp.router(routerConfig: router));

    await tester.tap(find.text('2'));
    await tester.pumpAndSettle();

    expect(find.text('mercado-teste community'), findsOneWidget);
  });

  testWidgets('MarketMetricPanel comment tile opens community tab', (
    tester,
  ) async {
    final router = GoRouter(
      routes: [
        GoRoute(
          path: '/',
          builder: (context, state) =>
              Scaffold(body: MarketMetricPanel(market: _market())),
        ),
        GoRoute(
          path: '/markets/:slug',
          builder: (context, state) => Text(
            '${state.pathParameters['slug']} ${state.uri.queryParameters['tab']}',
          ),
        ),
      ],
    );

    await tester.pumpWidget(MaterialApp.router(routerConfig: router));

    await tester.tap(find.text('COMENTÁRIOS'));
    await tester.pumpAndSettle();

    expect(find.text('mercado-teste community'), findsOneWidget);
  });

  testWidgets('MarketCompactCard time rail changes color with urgency', (
    tester,
  ) async {
    Future<Color> renderRailColor(String closesIn) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: MarketCompactCard(
              market: _market(closesIn: closesIn),
              api: ApiClient(tokenStore: MemoryTokenStore()),
              showStatus: false,
            ),
          ),
        ),
      );
      final indicator = tester.widget<LinearProgressIndicator>(
        find.byType(LinearProgressIndicator),
      );
      return indicator.valueColor!.value!;
    }

    final roomyColor = await renderRailColor('20d');
    final urgentColor = await renderRailColor('1h');

    expect(roomyColor, isNot(urgentColor));
    expect(urgentColor, GtlColors.accentRed);
  });

  testWidgets('MarketCompactCard truncates long closed deadline labels', (
    tester,
  ) async {
    final market = _market(
      status: 'locked',
      statusLabel: 'Fechado',
      closesIn: 'fim',
      closeLabel: 'Fecha em 21/05/2026 16:57 BRT',
    );

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SizedBox(
            width: 360,
            child: MarketCompactCard(
              market: market,
              api: ApiClient(tokenStore: MemoryTokenStore()),
            ),
          ),
        ),
      ),
    );

    expect(find.text('Fechado'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('MarketHeroCard can render as a non-navigable detail hero', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: MarketHeroCard(
            market: _market(),
            api: ApiClient(tokenStore: MemoryTokenStore()),
            openOnTap: false,
          ),
        ),
      ),
    );

    await tester.tap(find.byType(MarketHeroCard));
    await tester.pump();

    expect(tester.takeException(), isNull);
  });

  testWidgets('MarketSparklineCard renders one line per option series', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: MarketSparklineCard(market: _market())),
      ),
    );

    expect(find.byType(SparklinePath), findsNWidgets(2));
    expect(find.text('SIM'), findsOneWidget);
    expect(find.text('NÃO'), findsOneWidget);
  });
}

Market _market({
  String category = 'Tecnologia',
  String thumb = 'GT',
  bool favorite = false,
  bool prediction = false,
  String status = 'open',
  String statusLabel = 'Aberto',
  String closesIn = '3d',
  String closeLabel = 'Fecha em 3 dias',
}) {
  return Market.fromJson({
    'slug': 'mercado-teste',
    'title': 'O mercado teste ficará aberto?',
    'category': category,
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
    'comment_count': 2,
    'market_like_count': 1,
    'view_count': 10,
    'share_count': 0,
    'closes_in': closesIn,
    'close_label': closeLabel,
    'image_url': '',
    'thumb': thumb,
    'thumb_color': '#35A7FF',
    'summary': 'Resumo',
    'resolution_criteria': 'Critério',
    'viewer_has_favorite': favorite,
    'viewer_has_prediction': prediction,
    'options': [
      {'id': 1, 'label': 'SIM', 'probability': 64, 'probability_exact': 64.0},
      {'id': 2, 'label': 'NÃO', 'probability': 36, 'probability_exact': 36.0},
    ],
    'sparkline_series': [
      {'id': 1, 'label': 'SIM', 'path': 'M 4 24 L 110 20 L 216 16'},
      {'id': 2, 'label': 'NÃO', 'path': 'M 4 20 L 110 24 L 216 28'},
    ],
  });
}
