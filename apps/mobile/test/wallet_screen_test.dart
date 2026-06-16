import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gotrendlabs_mobile/src/features/auth/auth_controller.dart';
import 'package:gotrendlabs_mobile/src/features/auth/auth_models.dart';
import 'package:gotrendlabs_mobile/src/features/wallet/wallet_screen.dart';
import 'package:gotrendlabs_mobile/src/theme.dart';

void main() {
  testWidgets(
    'Wallet prioritizes available and locked balances over recharge',
    (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            authControllerProvider.overrideWith(
              _AuthenticatedAuthController.new,
            ),
            ledgerProvider.overrideWith((ref) async {
              return {
                'wallet': {
                  'available_gtl': 1700,
                  'locked_gtl': 300,
                  'total_earned_gtl': 0,
                },
                'entries': <dynamic>[],
              };
            }),
            walletRechargeRequestsProvider.overrideWith((ref) async {
              return {
                'requests': <dynamic>[],
                'available_gtl': 1700,
                'min_balance_gtl': 100,
                'eligible': false,
              };
            }),
          ],
          child: MaterialApp(
            theme: buildGoTrendLabsTheme(),
            home: const WalletScreen(),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('Sua carteira'), findsOneWidget);
      expect(find.text('DISPONÍVEL'), findsOneWidget);
      expect(find.text('BLOQUEADO'), findsOneWidget);
      expect(find.text('1700 GT₵'), findsWidgets);
      expect(find.text('300 GT₵'), findsOneWidget);
      expect(
        tester.getTopLeft(find.text('Sua carteira')).dy,
        lessThan(tester.getTopLeft(find.text('Recarga educativa')).dy),
      );
    },
  );
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
