import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gotrendlabs_mobile/src/core/api_client.dart';
import 'package:gotrendlabs_mobile/src/core/providers.dart';
import 'package:gotrendlabs_mobile/src/features/auth/auth_controller.dart';
import 'package:gotrendlabs_mobile/src/features/auth/auth_models.dart';
import 'package:gotrendlabs_mobile/src/features/auth/auth_repository.dart';
import 'package:gotrendlabs_mobile/src/features/auth/biometric_auth.dart';
import 'package:gotrendlabs_mobile/src/features/auth/login_sheet.dart';
import 'package:gotrendlabs_mobile/src/features/profile/profile_screen.dart';
import 'package:gotrendlabs_mobile/src/features/push/push_controller.dart';
import 'package:gotrendlabs_mobile/src/theme.dart';

void main() {
  test(
    'restore cancel keeps stored token locked and skips session call',
    () async {
      final tokenStore = MemoryTokenStore()..token = 'stored-token';
      final api = ApiClient(tokenStore: tokenStore);
      final repo = _FakeAuthRepository();
      final container = ProviderContainer(
        overrides: [
          apiClientProvider.overrideWithValue(api),
          authRepositoryProvider.overrideWithValue(repo),
          biometricPreferenceStoreProvider.overrideWithValue(
            MemoryBiometricPreferenceStore(enabled: true),
          ),
          biometricAuthenticatorProvider.overrideWithValue(
            const _FakeBiometricAuthenticator(
              supported: true,
              authenticateResult: false,
            ),
          ),
        ],
      );
      addTearDown(container.dispose);

      container.read(authControllerProvider);
      await Future<void>.delayed(Duration.zero);

      expect(container.read(authControllerProvider).sessionLocked, isTrue);
      expect(repo.sessionCalls, 0);
      expect(await tokenStore.readToken(), 'stored-token');
    },
  );

  test(
    'unlock protected session activates stored token after local auth',
    () async {
      final tokenStore = MemoryTokenStore()..token = 'stored-token';
      final api = ApiClient(tokenStore: tokenStore);
      final repo = _FakeAuthRepository();
      final container = ProviderContainer(
        overrides: [
          apiClientProvider.overrideWithValue(api),
          authRepositoryProvider.overrideWithValue(repo),
          biometricPreferenceStoreProvider.overrideWithValue(
            MemoryBiometricPreferenceStore(enabled: true),
          ),
          biometricAuthenticatorProvider.overrideWithValue(
            const _FakeBiometricAuthenticator(
              supported: true,
              authenticateResult: true,
            ),
          ),
          pushTokenProvider.overrideWithValue(const NoopPushTokenProvider()),
        ],
      );
      addTearDown(container.dispose);

      container.read(authControllerProvider);
      await Future<void>.delayed(Duration.zero);

      final state = container.read(authControllerProvider);
      expect(state.isAuthenticated, isTrue);
      expect(state.sessionLocked, isFalse);
      expect(repo.sessionCalls, 1);
    },
  );

  testWidgets('LoginSheet offers biometric protection for remembered login', (
    tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authControllerProvider.overrideWith(
            _UnauthenticatedAuthController.new,
          ),
          biometricCapabilityProvider.overrideWith((ref) async => true),
        ],
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: const Scaffold(body: LoginSheet()),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Proteger sessão com biometria'), findsOneWidget);
    final biometricSwitch = tester.widget<SwitchListTile>(
      find.widgetWithText(SwitchListTile, 'Proteger sessão com biometria'),
    );
    expect(biometricSwitch.value, isTrue);
    expect(
      find.text('Na próxima abertura, use biometria ou senha do aparelho.'),
      findsOneWidget,
    );
  });

  testWidgets('LoginSheet offers biometric protection for registration', (
    tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authControllerProvider.overrideWith(
            _UnauthenticatedAuthController.new,
          ),
          biometricCapabilityProvider.overrideWith((ref) async => true),
        ],
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: const Scaffold(body: LoginSheet()),
        ),
      ),
    );

    await tester.pumpAndSettle();
    await tester.tap(find.text('Cadastro'));
    await tester.pumpAndSettle();

    expect(find.text('Proteger sessão com biometria'), findsOneWidget);
    final biometricSwitch = tester.widget<SwitchListTile>(
      find.widgetWithText(SwitchListTile, 'Proteger sessão com biometria'),
    );
    expect(biometricSwitch.value, isTrue);
  });

  testWidgets('LoginSheet shows biometric unlock for protected sessions', (
    tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authControllerProvider.overrideWith(
            _UnauthenticatedAuthController.new,
          ),
          biometricCapabilityProvider.overrideWith((ref) async => true),
          biometricPreferenceProvider.overrideWith((ref) async => true),
          rememberedSessionProvider.overrideWith((ref) async => true),
        ],
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: const Scaffold(body: LoginSheet()),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Entrar com biometria'), findsOneWidget);
  });

  testWidgets('LoginSheet hides biometric unlock when preference is disabled', (
    tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authControllerProvider.overrideWith(
            _UnauthenticatedAuthController.new,
          ),
          biometricCapabilityProvider.overrideWith((ref) async => true),
          biometricPreferenceProvider.overrideWith((ref) async => false),
          rememberedSessionProvider.overrideWith((ref) async => true),
        ],
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: const Scaffold(body: LoginSheet()),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Entrar com biometria'), findsNothing);
  });

  test(
    'unlock protected session does not backfill biometric preference',
    () async {
      final store = MemoryBiometricPreferenceStore();
      final tokenStore = MemoryTokenStore()..token = 'stored-token';
      final repo = _FakeAuthRepository();
      final container = ProviderContainer(
        overrides: [
          apiClientProvider.overrideWithValue(
            ApiClient(tokenStore: tokenStore),
          ),
          authRepositoryProvider.overrideWithValue(repo),
          biometricPreferenceStoreProvider.overrideWithValue(store),
          biometricAuthenticatorProvider.overrideWithValue(
            const _FakeBiometricAuthenticator(
              supported: true,
              authenticateResult: true,
            ),
          ),
          pushTokenProvider.overrideWithValue(const NoopPushTokenProvider()),
        ],
      );
      addTearDown(container.dispose);

      await container
          .read(authControllerProvider.notifier)
          .unlockProtectedSession();

      expect(await store.readEnabled(), isFalse);
      expect(container.read(authControllerProvider).isAuthenticated, isTrue);
      expect(repo.sessionCalls, greaterThanOrEqualTo(1));
    },
  );

  test(
    'register can enable biometric protection for remembered session',
    () async {
      final store = MemoryBiometricPreferenceStore();
      final container = ProviderContainer(
        overrides: [
          apiClientProvider.overrideWithValue(
            ApiClient(tokenStore: MemoryTokenStore()),
          ),
          authRepositoryProvider.overrideWithValue(_FakeAuthRepository()),
          biometricPreferenceStoreProvider.overrideWithValue(store),
          biometricAuthenticatorProvider.overrideWithValue(
            const _FakeBiometricAuthenticator(
              supported: true,
              authenticateResult: true,
            ),
          ),
          pushTokenProvider.overrideWithValue(const NoopPushTokenProvider()),
        ],
      );
      addTearDown(container.dispose);

      await container
          .read(authControllerProvider.notifier)
          .register(
            'Tester',
            'tester@example.com',
            'password',
            true,
            protectWithBiometrics: true,
          );

      expect(await store.readEnabled(), isTrue);
      expect(container.read(authControllerProvider).isAuthenticated, isTrue);
    },
  );

  testWidgets('LoginSheet shows protected session actions', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authControllerProvider.overrideWith(_LockedAuthController.new),
          biometricCapabilityProvider.overrideWith((ref) async => true),
        ],
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: const Scaffold(body: LoginSheet()),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Sessão protegida'), findsOneWidget);
    expect(find.text('Desbloquear sessão'), findsOneWidget);
    expect(find.text('Sair deste dispositivo'), findsOneWidget);
    expect(find.text('Email'), findsNothing);
  });

  testWidgets('ProfileScreen exposes biometric protection settings', (
    tester,
  ) async {
    final tokenStore = MemoryTokenStore()..token = 'stored-token';
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          apiClientProvider.overrideWithValue(
            ApiClient(tokenStore: tokenStore),
          ),
          authControllerProvider.overrideWith(_AuthenticatedAuthController.new),
          profileProvider.overrideWith(
            (ref) async => {
              'user': {'display_name': 'Tester', 'handle': 'tester'},
              'bio': '',
              'strong_category': '',
              'reputation': {'reputation_score': 10, 'ranking_position': 1},
            },
          ),
          badgesProvider.overrideWith((ref) async => <dynamic>[]),
          biometricCapabilityProvider.overrideWith((ref) async => true),
          biometricPreferenceProvider.overrideWith((ref) async => false),
          rememberedSessionProvider.overrideWith((ref) async => true),
        ],
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: const ProfileScreen(),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Proteção local'), findsOneWidget);
    expect(
      find.text('Na próxima abertura, use biometria ou senha do aparelho.'),
      findsOneWidget,
    );
  });
}

