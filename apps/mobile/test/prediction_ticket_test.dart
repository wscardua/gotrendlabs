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
import 'package:gotrendlabs_mobile/src/features/markets/market_models.dart';
import 'package:gotrendlabs_mobile/src/features/markets/prediction_ticket.dart';

void main() {
  testWidgets('PredictionTicket mirrors web preview labels', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authControllerProvider.overrideWith(
            _UnauthenticatedAuthController.new,
          ),
        ],
        child: MaterialApp(
          home: Scaffold(
            body: SingleChildScrollView(
              child: PredictionTicket(market: _market()),
            ),
          ),
        ),
      ),
    );

    expect(find.text('Opção escolhida'), findsOneWidget);
    expect(find.text('Selecione'), findsOneWidget);
    expect(find.text('Crédito possível se acertar'), findsOneWidget);
    expect(find.text('-'), findsOneWidget);
    expect(find.text('Crédito reservado'), findsNWidgets(2));
    expect(find.text('80 GT₵'), findsNWidgets(2));

    await tester.tap(find.byType(ChoiceChip).first);
    await tester.pump();

    expect(find.text('SIM'), findsNWidgets(2));
    expect(find.text('-'), findsOneWidget);
  });

  testWidgets('PredictionTicket refreshes possible credit from API', (
    tester,
  ) async {
    final dio = Dio(BaseOptions(baseUrl: 'http://api.test'));
    final stakes = <int>[];
    dio.httpClientAdapter = _Adapter((options) {
      expect(options.method, 'POST');
      expect(options.path, '/markets/mercado-aberto/prediction-preview');
      final data = Map<String, dynamic>.from(options.data as Map);
      final stake = data['stake_amount'] as int;
      stakes.add(stake);
      return {
        'market_id': 10,
        'option_id': data['option_id'],
        'stake_amount': stake,
        'probability_exact': 50.0,
        'estimated_return': stake * 2,
      };
    });

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authControllerProvider.overrideWith(_AuthenticatedAuthController.new),
          apiClientProvider.overrideWithValue(
            ApiClient(dio: dio, tokenStore: MemoryTokenStore()),
          ),
        ],
        child: MaterialApp(
          home: Scaffold(
            body: SingleChildScrollView(
              child: PredictionTicket(market: _market()),
            ),
          ),
        ),
      ),
    );

    await tester.tap(find.byType(ChoiceChip).first);
    await tester.pump(const Duration(milliseconds: 350));
    await tester.pump();

    expect(find.text('160 GT₵'), findsOneWidget);

    await tester.drag(find.byType(Slider), const Offset(-240, 0));
    await tester.pump(const Duration(milliseconds: 350));
    await tester.pump();
    await tester.pump();

    expect(stakes.length, greaterThanOrEqualTo(2));
    expect(stakes.last, isNot(80));
    expect(find.text('${stakes.last * 2} GT₵'), findsOneWidget);
  });

  testWidgets('Prediction confirmation sheet fits compact physical screens', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(360, 560);
    tester.view.devicePixelRatio = 1;
    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
    });
    final dio = Dio(BaseOptions(baseUrl: 'http://api.test'));
    dio.httpClientAdapter = _Adapter((options) {
      final data = Map<String, dynamic>.from(options.data as Map);
      return {
        'market_id': 10,
        'option_id': data['option_id'],
        'stake_amount': data['stake_amount'],
        'probability_exact': 50.0,
        'estimated_return': 160,
      };
    });

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authControllerProvider.overrideWith(_AuthenticatedAuthController.new),
          apiClientProvider.overrideWithValue(
            ApiClient(dio: dio, tokenStore: MemoryTokenStore()),
          ),
        ],
        child: MaterialApp(
          home: Scaffold(
            body: ListView(children: [PredictionTicket(market: _market())]),
          ),
        ),
      ),
    );

    await tester.tap(find.byType(ChoiceChip).first);
    await tester.pump(const Duration(milliseconds: 350));
    await tester.pump();
    await tester.drag(find.byType(ListView), const Offset(0, -360));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Pré-visualizar e confirmar'));
    await tester.pumpAndSettle();

    expect(find.text('Confirmar previsão'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}

class _UnauthenticatedAuthController extends AuthController {
  @override
  AuthState build() {
    return const AuthState();
  }
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

class _Adapter implements HttpClientAdapter {
  _Adapter(this.handler);

  final Map<String, dynamic> Function(RequestOptions options) handler;

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    return ResponseBody.fromString(
      jsonEncode(handler(options)),
      200,
      headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      },
    );
  }

  @override
  void close({bool force = false}) {}
}

Market _market() {
  return Market.fromJson({
    'slug': 'mercado-aberto',
    'title': 'O mercado teste ficará aberto?',
    'category': 'Tecnologia',
    'subcategory': 'Apps',
    'event': 'Geral',
    'kind': 'binary',
    'status': 'open',
    'status_label': 'Aberto',
    'primary_outcome': 'SIM',
    'primary_probability': 64,
    'primary_probability_exact': 64.0,
    'human_volume_gtl': 120,
    'human_participants': 8,
    'comment_count': 2,
    'market_like_count': 1,
    'view_count': 10,
    'share_count': 0,
    'closes_in': '3d',
    'close_label': 'Fecha em 3 dias',
    'image_url': '',
    'thumb': 'GT',
    'thumb_color': '#35A7FF',
    'summary': 'Resumo',
    'resolution_criteria': 'Critério',
    'options': [
      {'id': 1, 'label': 'SIM', 'probability': 64, 'probability_exact': 64.0},
      {'id': 2, 'label': 'NÃO', 'probability': 36, 'probability_exact': 36.0},
    ],
  });
}
