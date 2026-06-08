import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_client.dart';
import '../../core/environment.dart';
import '../../core/providers.dart';
import 'push_models.dart';
import 'push_repository.dart';

abstract class PushTokenProvider {
  Future<PushTokenSnapshot> currentToken();
}

class NoopPushTokenProvider implements PushTokenProvider {
  const NoopPushTokenProvider();

  @override
  Future<PushTokenSnapshot> currentToken() async {
    return const PushTokenSnapshot.unavailable('firebase_not_configured');
  }
}

class FakePushTokenProvider implements PushTokenProvider {
  const FakePushTokenProvider({
    required this.token,
    this.platform = 'android',
    this.deviceLabel = 'Emulador local',
  });

  final String token;
  final String platform;
  final String deviceLabel;

  @override
  Future<PushTokenSnapshot> currentToken() async {
    final normalizedToken = token.trim();
    final normalizedPlatform = platform.trim().toLowerCase();
    if (normalizedToken.isEmpty ||
        (normalizedPlatform != 'android' && normalizedPlatform != 'ios')) {
      return const PushTokenSnapshot.unavailable('fake_token_invalid');
    }
    return PushTokenSnapshot.available(
      token: normalizedToken,
      platform: normalizedPlatform,
      deviceLabel: deviceLabel.trim().isEmpty ? 'Emulador local' : deviceLabel,
    );
  }
}

final pushRepositoryProvider = Provider<PushRepository>(
  (ref) => PushRepository(ref.watch(apiClientProvider)),
);

final pushTokenProvider = Provider<PushTokenProvider>(
  (ref) {
    if (AppEnvironment.pushFakeToken.trim().isNotEmpty) {
      return const FakePushTokenProvider(
        token: AppEnvironment.pushFakeToken,
        platform: AppEnvironment.pushFakePlatform,
        deviceLabel: AppEnvironment.pushFakeDeviceLabel,
      );
    }
    return const NoopPushTokenProvider();
  },
);

final pushControllerProvider = NotifierProvider<PushController, PushState>(
  PushController.new,
);

class PushController extends Notifier<PushState> {
  @override
  PushState build() {
    return const PushState();
  }

  Future<void> load() async {
    state = state.copyWith(status: 'loading', error: '');
    try {
      final repo = ref.read(pushRepositoryProvider);
      final results = await Future.wait([repo.devices(), repo.preferences()]);
      state = PushState(
        status: 'loaded',
        devices: results[0] as List<PushDevice>,
        preferences: results[1] as PushPreferenceSet,
      );
    } catch (error) {
      state = state.copyWith(
        status: 'error',
        error: ApiFailure.fromObject(error).message,
      );
    }
  }

  Future<void> syncAfterAuth() async {
    final tokenSnapshot = await ref.read(pushTokenProvider).currentToken();
    if (!tokenSnapshot.isAvailable) {
      state = state.copyWith(
        status: 'noop',
        reason: tokenSnapshot.reason,
        error: '',
      );
      return;
    }
    try {
      final repo = ref.read(pushRepositoryProvider);
      final preferences = await repo.preferences();
      if (!preferences.globalEnabled) {
        state = state.copyWith(
          status: 'disabled',
          reason: 'user_preference',
          preferences: preferences,
          error: '',
        );
        return;
      }
      final device = await repo.registerDevice(tokenSnapshot);
      state = state.copyWith(
        status: 'registered',
        reason: '',
        devices: [device],
        preferences: preferences,
        error: '',
      );
    } catch (error) {
      state = state.copyWith(
        status: 'error',
        error: ApiFailure.fromObject(error).message,
      );
    }
  }

  Future<void> revokeDevice(int deviceId) async {
    try {
      final repo = ref.read(pushRepositoryProvider);
      await repo.revokeDevice(deviceId);
      await load();
    } catch (error) {
      state = state.copyWith(
        status: 'error',
        error: ApiFailure.fromObject(error).message,
      );
    }
  }

  Future<void> setGlobalEnabled(bool enabled) async {
    try {
      final preferences = await ref
          .read(pushRepositoryProvider)
          .setGlobalEnabled(enabled);
      state = state.copyWith(preferences: preferences, error: '');
    } catch (error) {
      state = state.copyWith(
        status: 'error',
        error: ApiFailure.fromObject(error).message,
      );
    }
  }
}