class _FakeAuthRepository extends AuthRepository {
  _FakeAuthRepository() : super(ApiClient(tokenStore: MemoryTokenStore()));

  int sessionCalls = 0;

  @override
  Future<AuthResult> register({
    required String displayName,
    required String email,
    required String password,
    required bool termsAccepted,
  }) async {
    return const AuthResult(
      user: GtlUser(
        id: 7,
        handle: 'tester',
        email: 'tester@example.com',
        displayName: 'Tester',
        emailConfirmed: true,
        isStaff: false,
      ),
      session: AuthSession(
        token: 'registered-token',
        expiresAt: '2026-06-14T00:00:00Z',
      ),
    );
  }

  @override
  Future<GtlUser> session() async {
    sessionCalls += 1;
    return const GtlUser(
      id: 7,
      handle: 'tester',
      email: 'tester@example.com',
      displayName: 'Tester',
      emailConfirmed: true,
      isStaff: false,
    );
  }
}

class _FakeBiometricAuthenticator implements BiometricAuthenticator {
  const _FakeBiometricAuthenticator({
    required this.supported,
    required this.authenticateResult,
  });

  final bool supported;
  final bool authenticateResult;

  @override
  Future<bool> isSupported() async => supported;

  @override
  Future<bool> authenticate({required String reason}) async {
    return authenticateResult;
  }
}

class _UnauthenticatedAuthController extends AuthController {
  @override
  AuthState build() => const AuthState();
}

class _AuthenticatedAuthController extends AuthController {
  @override
  AuthState build() {
    return const AuthState(
      user: GtlUser(
        id: 7,
        handle: 'tester',
        email: 'tester@example.com',
        displayName: 'Tester',
        emailConfirmed: true,
        isStaff: false,
      ),
    );
  }
}

class _LockedAuthController extends AuthController {
  @override
  AuthState build() => const AuthState(sessionLocked: true);

  @override
  Future<void> unlockProtectedSession() async {}

  @override
  Future<void> forgetProtectedSession() async {}
}
