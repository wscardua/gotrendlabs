import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gotrendlabs_mobile/src/core/api_client.dart';
import 'package:gotrendlabs_mobile/src/features/push/push_controller.dart';
import 'package:gotrendlabs_mobile/src/features/push/push_models.dart';
import 'package:gotrendlabs_mobile/src/features/push/push_repository.dart';

void main() {
  test('noop provider does not register a device', () async {
    final repo = _FakePushRepository();
    final container = ProviderContainer(
      overrides: [
        pushRepositoryProvider.overrideWithValue(repo),
        pushTokenProvider.overrideWithValue(const NoopPushTokenProvider()),
      ],
    );
    addTearDown(container.dispose);

    await container.read(pushControllerProvider.notifier).syncAfterAuth();

    expect(repo.registerCalls, 0);
    expect(container.read(pushControllerProvider).status, 'noop');
  });

  test('available provider registers after authentication', () async {
    final repo = _FakePushRepository();
    final container = ProviderContainer(
      overrides: [
        pushRepositoryProvider.overrideWithValue(repo),
        pushTokenProvider.overrideWithValue(
          const _FakePushTokenProvider(
            PushTokenSnapshot.available(
              token: 'fcm-token-123',
              platform: 'android',
            ),
          ),
        ),
      ],
    );
    addTearDown(container.dispose);

    await container.read(pushControllerProvider.notifier).syncAfterAuth();

    expect(repo.registerCalls, 1);
    expect(container.read(pushControllerProvider).status, 'registered');
  });

  test('fake provider exposes a local token for emulator testing', () async {
    final snapshot = await const FakePushTokenProvider(
      token: ' fcm-local-emulator-001 ',
      platform: 'android',
      deviceLabel: 'Android emulator',
    ).currentToken();

    expect(snapshot.isAvailable, isTrue);
    expect(snapshot.token, 'fcm-local-emulator-001');
    expect(snapshot.platform, 'android');
    expect(snapshot.deviceLabel, 'Android emulator');
  });

  test('revokeDevice only runs on explicit action', () async {
    final repo = _FakePushRepository();
    final container = ProviderContainer(
      overrides: [pushRepositoryProvider.overrideWithValue(repo)],
    );
    addTearDown(container.dispose);

    expect(repo.revokeCalls, 0);

    await container.read(pushControllerProvider.notifier).revokeDevice(10);

    expect(repo.revokeCalls, 1);
  });
}

class _FakePushTokenProvider implements PushTokenProvider {
  const _FakePushTokenProvider(this.snapshot);

  final PushTokenSnapshot snapshot;

  @override
  Future<PushTokenSnapshot> currentToken() async => snapshot;
}

class _FakePushRepository extends PushRepository {
  _FakePushRepository() : super(ApiClient(tokenStore: MemoryTokenStore()));

  int registerCalls = 0;
  int revokeCalls = 0;

  @override
  Future<List<PushDevice>> devices() async => const [];

  @override
  Future<PushDevice> registerDevice(PushTokenSnapshot snapshot) async {
    registerCalls += 1;
    return const PushDevice(
      id: 10,
      provider: 'fcm',
      platform: 'android',
      isActive: true,
      pushEnabled: true,
    );
  }

  @override
  Future<PushDevice> revokeDevice(int deviceId) async {
    revokeCalls += 1;
    return const PushDevice(
      id: 10,
      provider: 'fcm',
      platform: 'android',
      isActive: false,
      pushEnabled: false,
      disabledReason: 'user_revoked',
    );
  }

  @override
  Future<PushPreferenceSet> preferences() async {
    return const PushPreferenceSet(globalEnabled: true, preferences: []);
  }
}
