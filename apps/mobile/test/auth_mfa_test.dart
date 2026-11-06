import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
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
import 'package:gotrendlabs_mobile/src/features/push/push_controller.dart';

void main() {
  cancellationAndUiTests();
  for (final enrollment in [false, true]) {
    testWidgets(
      'admin MFA enrollment=$enrollment never stores session before verification',
      (tester) async {
        final store = MemoryTokenStore();
        final dio = Dio(BaseOptions(baseUrl: 'http://api.test'));
        var invalid = true;
        var recovery = false;
        dio.httpClientAdapter = _Adapter((options) {
          if (options.path == '/auth/login') {
            return {
              'mfa_required': true,
              'challenge_token': 'challenge-token',
              'enrollment_required': enrollment,
              'expires_at': '2026-11-06T12:00:00Z',
            };
          }
          if (options.path == '/auth/mfa/enroll') {
            expect(options.data['challenge_token'], 'challenge-token');
            return {'manual_key': 'TESTMANUALKEY'};
          }
          if (options.path == '/auth/mfa/verify') {
            expect(options.data['challenge_token'], 'challenge-token');
            expect(options.data['code'], recovery ? '' : '123456');
            expect(options.data['recovery_code'], recovery ? 'RECOVERY' : '');
            if (invalid) return null;
            return {
              'user': {'id': 1, 'is_staff': true},
              'session': {
                'token': 'verified-token',
                'expires_at': '2026-12-01',
              },
              'recovery_codes': enrollment ? ['SAVE-THIS-CODE'] : <String>[],
            };
          }
          return {};
        });
        final container = ProviderContainer(
          overrides: [
            apiClientProvider.overrideWithValue(
              ApiClient(dio: dio, tokenStore: store),
            ),
            biometricPreferenceStoreProvider.overrideWithValue(
              MemoryBiometricPreferenceStore(),
            ),
            biometricCapabilityProvider.overrideWith((ref) async => false),
            pushTokenProvider.overrideWithValue(const NoopPushTokenProvider()),
          ],
        );
        addTearDown(container.dispose);
        container.read(authControllerProvider);
        await tester.pump();
        final controller = container.read(authControllerProvider.notifier);
        await tester.runAsync(
          () => controller.login(
            'admin@example.test',
            'password',
            rememberSession: enrollment,
          ),
        );
        expect(container.read(authControllerProvider).isAuthenticated, isFalse);
        expect(store.token, isNull);
        await tester.pumpWidget(
          UncontrolledProviderScope(
            container: container,
            child: const MaterialApp(home: Scaffold(body: LoginSheet())),
          ),
        );
        await tester.pumpAndSettle();
        expect(find.text('Verificação em duas etapas'), findsOneWidget);
        if (enrollment) expect(find.text('TESTMANUALKEY'), findsOneWidget);
        await tester.runAsync(() => controller.verifyMfa('123456'));
        await tester.pumpAndSettle();
        expect(container.read(authControllerProvider).isAuthenticated, isFalse);
        expect(store.token, isNull);
        expect(find.text('Código inválido ou expirado.'), findsOneWidget);
        invalid = false;
        recovery = !enrollment;
        await tester.runAsync(
          () => controller.verifyMfa(
            recovery ? 'RECOVERY' : '123456',
            recovery: recovery,
          ),
        );
        await tester.pumpAndSettle();
        expect(container.read(authControllerProvider).isAuthenticated, isTrue);
        expect(store.token, enrollment ? 'verified-token' : null);
        if (enrollment) {
          expect(find.text('SAVE-THIS-CODE'), findsOneWidget);
          controller.acknowledgeRecoveryCodes();
          expect(container.read(authControllerProvider).recoveryCodes, isEmpty);
        }
      },
    );
  }
}

class _Adapter implements HttpClientAdapter {
  _Adapter(this.handler);
  final Object? Function(RequestOptions) handler;
  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    final result = handler(options);
    return ResponseBody.fromString(
      jsonEncode(result ?? {'detail': 'Código inválido ou expirado.'}),
      result == null ? 401 : 200,
      headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      },
    );
  }

  @override
  void close({bool force = false}) {}
}

const _challenge = MfaChallenge(
  token: 'temporary-challenge',
  enrollmentRequired: false,
);
const _success = AuthResult(
  user: GtlUser(
    id: 1,
    handle: 'admin',
    email: 'admin@example.test',
    displayName: 'Admin',
    emailConfirmed: true,
    isStaff: true,
  ),
  session: AuthSession(token: 'verified-token', expiresAt: '2026-12-01'),
);

