import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_client.dart';
import '../../core/providers.dart';
import '../push/push_controller.dart';
import 'auth_models.dart';
import 'auth_repository.dart';

final authRepositoryProvider = Provider<AuthRepository>(
  (ref) => AuthRepository(ref.watch(apiClientProvider)),
);

final authControllerProvider = NotifierProvider<AuthController, AuthState>(
  AuthController.new,
);

class AuthController extends Notifier<AuthState> {
  @override
  AuthState build() {
    Future.microtask(restore);
    return const AuthState(restoring: true);
  }

  Future<void> restore() async {
    final api = ref.read(apiClientProvider);
    final repo = ref.read(authRepositoryProvider);
    await api.restoreToken();
    try {
      final user = await repo.session();
      state = AuthState(user: user);
      await ref.read(pushControllerProvider.notifier).syncAfterAuth();
    } catch (_) {
      await api.clearToken();
      state = const AuthState();
    }
  }

  Future<void> login(String email, String password) async {
    await _authenticate(
      () => ref
          .read(authRepositoryProvider)
          .login(email: email, password: password),
    );
  }

  Future<void> register(
    String name,
    String email,
    String password,
    bool acceptedTerms,
  ) async {
    await _authenticate(
      () => ref
          .read(authRepositoryProvider)
          .register(
            displayName: name,
            email: email,
            password: password,
            termsAccepted: acceptedTerms,
          ),
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
    state = const AuthState();
    _invalidateUserScopedData();
  }

  Future<void> _authenticate(Future<AuthResult> Function() call) async {
    state = state.copyWith(busy: true, clearError: true);
    final api = ref.read(apiClientProvider);
    try {
      final result = await call();
      await api.setToken(result.session.token);
      state = AuthState(user: result.user);
      await ref.read(pushControllerProvider.notifier).syncAfterAuth();
      _invalidateUserScopedData();
    } catch (error) {
      state = state.copyWith(
        busy: false,
        error: ApiFailure.fromObject(error).message,
      );
    }
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
