import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gotrendlabs_mobile/src/features/alerts/alerts_screen.dart';
import 'package:gotrendlabs_mobile/src/features/auth/auth_controller.dart';
import 'package:gotrendlabs_mobile/src/features/auth/auth_models.dart';
import 'package:gotrendlabs_mobile/src/theme.dart';

void main() {
  testWidgets('comment notification opens market community route', (
    tester,
  ) async {
    final router = GoRouter(
      routes: [
        GoRoute(path: '/', builder: (context, state) => const AlertsScreen()),
        GoRoute(
          path: '/markets/:slug',
          builder: (context, state) => Text(
            '${state.pathParameters['slug']} ${state.uri.queryParameters['tab']}',
          ),
        ),
      ],
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authControllerProvider.overrideWith(_AuthenticatedAuthController.new),
          notificationsProvider.overrideWith((ref) async {
            return [
              {
                'event_type': 'market_comment',
                'title': 'Novo comentário',
                'body': 'Alguém comentou em um mercado seu.',
                'market_slug': 'royal-ascot-2026',
              },
            ];
          }),
        ],
        child: MaterialApp.router(
          theme: buildGoTrendLabsTheme(),
          routerConfig: router,
        ),
      ),
    );

    await tester.pumpAndSettle();
    await tester.tap(find.text('Novo comentário'));
    await tester.pumpAndSettle();

    expect(find.text('royal-ascot-2026 community'), findsOneWidget);
  });
}

class _AuthenticatedAuthController extends AuthController {
  @override
  AuthState build() {
    return const AuthState(
      user: GtlUser(
        id: 1,
        handle: 'tester',
        email: 'tester@example.com',
        displayName: 'Tester',
        emailConfirmed: true,
        isStaff: false,
      ),
    );
  }
}
