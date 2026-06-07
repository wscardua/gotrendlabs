import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gotrendlabs_mobile/src/core/api_client.dart';

void main() {
  test('resolveUrl sends media paths to public web base', () {
    final api = ApiClient(
      baseUrl: 'http://10.0.2.2:8001',
      tokenStore: MemoryTokenStore(),
    );

    expect(
      api.resolveUrl('/media/badges/founder.png'),
      'http://10.0.2.2:8000/media/badges/founder.png',
    );
  });

  test('getList accepts root array responses', () async {
    final dio = Dio(BaseOptions(baseUrl: 'http://api.test'));
    dio.httpClientAdapter = _Adapter((options) {
      expect(options.path, '/users/me/badges');
      return [
        {'code': 'founder', 'name': 'Fundador', 'status': 'earned'},
      ];
    });
    final api = ApiClient(dio: dio, tokenStore: MemoryTokenStore());

    final badges = await api.getList('/users/me/badges', 'badges');

    expect(badges, hasLength(1));
    expect((badges.first as Map)['code'], 'founder');
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
