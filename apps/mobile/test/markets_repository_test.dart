import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gotrendlabs_mobile/src/core/api_client.dart';
import 'package:gotrendlabs_mobile/src/features/markets/markets_repository.dart';

void main() {
  test('listMarkets parses FastAPI market response', () async {
    final dio = Dio(BaseOptions(baseUrl: 'http://api.test'));
    dio.httpClientAdapter = _Adapter((options) {
      expect(options.path, '/markets');
      return {
        'markets': [
          {
            'slug': 'btc-junho',
            'title': 'Bitcoin fecha acima de 80k?',
            'category': 'Mercado',
            'subcategory': 'Cripto',
            'event': 'Bitcoin',
            'kind': 'binary',
            'status': 'open',
            'status_label': 'Aberto',
            'primary_outcome': 'SIM',
            'primary_probability': 51,
            'primary_probability_exact': 51.4,
            'human_volume_gtl': 20,
            'human_participants': 2,
            'comment_count': 1,
            'market_like_count': 3,
            'view_count': 4,
            'closes_in': '2d',
            'close_label': 'Fecha em breve',
            'image_url': '',
            'thumb': 'BTC',
            'thumb_color': '#f2a900',
            'summary': 'Resumo',
            'resolution_criteria': 'Fonte pública',
            'options': [
              {
                'id': 1,
                'label': 'SIM',
                'probability': 51,
                'probability_exact': 51.4,
              },
            ],
          },
        ],
      };
    });
    final repo = MarketsRepository(
      ApiClient(dio: dio, tokenStore: MemoryTokenStore()),
    );

    final markets = await repo.listMarkets();

    expect(markets, hasLength(1));
    expect(markets.first.slug, 'btc-junho');
    expect(markets.first.options.first.label, 'SIM');
  });

  test('trackShare posts to FastAPI share endpoint', () async {
    final dio = Dio(BaseOptions(baseUrl: 'http://api.test'));
    var called = false;
    dio.httpClientAdapter = _Adapter((options) {
      expect(options.method, 'POST');
      expect(options.path, '/markets/btc-junho/share');
      called = true;
      return {'view_count': 4, 'share_count': 2};
    });
    final repo = MarketsRepository(
      ApiClient(dio: dio, tokenStore: MemoryTokenStore()),
    );

    await repo.trackShare('btc-junho');

    expect(called, isTrue);
  });

  test('trackView posts to FastAPI view endpoint', () async {
    final dio = Dio(BaseOptions(baseUrl: 'http://api.test'));
    var called = false;
    dio.httpClientAdapter = _Adapter((options) {
      expect(options.method, 'POST');
      expect(options.path, '/markets/btc-junho/view');
      called = true;
      return {'view_count': 5, 'share_count': 2};
    });
    final repo = MarketsRepository(
      ApiClient(dio: dio, tokenStore: MemoryTokenStore()),
    );

    await repo.trackView('btc-junho');

    expect(called, isTrue);
  });

  test(
    'previewPositionAction posts to FastAPI position preview endpoint',
    () async {
      final dio = Dio(BaseOptions(baseUrl: 'http://api.test'));
      dio.httpClientAdapter = _Adapter((options) {
        expect(options.method, 'POST');
        expect(options.path, '/markets/btc-junho/position-preview');
        final data = Map<String, dynamic>.from(options.data as Map);
        expect(data['action'], 'reinforcement');
        expect(data['option_id'], 1);
        expect(data['stake_amount'], 80);
        return {
          'market_id': 10,
          'option_id': 1,
          'action': 'reinforcement',
          'stake_amount': 80,
          'active_stake_amount': 120,
          'active_position_count': 2,
          'penalty_amount': 0,
          'revision_penalty_percent': 10,
          'new_position_stake_amount': 80,
          'position_total_after': 200,
          'probability_exact': 50.0,
          'estimated_return': 160,
          'reinforcement_remaining': 1,
          'revision_remaining': 1,
          'allowed': true,
          'blocked_reason': '',
        };
      });
      final repo = MarketsRepository(
        ApiClient(dio: dio, tokenStore: MemoryTokenStore()),
      );

      final preview = await repo.previewPositionAction(
        slug: 'btc-junho',
        action: 'reinforcement',
        optionId: 1,
        stakeAmount: 80,
      );

      expect(preview.positionTotalAfter, 200);
      expect(preview.allowed, isTrue);
    },
  );

  test('previewPositionAction treats missing allowed as blocked', () async {
    final dio = Dio(BaseOptions(baseUrl: 'http://api.test'));
    dio.httpClientAdapter = _Adapter((options) {
      expect(options.method, 'POST');
      expect(options.path, '/markets/btc-junho/position-preview');
      return {
        'market_id': 10,
        'option_id': 1,
        'action': 'reinforcement',
        'stake_amount': 80,
        'active_stake_amount': 120,
        'active_position_count': 2,
        'penalty_amount': 0,
        'revision_penalty_percent': 10,
        'new_position_stake_amount': 80,
        'position_total_after': 200,
        'probability_exact': 50.0,
        'estimated_return': 160,
        'reinforcement_remaining': 1,
        'revision_remaining': 1,
        'blocked_reason': '',
      };
    });
    final repo = MarketsRepository(
      ApiClient(dio: dio, tokenStore: MemoryTokenStore()),
    );

    final preview = await repo.previewPositionAction(
      slug: 'btc-junho',
      action: 'reinforcement',
      optionId: 1,
      stakeAmount: 80,
    );

    expect(preview.allowed, isFalse);
  });

  test(
    'createPositionAction posts to FastAPI position actions endpoint',
    () async {
      final dio = Dio(BaseOptions(baseUrl: 'http://api.test'));
      dio.httpClientAdapter = _Adapter((options) {
        expect(options.method, 'POST');
        expect(options.path, '/markets/btc-junho/position-actions');
        final data = Map<String, dynamic>.from(options.data as Map);
        expect(data['action'], 'revision');
        expect(data['option_id'], 2);
        expect(data['stake_amount'], 0);
        return {
          'prediction_id': 30,
          'market_id': 10,
          'option_id': 2,
          'action': 'revision',
          'stake_amount': 108,
          'penalty_amount': 12,
          'accepted_at': '2026-06-14T12:00:00Z',
          'wallet_balance_after': {},
          'market_probability_snapshot': [],
          'potential_payout': 216,
          'viewer_position': {
            'has_position': true,
            'option_id': 2,
            'option_label': 'NÃO',
            'active_stake_amount': 108,
          },
        };
      });
      final repo = MarketsRepository(
        ApiClient(dio: dio, tokenStore: MemoryTokenStore()),
      );

      final result = await repo.createPositionAction(
        slug: 'btc-junho',
        action: 'revision',
        optionId: 2,
        stakeAmount: 0,
      );

      expect(result.action, 'revision');
      expect(result.penaltyAmount, 12);
      expect(result.viewerPosition.optionLabel, 'NÃO');
    },
  );
}

class _Adapter implements HttpClientAdapter {
  _Adapter(this.handler);

  final Map<String, dynamic> Function(RequestOptions options) handler;

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    return ResponseBody.fromString(
      jsonEncode(handler(options)),
      200,
      headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      },
    );
  }

  @override
  void close({bool force = false}) {}
}
