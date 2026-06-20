import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gotrendlabs_mobile/src/core/api_client.dart';
import 'package:package_info_plus/package_info_plus.dart';

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

  test('setToken can keep login only in memory', () async {
    late RequestOptions captured;
    final store = MemoryTokenStore();
    final dio = Dio(BaseOptions(baseUrl: 'http://api.test'));
    dio.httpClientAdapter = _Adapter((options) {
      captured = options;
      return {'status': 'ok'};
    });
    final api = ApiClient(
      dio: dio,
      tokenStore: store,
      appVersion: '1.0.8',
      appBuild: '9',
    );

    await api.setToken('session-token', persist: false);
    await api.getMap('/auth/session');

    expect(await store.readToken(), isNull);
    expect(captured.headers['Authorization'], 'Bearer session-token');
    expect(captured.headers['X-GoTrendLabs-Client'], 'mobile');
    expect(captured.headers['X-GoTrendLabs-App-Version'], '1.0.8');
    expect(captured.headers['X-GoTrendLabs-App-Build'], '9');
  });

  test('loads package info without caching fallback build zero', () async {
    late RequestOptions captured;
    final dio = Dio(BaseOptions(baseUrl: 'http://api.test'));
    dio.httpClientAdapter = _Adapter((options) {
      captured = options;
      return {'status': 'ok'};
    });
    final api = ApiClient(
      dio: dio,
      tokenStore: MemoryTokenStore(),
      packageInfoLoader: () async {
        await Future<void>.delayed(const Duration(milliseconds: 180));
        return PackageInfo(
          appName: 'GoTrendLabs',
          packageName: 'br.com.gotrendlabs.app',
          version: '1.0.8',
          buildNumber: '9',
        );
      },
    );

    await api.getMap('/health');

    expect(captured.headers['X-GoTrendLabs-App-Version'], '1.0.8');
    expect(captured.headers['X-GoTrendLabs-App-Build'], '9');
  });

  test('ApiClient notifies app update required for any 426 response', () async {
    Map<String, dynamic>? updatePayload;
    final dio = Dio(BaseOptions(baseUrl: 'http://api.test'));
    dio.httpClientAdapter = _StatusAdapter(
      statusCode: 426,
      body: {
        'code': 'app_update_required',
        'detail': 'Atualize.',
        'mobile': {
          'update_required': true,
          'current_app_build': 8,
          'latest_android_build': 9,
        },
      },
    );
    final api = ApiClient(
      dio: dio,
      tokenStore: MemoryTokenStore(),
      appVersion: '1.0.8',
      appBuild: '8',
      onAppUpdateRequired: (payload) => updatePayload = payload,
    );

    await expectLater(
      api.getMap('/users/me/wallet'),
      throwsA(isA<DioException>()),
    );

    expect(updatePayload, isNotNull);
    expect(updatePayload?['code'], 'app_update_required');
    expect((updatePayload?['mobile'] as Map)['latest_android_build'], 9);
  });

  test('ApiFailure hides raw validation payloads', () {
    final failure = ApiFailure.fromObject(
      DioException(
        requestOptions: RequestOptions(path: '/auth/login'),
        response: Response<Object?>(
          requestOptions: RequestOptions(path: '/auth/login'),
          statusCode: 422,
          data: {
            'detail': [
              {
                'type': 'value_error',
                'loc': ['body', 'email'],
                'msg': 'value is not a valid email address',
                'input': '',
                'ctx': {'reason': 'An email address must have an @-sign.'},
              },
            ],
          },
        ),
      ),
    );

    expect(failure.message, 'Informe um email válido.');
  });

  test('ApiFailure maps app update required response', () {
    final failure = ApiFailure.fromObject(
      DioException(
        requestOptions: RequestOptions(path: '/markets'),
        response: Response<Object?>(
          requestOptions: RequestOptions(path: '/markets'),
          statusCode: 426,
          data: {'code': 'app_update_required', 'detail': 'Atualize.'},
        ),
      ),
    );

    expect(failure.category, 'app_update_required');
    expect(failure.message, 'Atualize.');
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

class _StatusAdapter implements HttpClientAdapter {
  _StatusAdapter({required this.statusCode, required this.body});

  final int statusCode;
  final Object body;

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    return ResponseBody.fromString(
      jsonEncode(body),
      statusCode,
      headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      },
    );
  }

  @override
  void close({bool force = false}) {}
}
