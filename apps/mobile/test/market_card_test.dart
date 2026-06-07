import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gotrendlabs_mobile/src/core/api_client.dart';
import 'package:gotrendlabs_mobile/src/features/markets/market_cards.dart';
import 'package:gotrendlabs_mobile/src/features/markets/market_models.dart';

void main() {
  testWidgets('MarketHeroCard renders title and probability', (tester) async {
    final market = Market.fromJson({
      'slug': 'mercado-teste',
      'title': 'O mercado teste ficará aberto?',
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
      'closes_in': '3d',
      'close_label': 'Fecha em 3 dias',
      'thumb': 'GT',
      'thumb_color': '#35A7FF',
      'summary': 'Resumo',
      'resolution_criteria': 'Critério',
      'options': [],
    });

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
}
