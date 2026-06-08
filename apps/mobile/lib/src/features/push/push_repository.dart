import '../../core/api_client.dart';
import 'push_models.dart';

class PushRepository {
  const PushRepository(this._api);

  final ApiClient _api;

  Future<List<PushDevice>> devices() async {
    final json = await _api.getMap('/users/me/push-devices');
    final rawDevices = (json['devices'] as List<dynamic>?) ?? [];
    return rawDevices
        .whereType<Map>()
        .map((item) => PushDevice.fromJson(Map<String, dynamic>.from(item)))
        .toList();
  }

  Future<PushDevice> registerDevice(PushTokenSnapshot snapshot) async {
    final json = await _api.postMap(
      '/users/me/push-devices',
      data: {
        'provider': 'fcm',
        'platform': snapshot.platform,
        'token': snapshot.token,
        'app_version': snapshot.appVersion,
        'build_number': snapshot.buildNumber,
        'device_label': snapshot.deviceLabel,
      },
    );
    return PushDevice.fromJson(json);
  }

  Future<PushDevice> revokeDevice(int deviceId) async {
    final json = await _api.deleteMap('/users/me/push-devices/$deviceId');
    return PushDevice.fromJson(json);
  }

  Future<PushPreferenceSet> preferences() async {
    final json = await _api.getMap('/users/me/push-preferences');
    return PushPreferenceSet.fromJson(json);
  }

  Future<PushPreferenceSet> setGlobalEnabled(bool enabled) async {
    final json = await _api.patchMap(
      '/users/me/push-preferences',
      data: {'global_enabled': enabled},
    );
    return PushPreferenceSet.fromJson(json);
  }
}
