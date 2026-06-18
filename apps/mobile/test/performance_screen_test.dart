import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gotrendlabs_mobile/src/features/auth/auth_controller.dart';
import 'package:gotrendlabs_mobile/src/features/auth/auth_models.dart';
import 'package:gotrendlabs_mobile/src/features/performance/performance_providers.dart';
import 'package:gotrendlabs_mobile/src/features/performance/performance_screen.dart';
import 'package:gotrendlabs_mobile/src/theme.dart';

void main() {
  testWidgets('PerformanceScreen shows login CTA for visitors', (tester) async {
    var calls = 0;
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authControllerProvider.overrideWith(
            _UnauthenticatedAuthController.new,
          ),
          performanceProvider.overrideWith((ref) async {
            calls += 1;
            return _performancePayload();
          }),
        ],
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: const PerformanceScreen(),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Desempenho protegido'), findsOneWidget);
    expect(find.text('Entrar'), findsOneWidget);
    expect(calls, 0);
  });

  testWidgets('PerformanceScreen renders scorecard history and progression', (
    tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authControllerProvider.overrideWith(_AuthenticatedAuthController.new),
          performanceProvider.overrideWith(
            (ref) async => _performancePayload(),
          ),
        ],
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: const PerformanceScreen(),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Placar'), findsOneWidget);
    expect(find.text('Reputação'.toUpperCase()), findsOneWidget);
    expect(find.text('128'), findsOneWidget);
    await tester.scrollUntilVisible(
      find.text('Histórico'),
      320,
      scrollable: find.byType(Scrollable).first,
    );
    expect(find.text('Histórico'), findsOneWidget);
    expect(find.text('Mercado resolvido de teste'), findsOneWidget);
    expect(find.text('Acertou'), findsOneWidget);
    expect(find.text('+6'), findsOneWidget);
    expect(find.text('+80 GT₵'), findsOneWidget);
    await tester.scrollUntilVisible(
      find.text('Progressão'),
      320,
      scrollable: find.byType(Scrollable).first,
    );
    expect(find.text('Progressão'), findsOneWidget);
    expect(find.text('Primeira resolução'), findsOneWidget);
    expect(
      find.text(
        'Próximos marcos aparecem quando houver dados suficientes para acompanhar com confiança.',
      ),
      findsOneWidget,
    );
  });

  testWidgets('PerformanceScreen shows empty resolved history state', (
    tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authControllerProvider.overrideWith(_AuthenticatedAuthController.new),
          performanceProvider.overrideWith(
            (ref) async =>
                _performancePayload(history: <Map<String, dynamic>>[]),
          ),
        ],
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: const PerformanceScreen(),
        ),
      ),
    );

    await tester.pumpAndSettle();

    await tester.scrollUntilVisible(
      find.text('Nenhuma previsão resolvida ainda'),
      320,
      scrollable: find.byType(Scrollable).first,
    );
    expect(find.text('Nenhuma previsão resolvida ainda'), findsOneWidget);
  });

  testWidgets('PerformanceScreen refetches on open and pull refresh', (
    tester,
  ) async {
    var calls = 0;
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authControllerProvider.overrideWith(_AuthenticatedAuthController.new),
          performanceProvider.overrideWith((ref) async {
            calls += 1;
            return _performancePayload(score: 120 + calls);
          }),
        ],
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: const PerformanceScreen(),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(calls, greaterThanOrEqualTo(2));
    final callsAfterOpen = calls;

    await tester.drag(find.byType(ListView), const Offset(0, 360));
    await tester.pump();
    await tester.pumpAndSettle();

    expect(calls, greaterThan(callsAfterOpen));
    final callsAfterPull = calls;

    tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.resumed);
    await tester.pumpAndSettle();

    expect(calls, greaterThan(callsAfterPull));
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

Map<String, dynamic> _performancePayload({
  int score = 128,
  List<Map<String, dynamic>>? history,
}) {
  return {
    'scorecard': {
      'reputation_score': score,
      'ranking_position': 3,
      'resolved_predictions_count': 4,
      'accuracy_indicator': '75%',
      'streak': 2,
      'strong_category': 'IA',
      'last_updated_at': '2026-06-18T12:00:00+00:00',
    },
    'history':
        history ??
        [
          {
            'prediction_id': 11,
            'market_slug': 'mercado-resolvido',
            'market_title': 'Mercado resolvido de teste',
            'option_label': 'SIM',
            'winning_option_label': 'SIM',
            'won': true,
            'result_label': 'Acertou',
            'stake_amount': 100,
            'probability_at_entry': 40.0,
            'reputation_delta': 6,
            'gtc_result': 80,
            'educational_result_label': '+80 GT₵',
            'resolved_at_label': '18/06/2026 09:00 America/Sao_Paulo',
          },
        ],
    'progression': {
      'earned_badges_count': 1,
      'badges': [
        {
          'code': 'first_resolution',
          'name': 'Primeira resolução',
          'description': 'Primeira resolução auditável.',
          'status': 'earned',
          'earned_at': '2026-06-18T12:00:00+00:00',
          'image_url': '',
          'image_dark_url': '',
        },
      ],
      'latest_awards': [
        {
          'code': 'first_resolution',
          'name': 'Primeira resolução',
          'description': 'Primeira resolução auditável.',
          'status': 'earned',
          'earned_at': '2026-06-18T12:00:00+00:00',
          'image_url': '',
          'image_dark_url': '',
        },
      ],
      'next_milestones': <Map<String, dynamic>>[],
    },
  };
}
