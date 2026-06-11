import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

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

class ApiClient {
  ApiClient({
    Dio? dio,
    TokenStore? tokenStore,
    String baseUrl = AppEnvironment.apiBaseUrl,
  }) : _dio =
           dio ??
           Dio(
             BaseOptions(
               baseUrl: baseUrl,
               connectTimeout: const Duration(seconds: 8),
               receiveTimeout: const Duration(seconds: 12),
               headers: {'Accept': 'application/json'},
             ),
           ),
       _tokenStore = tokenStore ?? SecureTokenStore(),
       _baseUrl = baseUrl {
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) {
          final token = _token;
          if (token != null && token.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          handler.next(options);
        },
      ),
    );
  }

  final Dio _dio;
  final TokenStore _tokenStore;
  final String _baseUrl;
  String? _token;

  Future<void> restoreToken() async {
    _token = await _tokenStore.readToken();
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
