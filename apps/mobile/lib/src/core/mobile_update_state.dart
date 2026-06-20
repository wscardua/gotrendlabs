import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'formatters.dart';

const mobileUpdateRequiredMessageDefault =
    'Atualize o app para continuar usando o GoTrendLabs.';

class MobileUpdateInfo {
  const MobileUpdateInfo({
    this.updateRequired = false,
    this.updateAvailable = false,
    this.currentAppVersion = '',
    this.currentAppBuild,
    this.latestAndroidVersion = '',
    this.latestAndroidBuild = 0,
    this.downloadUrl = '',
    this.updateRequiredMessage = mobileUpdateRequiredMessageDefault,
  });

  final bool updateRequired;
  final bool updateAvailable;
  final String currentAppVersion;
  final int? currentAppBuild;
  final String latestAndroidVersion;
  final int latestAndroidBuild;
  final String downloadUrl;
  final String updateRequiredMessage;

  factory MobileUpdateInfo.fromHealthMobile(Map<String, dynamic> mobile) {
    return MobileUpdateInfo(
      updateRequired: safeBool(mobile['update_required']),
      updateAvailable: safeBool(mobile['update_available']),
      currentAppVersion: safeString(mobile['current_app_version']),
      currentAppBuild: mobile['current_app_build'] == null
          ? null
          : safeInt(mobile['current_app_build']),
      latestAndroidVersion: safeString(mobile['latest_android_version']),
      latestAndroidBuild: safeInt(mobile['latest_android_build']),
      downloadUrl: safeString(mobile['download_url']),
      updateRequiredMessage: safeString(
        mobile['update_required_message'],
        mobileUpdateRequiredMessageDefault,
      ),
    );
  }

  factory MobileUpdateInfo.fromApiResponse(Map<String, dynamic> response) {
    final mobile = response['mobile'] is Map
        ? Map<String, dynamic>.from(response['mobile'] as Map)
        : <String, dynamic>{};
    final parsed = MobileUpdateInfo.fromHealthMobile(mobile);
    final message = safeString(mobile['update_required_message']).trim();
    return MobileUpdateInfo(
      updateRequired: safeBool(mobile['update_required'], true),
      updateAvailable: parsed.updateAvailable,
      currentAppVersion: parsed.currentAppVersion,
      currentAppBuild: parsed.currentAppBuild,
      latestAndroidVersion: parsed.latestAndroidVersion,
      latestAndroidBuild: parsed.latestAndroidBuild,
      downloadUrl: parsed.downloadUrl,
      updateRequiredMessage: message.isNotEmpty
          ? message
          : safeString(response['detail'], mobileUpdateRequiredMessageDefault),
    );
  }
}

final mobileUpdateOverrideProvider =
    NotifierProvider<MobileUpdateOverride, MobileUpdateInfo?>(
      MobileUpdateOverride.new,
    );

class MobileUpdateOverride extends Notifier<MobileUpdateInfo?> {
  @override
  MobileUpdateInfo? build() => null;

  void show(MobileUpdateInfo info) {
    state = info;
  }

  void clear() {
    state = null;
  }
}
