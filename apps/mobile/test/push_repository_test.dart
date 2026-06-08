import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gotrendlabs_mobile/src/core/api_client.dart';
import 'package:gotrendlabs_mobile/src/features/push/push_models.dart';
import 'package:gotrendlabs_mobile/src/features/push/push_repository.dart';

void main() {
  test('registerDevice posts FCM token after auth', () async {
    late RequestOptions captured;
    final dio = Dio(BaseOptions(baseUrl: 'http://api.test'));
    dio.httpClientAdapter = _Adapter((options) {
      captured = options;
      return {
        'id': 7,
        'provider': 'fcm',
        'platform': 'android',
        'is_active': true,
        'push_enabled': true,
        'last_registered_at': '2026-06-08T12:00:00Z',
        'created_at': '2026-06-08T12:00:00Z',
        'updated_at': '2026-06-08T12:00:00Z',
      };
    });
    final repo = PushRepository(
      ApiClient(dio: dio, tokenStore: MemoryTokenStore()),
    );

    final device = await repo.registerDevice(
      const PushTokenSnapshot.available(
        token: 'fcm-token-123',
        platform: 'android',
        appVersion: '1.0.0',
        buildNumber: '1',
      ),
    );

    expect(captured.path, '/users/me/push-devices');
    expect(captured.method, 'POST');
    expect((captured.data as Map)['token'], 'fcm-token-123');
    expect(device.id, 7);
    expect(device.isActive, isTrue);
  });

  test('revokeDevice calls the authenticated revoke endpoint', () async {
    late RequestOptions captured;
    final dio = Dio(BaseOptions(baseUrl: 'http://api.test'));
    dio.httpClientAdapter = _Adapter((options) {
      captured = options;
      return {
        'id': 7,
        'provider': 'fcm',
        'platform': 'ios',
        'is_active': false,
        'push_enabled': false,
        'disabled_reason': 'user_revoked',
        'last_registered_at': '2026-06-08T12:00:00Z',
        'created_at': '2026-06-08T12:00:00Z',
        'updated_at': '2026-06-08T12:00:00Z',
      };
    });
    final repo = PushRepository(
      ApiClient(dio: dio, tokenStore: MemoryTokenStore()),
    );

    final device = await repo.revokeDevice(7);

    expect(captured.path, '/users/me/push-devices/7');
    expect(captured.method, 'DELETE');
    expect(device.isActive, isFalse);
    expect(device.disabledReason, 'user_revoked');
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
