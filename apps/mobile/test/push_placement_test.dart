import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gotrendlabs_mobile/src/core/api_client.dart';
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
    await tester.scrollUntilVisible(find.text('Ver desempenho'), 320);
    expect(find.text('Ver desempenho'), findsOneWidget);
  });

  testWidgets('Profile shows and edits private user data', (tester) async {
    var profile = _profilePayload();
    final repo = _FakeProfileRepository(
      onUpdate: ({required email, required birthDate, required bio}) async {
        profile = {
          ...profile,
          'user': {
            ...Map<String, dynamic>.from(profile['user'] as Map),
            'email': email,
            'email_confirmed': false,
          },
          'birth_date': birthDate,
          'bio': bio,
        };
        return profile;
      },
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authControllerProvider.overrideWith(_AuthenticatedAuthController.new),
          profileProvider.overrideWith((ref) async => profile),
          profileRepositoryProvider.overrideWithValue(repo),
          badgesProvider.overrideWith((ref) async => []),
          biometricCapabilityProvider.overrideWith((ref) async => true),
          biometricPreferenceProvider.overrideWith((ref) async => false),
          rememberedSessionProvider.overrideWith((ref) async => true),
        ],
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: const ProfileScreen(),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Dados pessoais'), findsOneWidget);
    expect(find.text('tester@example.com'), findsOneWidget);
    expect(find.text('18/06/1990'), findsOneWidget);
    expect(find.text('Bio inicial'), findsOneWidget);

    await tester.tap(find.text('Editar'));
    await tester.pumpAndSettle();

    final birthDateField = tester.widget<TextField>(
      find.widgetWithText(TextField, 'Data de nascimento'),
    );
    expect(birthDateField.controller?.text, '18/06/1990');
    expect(birthDateField.keyboardType, TextInputType.number);
    await tester.enterText(
      find.widgetWithText(TextField, 'Email'),
      'novo@example.com',
    );
    await tester.enterText(
      find.widgetWithText(TextField, 'Data de nascimento'),
      '01021991',
    );
    expect(find.text('01/02/1991'), findsOneWidget);
    await tester.enterText(
      find.widgetWithText(TextField, 'Bio'),
      'Bio atualizada',
    );
    await tester.tap(find.text('Salvar dados'));
    await tester.pumpAndSettle();

    expect(repo.lastEmail, 'novo@example.com');
    expect(repo.lastBirthDate, '1991-02-01');
    expect(repo.lastBio, 'Bio atualizada');
    expect(find.text('novo@example.com'), findsOneWidget);
    expect(find.text('Bio atualizada'), findsOneWidget);
  });

  testWidgets('Unconfirmed profile edit only corrects email', (tester) async {
    var profile = _profilePayload();
    final repo = _FakeProfileRepository(
      onUpdate: ({required email, required birthDate, required bio}) async {
        throw AssertionError(
          'Unconfirmed users must not update private fields',
        );
      },
      onEmailUpdate: ({required email}) async {
        profile = {
          ...profile,
          'user': {
            ...Map<String, dynamic>.from(profile['user'] as Map),
            'email': email,
            'email_confirmed': false,
          },
        };
        return profile;
      },
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authControllerProvider.overrideWith(_UnconfirmedAuthController.new),
          profileProvider.overrideWith((ref) async => profile),
          profileRepositoryProvider.overrideWithValue(repo),
          badgesProvider.overrideWith((ref) async => []),
          biometricCapabilityProvider.overrideWith((ref) async => true),
          biometricPreferenceProvider.overrideWith((ref) async => false),
          rememberedSessionProvider.overrideWith((ref) async => true),
        ],
        child: MaterialApp(
          theme: buildGoTrendLabsTheme(),
          home: const ProfileScreen(),
        ),
      ),
    );

    await tester.pumpAndSettle();
    await tester.tap(find.text('Editar'));
    await tester.pumpAndSettle();

    expect(
      find.text(
        'Depois de confirmar o email, você poderá alterar nascimento e bio.',
      ),
      findsOneWidget,
    );
    await tester.enterText(
      find.widgetWithText(TextField, 'Email'),
      'corrigido@example.com',
    );
    await tester.tap(find.text('Salvar dados'));
    await tester.pumpAndSettle();

    expect(repo.lastEmailOnly, 'corrigido@example.com');
    expect(repo.lastBirthDate, isNull);
    expect(repo.lastBio, isNull);
    expect(find.text('corrigido@example.com'), findsOneWidget);
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
    'user': {
      'id': 7,
      'display_name': 'Tester',
      'handle': 'tester',
      'email': 'tester@example.com',
      'email_confirmed': true,
      'is_staff': false,
    },
    'birth_date': '1990-06-18',
    'bio': 'Bio inicial',
    'strong_category': '',
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

class _FakeProfileRepository extends ProfileRepository {
  _FakeProfileRepository({required this.onUpdate, this.onEmailUpdate})
    : super(ApiClient(tokenStore: MemoryTokenStore()));

  final Future<Map<String, dynamic>> Function({
    required String email,
    required String birthDate,
    required String bio,
  })
  onUpdate;
  final Future<Map<String, dynamic>> Function({required String email})?
  onEmailUpdate;

  String? lastEmail;
  String? lastBirthDate;
  String? lastBio;
  String? lastEmailOnly;

  @override
  Future<Map<String, dynamic>> updatePrivateProfile({
    required String email,
    required String birthDate,
    required String bio,
  }) {
    lastEmail = email;
    lastBirthDate = birthDate;
    lastBio = bio;
    return onUpdate(email: email, birthDate: birthDate, bio: bio);
  }

  @override
  Future<Map<String, dynamic>> updateEmail({required String email}) {
    lastEmailOnly = email;
    return onEmailUpdate?.call(email: email) ??
        onUpdate(email: email, birthDate: '', bio: '');
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

class _UnconfirmedAuthController extends AuthController {
  @override
  AuthState build() {
    return const AuthState(
      user: GtlUser(
        id: 7,
        handle: 'tester',
        email: 'tester@example.com',
        displayName: 'Tester',
        emailConfirmed: false,
        isStaff: false,
      ),
    );
  }
}
