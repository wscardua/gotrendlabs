import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gotrendlabs_mobile/src/features/anti_abuse/anti_abuse_repository.dart';
import 'package:gotrendlabs_mobile/src/features/auth/auth_controller.dart';
import 'package:gotrendlabs_mobile/src/features/auth/auth_models.dart';
import 'package:gotrendlabs_mobile/src/features/support/contribution_sheets.dart';
import 'package:gotrendlabs_mobile/src/features/support/support_providers.dart';
import 'package:gotrendlabs_mobile/src/theme.dart';

void main() {
  testWidgets('Feedback sheet places challenge after description', (
    tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: _guestOverrides,
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: Scaffold(
            body: Builder(
              builder: (context) => FilledButton(
                onPressed: () => showFeedbackSheet(context),
                child: const Text('Abrir feedback'),
              ),
            ),
          ),
        ),
      ),
    );

    await tester.tap(find.text('Abrir feedback'));
    await tester.pumpAndSettle();

    expect(find.text('Suporte e feedback'), findsOneWidget);
    expect(find.textContaining('FastAPI'), findsNothing);
    expect(find.textContaining('Admin Ops'), findsNothing);
    expect(
      tester.getTopLeft(find.text('Descrição')).dy,
      lessThan(tester.getTopLeft(find.text('Verificação rápida')).dy),
    );
    expect(find.text(_challenge.prompt), findsOneWidget);
  });

  testWidgets('Suggestion sheet places challenge after context', (
    tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: _guestOverrides,
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: Scaffold(
            body: Builder(
              builder: (context) => FilledButton(
                onPressed: () => showSuggestionSheet(context),
                child: const Text('Abrir sugestão'),
              ),
            ),
          ),
        ),
      ),
    );

    await tester.tap(find.text('Abrir sugestão'));
    await tester.pumpAndSettle();

    expect(find.text('Sugerir mercado'), findsOneWidget);
    expect(find.textContaining('FastAPI'), findsNothing);
    expect(find.textContaining('Admin Ops'), findsNothing);
    expect(
      tester.getTopLeft(find.text('Contexto')).dy,
      lessThan(tester.getTopLeft(find.text('Verificação rápida')).dy),
    );
    expect(find.text(_challenge.prompt), findsOneWidget);
  });
}

const _challenge = AntiAbuseChallenge(
  prompt: 'Quanto é 2 + 3?',
  token: 'challenge-token',
  expiresAt: '2026-06-18T12:00:00Z',
);

class _UnauthenticatedAuthController extends AuthController {
  @override
  AuthState build() {
    return const AuthState();
  }
}

final _guestOverrides = [
  authControllerProvider.overrideWith(_UnauthenticatedAuthController.new),
  antiAbuseChallengeProvider.overrideWith((ref) async => _challenge),
  taxonomyProvider.overrideWith(
    (ref) async => [
      {'name': 'Tecnologia', 'is_blocked': false},
    ],
  ),
];
