import 'dart:math';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'api_client.dart';
import 'providers.dart';

final analyticsTrackerProvider = Provider<AnalyticsTracker>(
  (ref) => AnalyticsTracker(ref.watch(apiClientProvider)),
);

class AnalyticsTracker {
  AnalyticsTracker(this._api);

  final ApiClient _api;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();
  static const _visitorKey = 'gotrendlabs.analytics.visitor';
  String? _visitorId;
  Future<String>? _visitorFuture;
  String _sessionId = _uuid();
  String _viewId = _uuid();
  String _screenKey = 'today';
  DateTime _lastActivity = DateTime.now();

  static String _uuid() {
    final bytes = List<int>.generate(16, (_) => Random.secure().nextInt(256));
    bytes[6] = (bytes[6] & 0x0f) | 0x40;
    bytes[8] = (bytes[8] & 0x3f) | 0x80;
    final hex = bytes
        .map((byte) => byte.toRadixString(16).padLeft(2, '0'))
        .join();
    return '${hex.substring(0, 8)}-${hex.substring(8, 12)}-${hex.substring(12, 16)}-${hex.substring(16, 20)}-${hex.substring(20)}';
  }

  Future<String> _visitor() => _visitorFuture ??= _loadVisitor();

  Future<String> _loadVisitor() async {
    if (_visitorId != null) return _visitorId!;
    final stored = await _storage.read(key: _visitorKey);
    _visitorId = stored ?? _uuid();
    if (stored == null) {
      await _storage.write(key: _visitorKey, value: _visitorId);
    }
    return _visitorId!;
  }

  Future<void> screen(String key) async {
    _screenKey = key;
    _viewId = _uuid();
    await track('screen_viewed');
  }

  Future<void> track(
    String name, {
    String targetKey = '',
    Map<String, Object> properties = const {},
  }) async {
    try {
      final now = DateTime.now();
      final newSession =
          now.difference(_lastActivity) > const Duration(minutes: 30);
      if (newSession) {
        _sessionId = _uuid();
        _viewId = _uuid();
      }
      _lastActivity = now;
      final sessionId = _sessionId;
      final viewId = _viewId;
      final screenKey = _screenKey;
      final visitor = await _visitor();
      final events = <Map<String, Object>>[];
      if (newSession && name != 'screen_viewed') {
        events.add({
          'event_id': _uuid(),
          'view_id': viewId,
          'name': 'screen_viewed',
          'occurred_at': now
              .subtract(const Duration(microseconds: 1))
              .toUtc()
              .toIso8601String(),
          'screen_key': screenKey,
          'target_key': '',
          'properties': <String, Object>{},
        });
      }
      events.add({
        'event_id': _uuid(),
        'view_id': viewId,
        'name': name,
        'occurred_at': now.toUtc().toIso8601String(),
        'screen_key': screenKey,
        'target_key': targetKey,
        'properties': properties,
      });
      await _api.postMap(
        '/analytics/events',
        data: {
          'visitor_id': visitor,
          'session_id': sessionId,
          'entry_screen': screenKey,
          'events': events,
        },
      );
    } catch (_) {
      // Coleta não interrompe a navegação nem as ações do produto.
    }
  }

  Future<void> resetAfterLogout() async {
    _visitorId = null;
    _visitorFuture = null;
    _sessionId = _uuid();
    _viewId = _uuid();
    try {
      await _storage.delete(key: _visitorKey);
    } catch (_) {
      // Falha na telemetria não pode bloquear o logout local.
    }
  }
}