class _ControlledRepository extends AuthRepository {
  _ControlledRepository() : super(ApiClient(tokenStore: MemoryTokenStore()));
  final verification = Completer<AuthResult>();
  String? submittedCode;
  bool? submittedRecovery;
  @override
  Future<AuthOutcome> login({
    required String email,
    required String password,
  }) async => _challenge;
  @override
  Future<AuthResult> verifyMfa(
    String token,
    String code, {
    required bool recovery,
  }) {
    submittedCode = code;
    submittedRecovery = recovery;
    return verification.future;
  }
}

void cancellationAndUiTests() {
  test(
    'cancel discards pending verification and never activates its token',
    () async {
      final store = MemoryTokenStore();
      final repo = _ControlledRepository();
      final container = ProviderContainer(
        overrides: [
          apiClientProvider.overrideWithValue(ApiClient(tokenStore: store)),
          authRepositoryProvider.overrideWithValue(repo),
        ],
      );
      addTearDown(container.dispose);
      container.read(authControllerProvider);
      await Future<void>.delayed(Duration.zero);
      final controller = container.read(authControllerProvider.notifier);
      await controller.login('admin@example.test', 'password');
      final pending = controller.verifyMfa('123456');
      controller.cancelMfa();
      repo.verification.complete(_success);
      await pending;
      expect(container.read(authControllerProvider).challenge, isNull);
      expect(container.read(authControllerProvider).isAuthenticated, isFalse);
      expect(store.token, isNull);
      expect(
        container.read(apiClientProvider).readStoredToken(),
        completion(isNull),
      );
    },
  );

  testWidgets(
    'MFA form validates empty code, submits recovery, and can restart expired login',
    (tester) async {
      final repo = _ControlledRepository();
      final container = ProviderContainer(
        overrides: [
          apiClientProvider.overrideWithValue(
            ApiClient(tokenStore: MemoryTokenStore()),
          ),
          authRepositoryProvider.overrideWithValue(repo),
          biometricCapabilityProvider.overrideWith((ref) async => false),
        ],
      );
      addTearDown(container.dispose);
      container.read(authControllerProvider);
      await tester.pump();
      final controller = container.read(authControllerProvider.notifier);
      await controller.login('admin@example.test', 'password');
      await tester.pumpWidget(
        UncontrolledProviderScope(
          container: container,
          child: const MaterialApp(home: Scaffold(body: LoginSheet())),
        ),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.text('Confirmar e entrar'));
      await tester.pump();
      expect(find.text('Informe o código para continuar.'), findsOneWidget);
      await tester.tap(find.text('Usar código de recuperação'));
      await tester.pump();
      await tester.enterText(find.byType(TextField), 'RECOVERY');
      await tester.tap(find.text('Confirmar e entrar'));
      await tester.pump();
      expect(repo.submittedCode, 'RECOVERY');
      expect(repo.submittedRecovery, isTrue);
      repo.verification.completeError(
        ApiFailure(
          'unauthenticated',
          'Desafio MFA inválido, expirado ou já utilizado.',
        ),
      );
      await tester.pumpAndSettle();
      expect(
        find.text('Desafio MFA inválido, expirado ou já utilizado.'),
        findsOneWidget,
      );
      expect(container.read(authControllerProvider).isAuthenticated, isFalse);
      await tester.tap(find.text('Voltar ao login'));
      await tester.pumpAndSettle();
      expect(container.read(authControllerProvider).challenge, isNull);
      expect(find.text('Verificação em duas etapas'), findsNothing);
      expect(find.text('Senha'), findsOneWidget);
    },
  );

  testWidgets('dismissing login sheet clears the challenge', (tester) async {
    final repo = _ControlledRepository();
    final container = ProviderContainer(
      overrides: [
        apiClientProvider.overrideWithValue(
          ApiClient(tokenStore: MemoryTokenStore()),
        ),
        authRepositoryProvider.overrideWithValue(repo),
        biometricCapabilityProvider.overrideWith((ref) async => false),
      ],
    );
    addTearDown(container.dispose);
    container.read(authControllerProvider);
    await tester.pump();
    await container
        .read(authControllerProvider.notifier)
        .login('admin@example.test', 'password');
    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: MaterialApp(
          home: Scaffold(
            body: Builder(
              builder: (context) => TextButton(
                onPressed: () => showLoginSheet(context),
                child: const Text('Open'),
              ),
            ),
          ),
        ),
      ),
    );
    await tester.tap(find.text('Open'));
    await tester.pumpAndSettle();
    expect(find.text('Verificação em duas etapas'), findsOneWidget);
    Navigator.of(tester.element(find.text('Verificação em duas etapas'))).pop();
    await tester.pumpAndSettle();
    expect(container.read(authControllerProvider).challenge, isNull);
  });
}
