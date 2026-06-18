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
      expect(find.text('Fila Admin Ops'), findsNothing);
      expect(find.text('Solicitação'), findsNothing);
      expect(find.text('Revisão'), findsNothing);
      expect(find.text('Crédito'), findsNothing);
      expect(
        tester.getTopLeft(find.text('Sua carteira')).dy,
        lessThan(tester.getTopLeft(find.text('Recarga educativa')).dy),
      );
    },
  );

  testWidgets('Wallet refetches cached balances on open and pull refresh', (
    tester,
  ) async {
    var ledgerCalls = 0;
    var rechargeCalls = 0;
    var walletCalls = 0;
    final container = ProviderContainer(
      overrides: [
        authControllerProvider.overrideWith(_AuthenticatedAuthController.new),
        ledgerProvider.overrideWith((ref) async {
          ledgerCalls += 1;
          final available = ledgerCalls == 1
              ? 900
              : ledgerCalls == 2
              ? 1700
              : 1900;
          final locked = ledgerCalls == 1 ? 40 : 300;
          return _ledger(available: available, locked: locked);
        }),
        walletProvider.overrideWith((ref) async {
          walletCalls += 1;
          return {'available_gtl': 1900, 'locked_gtl': 300};
        }),
        walletRechargeRequestsProvider.overrideWith((ref) async {
          rechargeCalls += 1;
          return _recharge(available: ledgerCalls <= 1 ? 900 : 1900);
        }),
      ],
    );
    addTearDown(container.dispose);

    await container.read(ledgerProvider.future);
    await container.read(walletProvider.future);
    await container.read(walletRechargeRequestsProvider.future);
    expect(ledgerCalls, 1);
    expect(walletCalls, 1);
    expect(rechargeCalls, 1);

    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: const WalletScreen(),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(ledgerCalls, 2);
    expect(rechargeCalls, 2);
    expect(find.text('1700 GT₵'), findsWidgets);
    expect(find.text('300 GT₵'), findsOneWidget);

    await tester.drag(find.byType(ListView), const Offset(0, 360));
    await tester.pump();
    await tester.pumpAndSettle();

    expect(ledgerCalls, 3);
    expect(walletCalls, 2);
    expect(rechargeCalls, 3);
    expect(find.text('1900 GT₵'), findsWidgets);
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

Map<String, dynamic> _ledger({required int available, required int locked}) {
  return {
    'wallet': {
      'available_gtl': available,
      'locked_gtl': locked,
      'total_earned_gtl': 0,
    },
    'entries': <dynamic>[],
  };
}

Map<String, dynamic> _recharge({required int available}) {
  return {
    'requests': <dynamic>[],
    'available_gtl': available,
    'min_balance_gtl': 100,
    'eligible': false,
  };
}
