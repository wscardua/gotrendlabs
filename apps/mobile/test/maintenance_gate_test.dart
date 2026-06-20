import 'dart:async';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gotrendlabs_mobile/src/core/api_client.dart';
import 'package:gotrendlabs_mobile/src/features/maintenance/maintenance_gate.dart';
import 'package:gotrendlabs_mobile/src/theme.dart';

void main() {
  test('BackendHealth parses enriched health payload', () {
    final health = BackendHealth.fromJson({
      'status': 'ok',
      'maintenance': {
        'mobile_enabled': true,
        'mobile_message': 'App em manutenção.',
      },
      'mobile': {
        'current_app_version': '1.0.7',
        'current_app_build': 8,
        'latest_android_version': '1.0.8',
        'latest_android_build': 9,
        'update_required': false,
        'update_available': true,
        'download_url': 'https://gotrendlabs.com.br/app.apk',
        'update_required_message': 'Atualize.',
      },
      'checks': {'api': 'ok'},
    });

    expect(health.isHealthy, isTrue);
    expect(health.mobileMaintenanceEnabled, isTrue);
    expect(health.mobileMaintenanceMessage, 'App em manutenção.');
    expect(health.updateRequired, isFalse);
    expect(health.updateAvailable, isTrue);
    expect(health.currentAppVersion, '1.0.7');
    expect(health.currentAppBuild, 8);
    expect(health.latestAndroidVersion, '1.0.8');
    expect(health.latestAndroidBuild, 9);
  });

  test(
    'MaintenanceRepository maps network failure to unavailable health',
    () async {
      final dio = Dio(BaseOptions(baseUrl: 'http://api.test'));
      dio.httpClientAdapter = _FailingAdapter();
      final repository = MaintenanceRepository(
        ApiClient(dio: dio, tokenStore: MemoryTokenStore()),
      );

      final health = await repository.check();

      expect(health.backendUnavailable, isTrue);
      expect(health.mobileMaintenanceEnabled, isTrue);
    },
  );

  testWidgets('MaintenanceGate blocks the shell during mobile maintenance', (
    tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          maintenanceControllerProvider.overrideWith(
            (ref) async => const BackendHealth(
              status: 'ok',
              mobileMaintenanceEnabled: true,
              mobileMaintenanceMessage: 'App em manutenção.',
            ),
          ),
        ],
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: const MaintenanceGate(child: Text('Shell liberado')),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Voltamos em breve'), findsOneWidget);
    expect(find.text('App em manutenção.'), findsOneWidget);
    expect(
      find.widgetWithText(FilledButton, 'Tentar novamente'),
      findsOneWidget,
    );
    expect(find.text('Shell liberado'), findsNothing);
  });

  testWidgets('MaintenanceGate blocks the shell when health is degraded', (
    tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          maintenanceControllerProvider.overrideWith(
            (ref) async => const BackendHealth(
              status: 'degraded',
              mobileMaintenanceEnabled: false,
              mobileMaintenanceMessage:
                  'Não conseguimos carregar o backend agora.',
              backendUnavailable: true,
            ),
          ),
        ],
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: const MaintenanceGate(child: Text('Shell liberado')),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Voltamos em breve'), findsOneWidget);
    expect(
      find.text('Não conseguimos carregar o backend agora.'),
      findsOneWidget,
    );
    expect(find.text('Shell liberado'), findsNothing);
  });

  testWidgets('MaintenanceGate allows compatible app with optional update', (
    tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          maintenanceControllerProvider.overrideWith(
            (ref) async => const BackendHealth(
              status: 'ok',
              mobileMaintenanceEnabled: false,
              mobileMaintenanceMessage: '',
              updateAvailable: true,
            ),
          ),
        ],
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: const MaintenanceGate(child: Text('Shell liberado')),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Shell liberado'), findsOneWidget);
    expect(find.text('Atualize para continuar'), findsNothing);
  });

  testWidgets('MaintenanceGate rechecks compatibility when app resumes', (
    tester,
  ) async {
    var updateRequired = false;
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          maintenanceControllerProvider.overrideWith((ref) async {
            return BackendHealth(
              status: 'ok',
              mobileMaintenanceEnabled: false,
              mobileMaintenanceMessage: '',
              updateRequired: updateRequired,
              currentAppVersion: '1.0.8',
              currentAppBuild: 9,
              latestAndroidVersion: '1.0.9',
              latestAndroidBuild: 10,
              downloadUrl: 'https://gotrendlabs.com.br/app.apk',
            );
          }),
        ],
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: const MaintenanceGate(child: Text('Shell liberado')),
        ),
      ),
    );

    await tester.pumpAndSettle();
    expect(find.text('Shell liberado'), findsOneWidget);

    updateRequired = true;
    tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.resumed);
    await tester.pumpAndSettle();

    expect(find.text('Atualize para continuar'), findsOneWidget);
    expect(find.text('Shell liberado'), findsNothing);
  });

  testWidgets('MaintenanceGate blocks when update override is raised', (
    tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          mobileUpdateOverrideProvider.overrideWith(
            () => _StaticMobileUpdateOverride(
              const MobileUpdateInfo(
                updateRequired: true,
                currentAppVersion: '1.0.8',
                currentAppBuild: 8,
                latestAndroidVersion: '1.0.8',
                latestAndroidBuild: 9,
                downloadUrl: 'https://gotrendlabs.com.br/app.apk',
              ),
            ),
          ),
        ],
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: const MaintenanceGate(child: Text('Shell liberado')),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Atualize para continuar'), findsOneWidget);
    expect(find.text('1.0.8 · build 8'), findsOneWidget);
    expect(find.text('1.0.8 · build 9'), findsOneWidget);
    expect(find.text('Shell liberado'), findsNothing);
  });

  testWidgets('MaintenanceGate blocks with required update screen', (
    tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          maintenanceControllerProvider.overrideWith(
            (ref) async => const BackendHealth(
              status: 'ok',
              mobileMaintenanceEnabled: false,
              mobileMaintenanceMessage: '',
              updateRequired: true,
              currentAppVersion: '1.0.7',
              currentAppBuild: 8,
              latestAndroidVersion: '1.0.8',
              latestAndroidBuild: 9,
              downloadUrl: 'https://gotrendlabs.com.br/app.apk',
              updateRequiredMessage:
                  'Atualize o app para continuar usando o GoTrendLabs.',
            ),
          ),
        ],
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: const MaintenanceGate(child: Text('Shell liberado')),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Atualize para continuar'), findsOneWidget);
    expect(
      find.text('Atualize o app para continuar usando o GoTrendLabs.'),
      findsOneWidget,
    );
    expect(find.text('Instalada'), findsOneWidget);
    expect(find.text('1.0.7 · build 8'), findsOneWidget);
    expect(find.text('Disponível'), findsOneWidget);
    expect(find.text('1.0.8 · build 9'), findsOneWidget);
    expect(find.widgetWithText(FilledButton, 'Atualizar'), findsOneWidget);
    expect(
      find.widgetWithText(OutlinedButton, 'Tentar novamente'),
      findsOneWidget,
    );
    expect(find.text('Shell liberado'), findsNothing);
  });
}

class _FailingAdapter implements HttpClientAdapter {
  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    throw DioException(
      requestOptions: options,
      type: DioExceptionType.connectionError,
    );
  }

  @override
  void close({bool force = false}) {}
}

class _StaticMobileUpdateOverride extends MobileUpdateOverride {
  _StaticMobileUpdateOverride(this.info);

  final MobileUpdateInfo info;

  @override
  MobileUpdateInfo? build() => info;
}
