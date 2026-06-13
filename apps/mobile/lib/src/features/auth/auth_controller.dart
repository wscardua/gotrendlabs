import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_client.dart';
import '../../core/providers.dart';
import '../push/push_controller.dart';
import 'auth_models.dart';
import 'auth_repository.dart';
import 'biometric_auth.dart';

final authRepositoryProvider = Provider<AuthRepository>(
  (ref) => AuthRepository(ref.watch(apiClientProvider)),
);

final authControllerProvider = NotifierProvider<AuthController, AuthState>(
  AuthController.new,
);

final biometricPreferenceStoreProvider = Provider<BiometricPreferenceStore>(
  (ref) => SecureBiometricPreferenceStore(),
);

final biometricAuthenticatorProvider = Provider<BiometricAuthenticator>(
  (ref) => LocalBiometricAuthenticator(),
);

final biometricCapabilityProvider = FutureProvider<bool>((ref) {
  return ref.watch(biometricAuthenticatorProvider).isSupported();
});

final biometricPreferenceProvider = FutureProvider<bool>((ref) {
  return ref.watch(biometricPreferenceStoreProvider).readEnabled();
});

final rememberedSessionProvider = FutureProvider<bool>((ref) async {
  final token = await ref.watch(apiClientProvider).readStoredToken();
  return token?.isNotEmpty == true;
});

class AuthController extends Notifier<AuthState> {
  @override
  AuthState build() {
    Future.microtask(restore);
    return const AuthState(restoring: true);
  }

  Future<void> restore() async {
    await _restoreRememberedSession(forceLocalAuth: false);
  }

  Future<void> _restoreRememberedSession({required bool forceLocalAuth}) async {
    final api = ref.read(apiClientProvider);
    final repo = ref.read(authRepositoryProvider);
    final storedToken = await api.readStoredToken();
    if (!ref.mounted) {
      return;
    }
    if (storedToken == null || storedToken.isEmpty) {
      state = const AuthState();
      return;
    }
    final biometricEnabled = await ref
        .read(biometricPreferenceStoreProvider)
        .readEnabled();
    if (!ref.mounted) {
      return;
    }
    if (forceLocalAuth || biometricEnabled) {
      final supported = await ref
          .read(biometricAuthenticatorProvider)
          .isSupported();
      if (!ref.mounted) {
        return;
      }
      if (!supported) {
        state = state.copyWith(
          busy: false,
          sessionLocked: biometricEnabled,
          error:
              'Este aparelho não oferece biometria ou senha local compatível.',
        );
        return;
      }
      final unlocked = await _authenticateLocalDevice(
        'Desbloqueie sua sessão GoTrendLabs com biometria ou senha do aparelho.',
      );
      if (!ref.mounted) {
        return;
      }
      if (!unlocked) {
        state = const AuthState(sessionLocked: true);
        return;
      }
    }
    final currentStoredToken = await api.readStoredToken();
    if (!ref.mounted ||
        (!forceLocalAuth && state.busy) ||
        currentStoredToken != storedToken) {
      return;
    }
    api.activateToken(storedToken);
    try {
      final user = await repo.session();
      if (!ref.mounted || (!forceLocalAuth && state.busy)) {
        return;
      }
      state = AuthState(user: user);
      await ref.read(pushControllerProvider.notifier).syncAfterAuth();
    } catch (_) {
      if (!ref.mounted) {
        return;
      }
      await api.clearToken();
      await ref.read(biometricPreferenceStoreProvider).writeEnabled(false);
      ref.invalidate(biometricPreferenceProvider);
      ref.invalidate(rememberedSessionProvider);
      state = const AuthState();
    }
  }

  Future<void> login(
    String email,
    String password, {
    bool rememberSession = true,
    bool protectWithBiometrics = false,
  }) async {
    await _authenticate(
      () => ref
          .read(authRepositoryProvider)
          .login(email: email, password: password),
      rememberSession: rememberSession,
      protectWithBiometrics: protectWithBiometrics,
    );
  }

