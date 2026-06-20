import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:package_info_plus/package_info_plus.dart';

import 'environment.dart';

abstract class TokenStore {
  Future<String?> readToken();
  Future<void> writeToken(String token);
  Future<void> clearToken();
}

class SecureTokenStore implements TokenStore {
  SecureTokenStore() : _storage = const FlutterSecureStorage();

  static const _key = 'gotrendlabs.session.token';
  final FlutterSecureStorage _storage;

  @override
  Future<String?> readToken() => _storage.read(key: _key);

  @override
  Future<void> writeToken(String token) =>
      _storage.write(key: _key, value: token);

  @override
  Future<void> clearToken() => _storage.delete(key: _key);
}

class MemoryTokenStore implements TokenStore {
  String? token;

  @override
  Future<String?> readToken() async => token;

  @override
  Future<void> writeToken(String token) async {
    this.token = token;
  }

  @override
  Future<void> clearToken() async {
    token = null;
  }
}

typedef PackageInfoLoader = Future<PackageInfo> Function();
typedef AppUpdateRequiredHandler = void Function(Map<String, dynamic> payload);

class ApiClient {
  ApiClient({
    Dio? dio,
    TokenStore? tokenStore,
    String baseUrl = AppEnvironment.apiBaseUrl,
    PackageInfoLoader? packageInfoLoader,
    this.onAppUpdateRequired,
    String? appVersion,
    String? appBuild,
  }) : _dio =
           dio ??
           Dio(
             BaseOptions(
               baseUrl: baseUrl,
               connectTimeout: const Duration(seconds: 8),
               receiveTimeout: const Duration(seconds: 12),
               headers: {
                 'Accept': 'application/json',
                 'X-GoTrendLabs-Client': 'mobile',
               },
             ),
           ),
       _tokenStore = tokenStore ?? SecureTokenStore(),
       _baseUrl = baseUrl,
       _packageInfoLoader = packageInfoLoader ?? PackageInfo.fromPlatform {
    _appVersion = appVersion;
    _appBuild = appBuild;
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          options.headers.putIfAbsent('Accept', () => 'application/json');
          options.headers.putIfAbsent('X-GoTrendLabs-Client', () => 'mobile');
          final appHeaders = await _appHeaders();
          options.headers.putIfAbsent(
            'X-GoTrendLabs-App-Version',
            () => appHeaders.version,
          );
          options.headers.putIfAbsent(
            'X-GoTrendLabs-App-Build',
            () => appHeaders.build,
          );
          final token = _token;
          if (token != null && token.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          handler.next(options);
        },
        onError: (error, handler) {
          if (error.response?.statusCode == 426) {
            onAppUpdateRequired?.call(_asMap(error.response?.data));
          }
          handler.next(error);
        },
      ),
    );
  }

  final Dio _dio;
  final TokenStore _tokenStore;
  final String _baseUrl;
  final PackageInfoLoader _packageInfoLoader;
  final AppUpdateRequiredHandler? onAppUpdateRequired;
  String? _appVersion;
  String? _appBuild;
  String? _token;

  Future<void> restoreToken() async {
    _token = await _tokenStore.readToken();
  }

  Future<String?> readStoredToken() => _tokenStore.readToken();

  void activateToken(String token) {
    _token = token;
  }

  Future<void> setToken(String token, {bool persist = true}) async {
    _token = token;
    if (persist) {
      await _tokenStore.writeToken(token);
    } else {
      await _tokenStore.clearToken();
    }
  }

  Future<void> clearToken() async {
    _token = null;
    await _tokenStore.clearToken();
  }

  Future<_AppHeaders> _appHeaders() async {
    final version = (_appVersion ?? '').trim();
    final build = (_appBuild ?? '').trim();
    if (version.isNotEmpty && build.isNotEmpty) {
      return _AppHeaders(version: version, build: build);
    }
    try {
      final info = await _packageInfoLoader();
      final loadedVersion = info.version.trim();
      final loadedBuild = info.buildNumber.trim();
      if (loadedVersion.isNotEmpty) {
        _appVersion = loadedVersion;
      }
      if (loadedBuild.isNotEmpty) {
        _appBuild = loadedBuild;
      }
    } catch (_) {
      return const _AppHeaders(version: '0.0.0', build: '0');
    }
    return _AppHeaders(
      version: (_appVersion ?? '').isEmpty ? '0.0.0' : _appVersion!,
      build: (_appBuild ?? '').isEmpty ? '0' : _appBuild!,
    );
  }

  String resolveUrl(String path) {
    if (path.startsWith('http://') || path.startsWith('https://')) {
      return path;
    }
    if (path.isEmpty) {
      return '';
    }
    final base = Uri.parse(
      path.startsWith('/media/') ? AppEnvironment.publicWebBaseUrl : _baseUrl,
    );
    return base.replace(path: path).toString();
  }

  Future<Map<String, dynamic>> getMap(
    String path, {
    Map<String, dynamic>? query,
  }) async {
    final response = await _dio.get<Object?>(path, queryParameters: query);
    return _asMap(response.data);
  }

  Future<List<dynamic>> getList(String path, String key) async {
    final response = await _dio.get<Object?>(path);
    final data = response.data;
    if (data is List<dynamic>) {
      return data;
    }
    if (data is List) {
      return List<dynamic>.from(data);
    }
    final map = _asMap(data);
    return (map[key] as List<dynamic>?) ?? <dynamic>[];
  }

  Future<Map<String, dynamic>> postMap(String path, {Object? data}) async {
    final response = await _dio.post<Object?>(path, data: data);
    return _asMap(response.data);
  }

  Future<Map<String, dynamic>> patchMap(String path, {Object? data}) async {
    final response = await _dio.patch<Object?>(path, data: data);
    return _asMap(response.data);
  }

  Future<void> postEmpty(String path, {Object? data}) async {
    await _dio.post<Object?>(path, data: data);
  }

  Future<Map<String, dynamic>> deleteMap(String path) async {
    final response = await _dio.delete<Object?>(path);
    return _asMap(response.data);
  }

  Map<String, dynamic> _asMap(Object? value) {
    if (value is Map<String, dynamic>) {
      return value;
    }
    if (value is Map) {
      return Map<String, dynamic>.from(value);
    }
    return <String, dynamic>{};
  }
}

