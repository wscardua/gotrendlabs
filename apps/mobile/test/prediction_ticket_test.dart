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

  testWidgets('Position desk previews reinforcement through FastAPI', (
    tester,
  ) async {
    final dio = Dio(BaseOptions(baseUrl: 'http://api.test'));
    final paths = <String>[];
    dio.httpClientAdapter = _Adapter((options) {
      paths.add(options.path);
      expect(options.method, 'POST');
      final data = Map<String, dynamic>.from(options.data as Map);
      if (options.path == '/markets/mercado-aberto/position-preview') {
        expect(data['action'], 'reinforcement');
        expect(data['option_id'], 1);
        return {
          'market_id': 10,
          'option_id': 1,
          'action': 'reinforcement',
          'stake_amount': data['stake_amount'],
          'active_stake_amount': 120,
          'active_position_count': 2,
          'penalty_amount': 0,
          'revision_penalty_percent': 10,
          'new_position_stake_amount': data['stake_amount'],
          'position_total_after': 200,
          'probability_exact': 50.0,
          'estimated_return': 160,
          'reinforcement_remaining': 1,
          'revision_remaining': 1,
          'allowed': true,
          'blocked_reason': '',
        };
      }
      expect(options.path, '/markets/mercado-aberto/position-actions');
      expect(data['action'], 'reinforcement');
      expect(data['option_id'], 1);
      return {
        'prediction_id': 200,
        'market_id': 10,
        'option_id': 1,
        'action': 'reinforcement',
        'stake_amount': data['stake_amount'],
        'penalty_amount': 0,
        'accepted_at': '2026-06-14T12:00:00Z',
        'wallet_balance_after': {},
        'market_probability_snapshot': [],
        'potential_payout': 160,
        'viewer_position': _viewerPosition(),
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
            body: ListView(
              children: [PredictionTicket(market: _positionMarket())],
            ),
          ),
        ),
      ),
    );

    expect(find.text('Sua posição atual'), findsOneWidget);
    expect(find.text('Sua escolha'), findsOneWidget);
    expect(
      find.text('2 movimento(s) ativos considerados pela API'),
      findsOneWidget,
    );
    expect(find.text('Adicionar GT₵ à sua escolha atual'), findsOneWidget);
    expect(find.text('Mover sua posição para outra opção'), findsOneWidget);
    expect(find.text('GT₵ para aumentar'), findsNothing);

    await tester.tap(find.text('Aumentar posição'));
    await tester.pumpAndSettle();
    expect(find.text('GT₵ para aumentar'), findsOneWidget);

    await tester.drag(find.byType(ListView), const Offset(0, -700));
    await tester.pumpAndSettle();
    await tester.tap(
      find.widgetWithText(FilledButton, 'Pré-visualizar aumento'),
    );
    await tester.pumpAndSettle();

    expect(find.text('Confirmar aumento'), findsWidgets);
    expect(find.text('Novo total ativo'), findsWidgets);
    expect(find.text('200 GT₵'), findsWidgets);

    await tester.tap(
      find.widgetWithText(FilledButton, 'Confirmar aumento').last,
    );
    await tester.pumpAndSettle();

    expect(paths, contains('/markets/mercado-aberto/position-actions'));
    expect(find.text('Posição aumentada.'), findsOneWidget);
  });

  testWidgets('Position desk previews revision with backend penalty', (
    tester,
  ) async {
    final dio = Dio(BaseOptions(baseUrl: 'http://api.test'));
    dio.httpClientAdapter = _Adapter((options) {
      expect(options.method, 'POST');
      expect(options.path, '/markets/mercado-aberto/position-preview');
      final data = Map<String, dynamic>.from(options.data as Map);
      expect(data['action'], 'revision');
      expect(data['option_id'], 2);
      expect(data['stake_amount'], 0);
      return {
        'market_id': 10,
        'option_id': 2,
        'action': 'revision',
        'stake_amount': 0,
        'active_stake_amount': 120,
        'active_position_count': 2,
        'penalty_amount': 12,
        'revision_penalty_percent': 10,
        'new_position_stake_amount': 108,
        'position_total_after': 108,
        'probability_exact': 36.0,
        'estimated_return': 300,
        'reinforcement_remaining': 2,
        'revision_remaining': 0,
        'allowed': true,
        'blocked_reason': '',
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
            body: ListView(
              children: [PredictionTicket(market: _positionMarket())],
            ),
          ),
        ),
      ),
    );

    expect(find.text('Movimentos que serão encerrados'), findsNothing);

    await tester.ensureVisible(find.text('Trocar escolha'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Trocar escolha'));
    await tester.pumpAndSettle();
    expect(find.text('Movimentos que serão encerrados'), findsOneWidget);

    await tester.drag(find.byType(ListView), const Offset(0, -520));
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(ChoiceChip, 'NÃO'));
    await tester.pump();
    await tester.drag(find.byType(ListView), const Offset(0, -360));
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(FilledButton, 'Confirmar troca'));
    await tester.pumpAndSettle();

    expect(find.text('Confirmar troca'), findsWidgets);
    expect(find.text('Custo da troca'), findsWidgets);
    expect(find.text('12 GT₵ (10%)'), findsWidgets);
    expect(find.text('108 GT₵'), findsWidgets);
  });

  testWidgets('Position desk shows backend blocked reasons', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authControllerProvider.overrideWith(_AuthenticatedAuthController.new),
        ],
        child: MaterialApp(
          home: Scaffold(
            body: SingleChildScrollView(
              child: PredictionTicket(
                market: _positionMarket(
                  viewerPosition: {
                    ..._viewerPosition(),
                    'can_reinforce': false,
                    'can_revise': false,
                    'reinforcement_remaining': 0,
                    'revision_remaining': 0,
                    'reinforcement_blocked_reason':
                        'Limite de reforços atingido neste mercado.',
                    'revision_blocked_reason':
                        'Janela de revisão encerrada para este mercado.',
                  },
                ),
              ),
            ),
          ),
        ),
      ),
    );

    expect(
      find.text('Limite de reforços atingido neste mercado.'),
      findsWidgets,
    );
    expect(
      find.text('Janela de revisão encerrada para este mercado.'),
      findsOneWidget,
    );
    expect(find.text('Bloqueado'), findsNWidgets(2));
    expect(
      find.widgetWithText(FilledButton, 'Pré-visualizar aumento'),
      findsNothing,
    );
  });

  testWidgets('Position action frames stay closed with a single action', (
    tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authControllerProvider.overrideWith(_AuthenticatedAuthController.new),
        ],
        child: MaterialApp(
          home: Scaffold(
            body: ListView(
              children: [
                PredictionTicket(
                  market: _positionMarket(
                    viewerPosition: {
                      ..._viewerPosition(),
                      'can_revise': false,
                      'revision_remaining': 0,
                      'revision_blocked_reason':
                          'Janela de troca encerrada para este mercado.',
                    },
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );

    expect(find.text('Aumentar posição'), findsOneWidget);
    expect(find.text('Trocar escolha'), findsOneWidget);
    expect(find.text('GT₵ para aumentar'), findsNothing);
    expect(
      find.widgetWithText(FilledButton, 'Pré-visualizar aumento'),
      findsNothing,
    );

    await tester.tap(find.text('Aumentar posição'));
    await tester.pumpAndSettle();

    expect(find.text('GT₵ para aumentar'), findsOneWidget);
    expect(
      find.widgetWithText(FilledButton, 'Pré-visualizar aumento'),
      findsOneWidget,
    );
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

Market _market({Map<String, dynamic>? viewerPosition}) {
  final json = {
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
    'viewer_has_prediction': viewerPosition != null,
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
  };
  if (viewerPosition != null) {
    json['viewer_position'] = viewerPosition;
  }
  return Market.fromJson(json);
}

Market _positionMarket({Map<String, dynamic>? viewerPosition}) {
  return _market(viewerPosition: viewerPosition ?? _viewerPosition());
}

Map<String, dynamic> _viewerPosition() {
  return {
    'has_position': true,
    'option_id': 1,
    'option_label': 'SIM',
    'active_stake_amount': 120,
    'potential_payout_total': 240,
    'probability_at_entry': 50.0,
    'position_count': 2,
    'reinforcement_count': 1,
    'reinforcement_remaining': 2,
    'reinforcement_max_count': 3,
    'revision_count': 0,
    'revision_remaining': 1,
    'revision_penalty_percent': 10,
    'revision_penalty_amount': 12,
    'revision_new_stake_amount': 108,
    'can_reinforce': true,
    'can_revise': true,
    'reinforcement_blocked_reason': '',
    'revision_blocked_reason': '',
    'active_entries': [
      {
        'id': 100,
        'option_id': 1,
        'option_label': 'SIM',
        'action_type': 'initial',
        'position_sequence': 1,
        'stake_amount': 80,
        'probability_at_entry': 64.0,
        'potential_payout': 125,
        'created_at': '2026-06-14T10:00:00Z',
      },
      {
        'id': 101,
        'option_id': 1,
        'option_label': 'SIM',
        'action_type': 'reinforcement',
        'position_sequence': 2,
        'stake_amount': 40,
        'probability_at_entry': 60.0,
        'potential_payout': 67,
        'created_at': '2026-06-14T11:00:00Z',
      },
    ],
    'history': [
      {
        'id': 100,
        'option_id': 1,
        'option_label': 'SIM',
        'action_type': 'initial',
        'position_sequence': 1,
        'stake_amount': 80,
        'probability_at_entry': 64.0,
        'potential_payout': 125,
        'status': 'open',
        'created_at': '2026-06-14T10:00:00Z',
      },
    ],
  };
}