  Future<void> register(
    String name,
    String email,
    String password,
    bool acceptedTerms, {
    bool protectWithBiometrics = false,
  }) async {
    await _authenticate(
      () => ref
          .read(authRepositoryProvider)
          .register(
            displayName: name,
            email: email,
            password: password,
            termsAccepted: acceptedTerms,
          ),
      protectWithBiometrics: protectWithBiometrics,
    );
  }

  Future<void> requestPasswordReset(String email) async {
    state = state.copyWith(busy: true, clearError: true);
    try {
      await ref.read(authRepositoryProvider).requestPasswordReset(email);
      state = state.copyWith(busy: false);
    } catch (error) {
      state = state.copyWith(
        busy: false,
        error: ApiFailure.fromObject(error).message,
      );
    }
  }

  Future<void> logout() async {
    state = state.copyWith(busy: true, clearError: true);
    final api = ref.read(apiClientProvider);
    try {
      await ref.read(authRepositoryProvider).logout();
    } catch (_) {
      // Logout local continua mesmo se a sessão já tiver expirado no backend.
    }
    await api.clearToken();
    await ref.read(biometricPreferenceStoreProvider).writeEnabled(false);
    ref.invalidate(biometricPreferenceProvider);
    ref.invalidate(rememberedSessionProvider);
    state = const AuthState();
    _scheduleUserScopedDataInvalidation();
  }

  Future<void> unlockProtectedSession() async {
    if (state.isAuthenticated) {
      return;
    }
    state = state.copyWith(busy: true, clearError: true);
    await _restoreRememberedSession(forceLocalAuth: true);
  }

  Future<void> forgetProtectedSession() async {
    await ref.read(apiClientProvider).clearToken();
    await ref.read(biometricPreferenceStoreProvider).writeEnabled(false);
    ref.invalidate(biometricPreferenceProvider);
    ref.invalidate(rememberedSessionProvider);
    state = const AuthState();
    _scheduleUserScopedDataInvalidation();
  }

  Future<void> setBiometricProtection(bool enabled) async {
    state = state.copyWith(busy: true, clearError: true);
    final store = ref.read(biometricPreferenceStoreProvider);
    if (!enabled) {
      await store.writeEnabled(false);
      ref.invalidate(biometricPreferenceProvider);
      state = state.copyWith(busy: false);
      return;
    }
    final token = await ref.read(apiClientProvider).readStoredToken();
    if (token == null || token.isEmpty) {
      state = state.copyWith(
        busy: false,
        error: 'Entre com Lembrar login para proteger a sessão.',
      );
      return;
    }
    final supported = await ref
        .read(biometricAuthenticatorProvider)
        .isSupported();
    if (!supported) {
      state = state.copyWith(
        busy: false,
        error: 'Este aparelho não oferece biometria ou senha local compatível.',
      );
      return;
    }
    final unlocked = await _authenticateLocalDevice(
      'Confirme com biometria ou senha do aparelho para proteger sua sessão.',
    );
    if (!unlocked) {
      state = state.copyWith(
        busy: false,
        error: 'Não foi possível ativar a proteção local.',
      );
      return;
    }
    await store.writeEnabled(true);
    ref.invalidate(biometricPreferenceProvider);
    state = state.copyWith(busy: false);
  }

  Future<void> _authenticate(
    Future<AuthResult> Function() call, {
    bool rememberSession = true,
    bool protectWithBiometrics = false,
  }) async {
    state = state.copyWith(busy: true, clearError: true);
    final api = ref.read(apiClientProvider);
    try {
      final result = await call();
      await api.setToken(result.session.token, persist: rememberSession);
      await _setBiometricPreference(rememberSession && protectWithBiometrics);
      state = AuthState(user: result.user);
      await ref.read(pushControllerProvider.notifier).syncAfterAuth();
      _scheduleUserScopedDataInvalidation();
    } catch (error) {
      state = state.copyWith(
        busy: false,
        error: ApiFailure.fromObject(error).message,
      );
    }
  }

