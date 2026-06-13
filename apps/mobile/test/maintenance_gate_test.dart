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
      'checks': {'api': 'ok'},
    });

    expect(health.isHealthy, isTrue);
    expect(health.mobileMaintenanceEnabled, isTrue);
    expect(health.mobileMaintenanceMessage, 'App em manutenção.');
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
