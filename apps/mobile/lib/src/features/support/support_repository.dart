import '../../core/api_client.dart';

class SupportRepository {
  const SupportRepository(this._api);

  final ApiClient _api;

  Future<void> sendFeedback({
    required String feedbackType,
    required String description,
    String severity = 'medium',
    String guestName = '',
    String guestEmail = '',
    String antiAbuseToken = '',
    String antiAbuseAnswer = '',
  }) async {
    await _api.postMap(
      '/feedback',
      data: {
        'guest_name': guestName,
        'guest_email': guestEmail.isEmpty ? null : guestEmail,
        'feedback_type': feedbackType,
        'severity': severity,
        'description': description,
        'recaptcha_token': '',
        'anti_abuse_token': antiAbuseToken,
        'anti_abuse_answer': antiAbuseAnswer,
      },
    );
  }

  Future<void> suggestMarket({
    required String question,
    required String category,
    required String subcategory,
    required String suggestedSource,
    required String rationale,
    String kind = 'binary',
    String guestName = '',
    String guestEmail = '',
    String antiAbuseToken = '',
    String antiAbuseAnswer = '',
  }) async {
    await _api.postMap(
      '/suggestions',
      data: {
        'guest_name': guestName,
        'guest_email': guestEmail.isEmpty ? null : guestEmail,
        'question': question,
        'category': category,
        'subcategory': subcategory,
        'kind': kind,
        'suggested_source': suggestedSource,
        'rationale': rationale,
        'recaptcha_token': '',
        'anti_abuse_token': antiAbuseToken,
        'anti_abuse_answer': antiAbuseAnswer,
      },
    );
  }
}
