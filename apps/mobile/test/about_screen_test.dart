import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gotrendlabs_mobile/src/features/auth/auth_controller.dart';
import 'package:gotrendlabs_mobile/src/features/auth/auth_models.dart';
import 'package:gotrendlabs_mobile/src/features/info/about_screen.dart';
import 'package:gotrendlabs_mobile/src/theme.dart';
import 'package:package_info_plus/package_info_plus.dart';

void main() {
  testWidgets('AboutScreen shows app, API and account diagnostics', (
    tester,
  ) async {
    PackageInfo.setMockInitialValues(
      appName: 'GoTrendLabs',
      packageName: 'br.com.gotrendlabs.gotrendlabs_mobile',
      version: '1.2.3',
      buildNumber: '45',
      buildSignature: '',
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authControllerProvider.overrideWith(_AuthenticatedAuthController.new),
          aboutApiHealthProvider.overrideWith((ref) async => {'status': 'ok'}),
        ],
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: const AboutScreen(),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Sobre'), findsWidgets);
    expect(find.text('1.2.3'), findsOneWidget);
    expect(find.text('45'), findsOneWidget);
    expect(find.text('Saúde da API'), findsOneWidget);
    expect(find.text('ativa'), findsOneWidget);
    expect(find.text('Operando normalmente'), findsOneWidget);
    expect(find.text('API BASE'), findsNothing);
    expect(find.text('WEB BASE'), findsNothing);
    expect(find.text('IDENTIFICADOR'), findsOneWidget);
    expect(find.text('ID'), findsNothing);
    expect(find.text('@tester'), findsOneWidget);

    await tester.drag(find.byType(ListView), const Offset(0, -1000));
    await tester.pumpAndSettle();

    expect(find.text('Copiar diagnóstico'), findsOneWidget);
  });
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
