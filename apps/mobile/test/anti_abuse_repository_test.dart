import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gotrendlabs_mobile/src/core/api_client.dart';
import 'package:gotrendlabs_mobile/src/features/anti_abuse/anti_abuse_repository.dart';

void main() {
  test('fetchChallenge reads anti abuse challenge endpoint', () async {
    final dio = Dio(BaseOptions(baseUrl: 'http://api.test'));
    dio.httpClientAdapter = _Adapter((options) {
      expect(options.method, 'GET');
      expect(options.path, '/anti-abuse/challenge');
      return {
        'prompt': 'Quanto é 2 + 3?',
        'token': 'challenge-token',
        'expires_at': '2026-06-14T00:10:00Z',
      };
    });
    final repo = AntiAbuseRepository(
      ApiClient(dio: dio, tokenStore: MemoryTokenStore()),
    );

    final challenge = await repo.fetchChallenge();

    expect(challenge.prompt, 'Quanto é 2 + 3?');
    expect(challenge.token, 'challenge-token');
    expect(challenge.expiresAt, '2026-06-14T00:10:00Z');
  });
}

class _Adapter implements HttpClientAdapter {
  _Adapter(this.handler);

  final Object Function(RequestOptions options) handler;

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
