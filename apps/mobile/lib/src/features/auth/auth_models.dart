import '../../core/formatters.dart';

class GtlUser {
  const GtlUser({
    required this.id,
    required this.handle,
    required this.email,
    required this.displayName,
    required this.emailConfirmed,
    required this.isStaff,
  });

  final int id;
  final String handle;
  final String email;
  final String displayName;
  final bool emailConfirmed;
  final bool isStaff;

  factory GtlUser.fromJson(Map<String, dynamic> json) {
    return GtlUser(
      id: safeInt(json['id']),
      handle: safeString(json['handle']),
      email: safeString(json['email']),
      displayName: safeString(json['display_name']),
      emailConfirmed: safeBool(json['email_confirmed'], true),
      isStaff: safeBool(json['is_staff']),
    );
  }
}

class AuthSession {
  const AuthSession({required this.token, required this.expiresAt});

  final String token;
  final String expiresAt;

  factory AuthSession.fromJson(Map<String, dynamic> json) {
    return AuthSession(
      token: safeString(json['token']),
      expiresAt: safeString(json['expires_at']),
    );
  }
}

sealed class AuthOutcome {
  const AuthOutcome();
}

class MfaChallenge extends AuthOutcome {
  const MfaChallenge({required this.token, required this.enrollmentRequired});
  final String token;
  final bool enrollmentRequired;
}

class AuthResult extends AuthOutcome {
  const AuthResult({
    required this.user,
    required this.session,
    this.recoveryCodes = const [],
  });

  final GtlUser user;
  final AuthSession session;
  final List<String> recoveryCodes;

  factory AuthResult.fromJson(Map<String, dynamic> json) {
    return AuthResult(
      recoveryCodes: List<String>.from(json['recovery_codes'] ?? const []),
      user: GtlUser.fromJson(Map<String, dynamic>.from(json['user'] as Map)),
      session: AuthSession.fromJson(
        Map<String, dynamic>.from(json['session'] as Map),
      ),
    );
  }
}

class AuthState {
  const AuthState({
    this.user,
    this.restoring = false,
    this.sessionLocked = false,
    this.busy = false,
    this.error,
    this.challenge,
    this.manualKey,
    this.recoveryCodes = const [],
  });

  final GtlUser? user;
  final bool restoring;
  final bool sessionLocked;
  final bool busy;
  final String? error;
  final MfaChallenge? challenge;
  final String? manualKey;
  final List<String> recoveryCodes;

  bool get isAuthenticated => user != null;

  AuthState copyWith({
    GtlUser? user,
    bool? restoring,
    bool? sessionLocked,
    bool? busy,
    String? error,
    bool clearUser = false,
    bool clearError = false,
  }) {
    return AuthState(
      challenge: challenge,
      manualKey: manualKey,
      recoveryCodes: recoveryCodes,
      user: clearUser ? null : user ?? this.user,
      restoring: restoring ?? this.restoring,
      sessionLocked: sessionLocked ?? this.sessionLocked,
      busy: busy ?? this.busy,
      error: clearError ? null : error ?? this.error,
    );
  }
}