  Future<void> _setBiometricPreference(bool enabled) async {
    final store = ref.read(biometricPreferenceStoreProvider);
    if (!enabled) {
      await store.writeEnabled(false);
      ref.invalidate(biometricPreferenceProvider);
      ref.invalidate(rememberedSessionProvider);
      return;
    }
    final supported = await ref
        .read(biometricAuthenticatorProvider)
        .isSupported();
    await store.writeEnabled(supported);
    ref.invalidate(biometricPreferenceProvider);
    ref.invalidate(rememberedSessionProvider);
  }

  Future<bool> _authenticateLocalDevice(String reason) {
    return ref
        .read(biometricAuthenticatorProvider)
        .authenticate(reason: reason);
  }

  void _scheduleUserScopedDataInvalidation() {
    unawaited(Future<void>.microtask(_invalidateUserScopedData));
  }

  void _invalidateUserScopedData() {
    ref.invalidate(walletProvider);
    ref.invalidate(ledgerProvider);
    ref.invalidate(notificationsProvider);
    ref.invalidate(profileProvider);
    ref.invalidate(badgesProvider);
    ref.invalidate(badgeCatalogProvider);
    ref.invalidate(referralProvider);
    ref.invalidate(walletRechargeRequestsProvider);
  }
}

final profileProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  ref.watch(authControllerProvider);
  final auth = ref.read(authControllerProvider);
  if (!auth.isAuthenticated) {
    return <String, dynamic>{};
  }
  return ref.read(apiClientProvider).getMap('/users/me');
});

final notificationsProvider = FutureProvider<List<dynamic>>((ref) async {
  ref.watch(authControllerProvider);
  final auth = ref.read(authControllerProvider);
  if (!auth.isAuthenticated) {
    return <dynamic>[];
  }
  final json = await ref
      .read(apiClientProvider)
      .getMap('/users/me/notifications');
  return (json['notifications'] as List<dynamic>?) ?? <dynamic>[];
});

final badgesProvider = FutureProvider<List<dynamic>>((ref) async {
  ref.watch(authControllerProvider);
  final auth = ref.read(authControllerProvider);
  if (!auth.isAuthenticated) {
    return <dynamic>[];
  }
  return ref.read(apiClientProvider).getList('/users/me/badges', 'badges');
});

final badgeCatalogProvider = FutureProvider<List<dynamic>>((ref) async {
  ref.watch(authControllerProvider);
  return ref.read(apiClientProvider).getList('/badges', 'badges');
});

final referralProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  ref.watch(authControllerProvider);
  final auth = ref.read(authControllerProvider);
  if (!auth.isAuthenticated) {
    return <String, dynamic>{};
  }
  return ref.read(apiClientProvider).getMap('/users/me/referral');
});

final walletProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  ref.watch(authControllerProvider);
  final auth = ref.read(authControllerProvider);
  if (!auth.isAuthenticated) {
    return <String, dynamic>{};
  }
  return ref.read(apiClientProvider).getMap('/users/me/wallet');
});

final ledgerProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  ref.watch(authControllerProvider);
  final auth = ref.read(authControllerProvider);
  if (!auth.isAuthenticated) {
    return <String, dynamic>{};
  }
  return ref.read(apiClientProvider).getMap('/users/me/ledger');
});

final walletRechargeRequestsProvider = FutureProvider<Map<String, dynamic>>((
  ref,
) async {
  ref.watch(authControllerProvider);
  final auth = ref.read(authControllerProvider);
  if (!auth.isAuthenticated) {
    return <String, dynamic>{
      'requests': <dynamic>[],
      'available_gtl': 0,
      'min_balance_gtl': 100,
      'eligible': false,
    };
  }
  return ref
      .read(apiClientProvider)
      .getMap('/users/me/wallet/recharge-requests');
});
