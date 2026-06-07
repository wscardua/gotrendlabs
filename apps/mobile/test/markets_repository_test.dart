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
