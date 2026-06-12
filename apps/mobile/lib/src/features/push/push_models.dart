class PushDevice {
  const PushDevice({
    required this.id,
    required this.provider,
    required this.platform,
    required this.isActive,
    required this.pushEnabled,
    this.deviceLabel = '',
    this.appVersion = '',
    this.buildNumber = '',
    this.disabledReason = '',
  });

  final int id;
  final String provider;
  final String platform;
  final bool isActive;
  final bool pushEnabled;
  final String deviceLabel;
  final String appVersion;
  final String buildNumber;
  final String disabledReason;

  factory PushDevice.fromJson(Map<String, dynamic> json) {
    return PushDevice(
      id: _safeInt(json['id']),
      provider: json['provider']?.toString() ?? 'fcm',
      platform: json['platform']?.toString() ?? '',
      isActive: json['is_active'] == true,
      pushEnabled: json['push_enabled'] == true,
      deviceLabel: json['device_label']?.toString() ?? '',
      appVersion: json['app_version']?.toString() ?? '',
      buildNumber: json['build_number']?.toString() ?? '',
      disabledReason: json['disabled_reason']?.toString() ?? '',
    );
  }
}

class PushPreference {
  const PushPreference({
    required this.eventType,
    required this.mode,
    required this.pushEnabled,
    required this.defaultUserEnabled,
  });

  final String eventType;
  final String mode;
  final bool pushEnabled;
  final bool defaultUserEnabled;

  factory PushPreference.fromJson(Map<String, dynamic> json) {
    return PushPreference(
      eventType: json['event_type']?.toString() ?? '',
      mode: json['mode']?.toString() ?? 'off',
      pushEnabled: json['push_enabled'] == true,
      defaultUserEnabled: json['default_user_enabled'] != false,
    );
  }
}

class PushPreferenceSet {
  const PushPreferenceSet({
    required this.globalEnabled,
    required this.preferences,
  });

  final bool globalEnabled;
  final List<PushPreference> preferences;

  factory PushPreferenceSet.fromJson(Map<String, dynamic> json) {
    final rawPreferences = (json['preferences'] as List<dynamic>?) ?? [];
    return PushPreferenceSet(
      globalEnabled: json['global_enabled'] != false,
      preferences: rawPreferences
          .whereType<Map>()
          .map(
            (item) => PushPreference.fromJson(Map<String, dynamic>.from(item)),
          )
          .toList(),
    );
  }
}

class PushTokenSnapshot {
  const PushTokenSnapshot.unavailable([this.reason = 'noop'])
    : token = '',
      platform = '',
      appVersion = '',
      buildNumber = '',
      deviceLabel = '';

  const PushTokenSnapshot.available({
    required this.token,
    required this.platform,
    this.appVersion = '',
    this.buildNumber = '',
    this.deviceLabel = '',
    this.reason = '',
  });

  final String token;
  final String platform;
  final String appVersion;
  final String buildNumber;
  final String deviceLabel;
  final String reason;

  bool get isAvailable => token.isNotEmpty && platform.isNotEmpty;
}

class PushState {
  const PushState({
    this.status = 'idle',
    this.reason = '',
    this.devices = const [],
    this.preferences,
    this.error = '',
  });

  final String status;
  final String reason;
  final List<PushDevice> devices;
  final PushPreferenceSet? preferences;
  final String error;

  PushState copyWith({
    String? status,
    String? reason,
    List<PushDevice>? devices,
    PushPreferenceSet? preferences,
    String? error,
  }) {
    return PushState(
      status: status ?? this.status,
      reason: reason ?? this.reason,
      devices: devices ?? this.devices,
      preferences: preferences ?? this.preferences,
      error: error ?? this.error,
    );
  }
}

int _safeInt(Object? value) {
  if (value is int) {
    return value;
  }
  return int.tryParse(value?.toString() ?? '') ?? 0;
}