class _AppHeaders {
  const _AppHeaders({required this.version, required this.build});

  final String version;
  final String build;
}

class ApiFailure implements Exception {
  ApiFailure(this.category, this.message);

  final String category;
  final String message;

  static ApiFailure fromObject(Object error) {
    if (error is ApiFailure) {
      return error;
    }
    if (error is DioException) {
      final statusCode = error.response?.statusCode ?? 0;
      final detail = _detailMessage(error.response?.data);
      if (error.type == DioExceptionType.connectionTimeout ||
          error.type == DioExceptionType.receiveTimeout ||
          error.type == DioExceptionType.connectionError) {
        return ApiFailure('network', 'Não foi possível alcançar a API.');
      }
      if (statusCode == 401) {
        return ApiFailure(
          'unauthenticated',
          detail ?? 'Sessão ausente ou expirada.',
        );
      }
      if (statusCode == 403) {
        return ApiFailure('forbidden', detail ?? 'Ação não permitida.');
      }
      if (statusCode == 426) {
        return ApiFailure(
          'app_update_required',
          detail ?? 'Atualize o app para continuar usando o GoTrendLabs.',
        );
      }
      if (statusCode == 409 || statusCode == 422) {
        final lower = (detail ?? '').toLowerCase();
        final validationMessage = _validationMessage(lower);
        if (validationMessage != null) {
          return ApiFailure('validation', validationMessage);
        }
        if (lower.contains('saldo')) {
          return ApiFailure(
            'insufficient_balance',
            detail ?? 'Saldo educativo insuficiente.',
          );
        }
        if (lower.contains('mercado') || lower.contains('previs')) {
          return ApiFailure(
            'domain_state',
            detail ?? 'O mercado não aceita esta ação agora.',
          );
        }
        return ApiFailure(
          'validation',
          detail ?? 'Revise os dados informados.',
        );
      }
      return ApiFailure('server', detail ?? 'Falha inesperada da API.');
    }
    return ApiFailure('server', 'Falha inesperada.');
  }

  static String? _detailMessage(Object? data) {
    if (data is! Map) {
      return null;
    }
    final detail = data['detail'];
    if (detail is String) {
      return detail;
    }
    if (detail is List) {
      return detail.map(_detailItemMessage).whereType<String>().join(' ');
    }
    if (detail is Map) {
      return _detailItemMessage(detail);
    }
    return detail?.toString();
  }

  static String? _detailItemMessage(Object? item) {
    if (item is Map) {
      final loc = (item['loc'] as List?)?.join('.') ?? '';
      final msg = item['msg']?.toString() ?? '';
      final reason = item['ctx'] is Map
          ? (item['ctx'] as Map)['reason']?.toString() ?? ''
          : '';
      return '$loc $msg $reason'.trim();
    }
    return item?.toString();
  }

  static String? _validationMessage(String lower) {
    if (lower.contains('email') && lower.contains('@')) {
      return 'Informe um email válido.';
    }
    if (lower.contains('email') && lower.contains('valid')) {
      return 'Informe um email válido.';
    }
    if (lower.contains('body.email')) {
      return 'Informe um email válido.';
    }
    if (lower.contains('terms') || lower.contains('política')) {
      return 'Aceite a política de uso para criar sua conta.';
    }
    if (lower.contains('field required') || lower.contains('missing')) {
      return 'Preencha os campos obrigatórios.';
    }
    if (lower.contains('password') || lower.contains('senha')) {
      return 'Revise a senha informada.';
    }
    if (lower.contains('value_error') || lower.contains('loc:')) {
      return 'Revise os dados informados.';
    }
    return null;
  }

  @override
  String toString() => message;
}
