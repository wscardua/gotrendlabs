import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gotrendlabs_mobile/src/features/alerts/alerts_screen.dart';
import 'package:gotrendlabs_mobile/src/features/auth/auth_controller.dart';
import 'package:gotrendlabs_mobile/src/features/auth/auth_models.dart';
import 'package:gotrendlabs_mobile/src/features/profile/profile_screen.dart';
import 'package:gotrendlabs_mobile/src/theme.dart';

void main() {
  testWidgets('Profile omits push controls', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authControllerProvider.overrideWith(_AuthenticatedAuthController.new),
          profileProvider.overrideWith((ref) async => _profilePayload()),
          badgesProvider.overrideWith((ref) async => []),
        ],
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: const ProfileScreen(),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Push mobile'), findsNothing);
    expect(find.text('Push preparado'), findsNothing);
    expect(find.text('Atualizar push'), findsNothing);
  });

  testWidgets('AlertsScreen omits push controls', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authControllerProvider.overrideWith(_AuthenticatedAuthController.new),
          notificationsProvider.overrideWith((ref) async => []),
        ],
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: const AlertsScreen(),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Alertas'), findsOneWidget);
    expect(find.text('Push preparado'), findsNothing);
    expect(find.text('Atualizar push'), findsNothing);
  });
}

Map<String, dynamic> _profilePayload() {
  return {
    'user': {'display_name': 'Tester', 'handle': 'tester'},
    'reputation': {
      'reputation_score': 0,
      'ranking_position': 0,
      'resolved_predictions_count': 0,
      'accuracy_indicator': '0%',
      'streak': 0,
      'strong_category': 'Geral',
    },
  };
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
