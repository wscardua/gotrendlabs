import '../../core/api_client.dart';
import 'auth_models.dart';

class AuthRepository {
  const AuthRepository(this._api);

  final ApiClient _api;

  Future<AuthOutcome> login({
    required String email,
    required String password,
  }) async {
    final json = await _api.postMap(
      '/auth/login',
      data: {'email': email, 'password': password},
    );
    if (json['mfa_required'] == true) {
      return MfaChallenge(
        token: json['challenge_token'] as String,
        enrollmentRequired: json['enrollment_required'] as bool,
      );
    }
    return AuthResult.fromJson(json);
  }

  Future<String> enrollMfa(String token) async {
    final json = await _api.postMap(
      '/auth/mfa/enroll',
      data: {'challenge_token': token},
    );
    return json['manual_key'] as String;
  }

  Future<AuthResult> verifyMfa(
    String token,
    String code, {
    required bool recovery,
  }) async {
    final json = await _api.postMap(
      '/auth/mfa/verify',
      data: {
        'challenge_token': token,
        'code': recovery ? '' : code,
        'recovery_code': recovery ? code : '',
      },
    );
    return AuthResult.fromJson(json);
  }

  Future<AuthResult> register({
    required String displayName,
    required String email,
    required String birthDate,
    required String password,
    required bool termsAccepted,
    String antiAbuseToken = '',
    String antiAbuseAnswer = '',
  }) async {
    final json = await _api.postMap(
      '/auth/register',
      data: {
        'display_name': displayName,
        'email': email,
        'birth_date': birthDate,
        'password': password,
        'language': 'pt-br',
        'terms_accepted': termsAccepted,
        'recaptcha_token': '',
        'anti_abuse_token': antiAbuseToken,
        'anti_abuse_answer': antiAbuseAnswer,
        'referral_code': '',
      },
    );
    return AuthResult.fromJson(json);
  }

  Future<GtlUser> session() async {
    final json = await _api.getMap('/auth/session');
    return GtlUser.fromJson(Map<String, dynamic>.from(json['user'] as Map));
  }

  Future<void> logout() => _api.postEmpty('/auth/logout');

  Future<void> requestPasswordReset(String email) async {
    await _api.postMap('/auth/password-reset/request', data: {'email': email});
  }
}
