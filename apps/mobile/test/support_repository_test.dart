import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gotrendlabs_mobile/src/core/api_client.dart';
import 'package:gotrendlabs_mobile/src/features/support/support_repository.dart';

void main() {
  test('sendFeedback posts to feedback endpoint', () async {
    final dio = Dio(BaseOptions(baseUrl: 'http://api.test'));
    dio.httpClientAdapter = _Adapter((options, body) {
      expect(options.method, 'POST');
      expect(options.path, '/feedback');
      expect(body['feedback_type'], 'Bug de produto');
      expect(body['severity'], 'medium');
      expect(body['description'], 'Preciso de ajuda.');
      return {'id': 1, 'kind': 'feedback', 'status': 'pending'};
    });
    final repo = SupportRepository(
      ApiClient(dio: dio, tokenStore: MemoryTokenStore()),
    );

    await repo.sendFeedback(
      feedbackType: 'Bug de produto',
      description: 'Preciso de ajuda.',
    );
  });

  test('suggestMarket posts to suggestions endpoint', () async {
    final dio = Dio(BaseOptions(baseUrl: 'http://api.test'));
    dio.httpClientAdapter = _Adapter((options, body) {
      expect(options.method, 'POST');
      expect(options.path, '/suggestions');
      expect(body['question'], 'Este mercado deve existir?');
      expect(body['category'], 'Tecnologia');
      expect(body['subcategory'], '');
      expect(body['kind'], 'binary');
      expect(body['suggested_source'], 'Fonte pública');
      return {'id': 2, 'kind': 'suggestion', 'status': 'pending'};
    });
    final repo = SupportRepository(
      ApiClient(dio: dio, tokenStore: MemoryTokenStore()),
    );

    await repo.suggestMarket(
      question: 'Este mercado deve existir?',
      category: 'Tecnologia',
      subcategory: '',
      suggestedSource: 'Fonte pública',
      rationale: 'Ajuda a comunidade.',
    );
  });
}

class _Adapter implements HttpClientAdapter {
  _Adapter(this.handler);

  final Object Function(RequestOptions options, Map<String, dynamic> body)
  handler;

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    final bytes = await requestStream?.fold<List<int>>(
      <int>[],
      (previous, chunk) => previous..addAll(chunk),
    );
    final body = jsonDecode(utf8.decode(bytes ?? <int>[])) as Map;
    return ResponseBody.fromString(
      jsonEncode(handler(options, Map<String, dynamic>.from(body))),
      200,
      headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      },
    );
  }

  @override
  void close({bool force = false}) {}
}
