import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_client.dart';
import '../../core/providers.dart';
import '../../core/formatters.dart';

class AntiAbuseChallenge {
  const AntiAbuseChallenge({
    required this.prompt,
    required this.token,
    required this.expiresAt,
  });

  final String prompt;
  final String token;
  final String expiresAt;

  factory AntiAbuseChallenge.fromJson(Map<String, dynamic> json) {
    return AntiAbuseChallenge(
      prompt: safeString(json['prompt']),
      token: safeString(json['token']),
      expiresAt: safeString(json['expires_at']),
    );
  }
}

class AntiAbuseRepository {
  const AntiAbuseRepository(this._api);

  final ApiClient _api;

  Future<AntiAbuseChallenge> fetchChallenge() async {
    final json = await _api.getMap('/anti-abuse/challenge');
    return AntiAbuseChallenge.fromJson(json);
  }
}

final antiAbuseRepositoryProvider = Provider<AntiAbuseRepository>(
  (ref) => AntiAbuseRepository(ref.watch(apiClientProvider)),
);

final antiAbuseChallengeProvider =
    FutureProvider.autoDispose<AntiAbuseChallenge>(
      (ref) => ref.watch(antiAbuseRepositoryProvider).fetchChallenge(),
    );
