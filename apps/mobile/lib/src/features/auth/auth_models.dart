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

class AuthResult {
  const AuthResult({required this.user, required this.session});

  final GtlUser user;
  final AuthSession session;

  factory AuthResult.fromJson(Map<String, dynamic> json) {
    return AuthResult(
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
    this.busy = false,
    this.error,
  });

  final GtlUser? user;
  final bool restoring;
  final bool busy;
  final String? error;

  bool get isAuthenticated => user != null;

  AuthState copyWith({
    GtlUser? user,
    bool? restoring,
    bool? busy,
    String? error,
    bool clearUser = false,
    bool clearError = false,
  }) {
    return AuthState(
      user: clearUser ? null : user ?? this.user,
      restoring: restoring ?? this.restoring,
      busy: busy ?? this.busy,
      error: clearError ? null : error ?? this.error,
    );
  }
}
