import '../../core/api_client.dart';
import 'market_models.dart';

class MarketsRepository {
  const MarketsRepository(this._api);

  final ApiClient _api;

  Future<List<Market>> listMarkets({String? status, String? category}) async {
    final json = await _api.getMap(
      '/markets',
      query: {
        if (status != null && status.isNotEmpty) 'status': status,
        if (category != null && category.isNotEmpty) 'category': category,
      },
    );
    return ((json['markets'] as List<dynamic>?) ?? <dynamic>[])
        .whereType<Map>()
        .map((item) => Market.fromJson(Map<String, dynamic>.from(item)))
        .toList();
  }

  Future<Market> detail(String slug) async {
    return Market.fromJson(await _api.getMap('/markets/$slug'));
  }

  Future<void> trackView(String slug) async {
    await _api.postMap('/markets/$slug/view');
  }

  Future<Market> favorite(String slug, bool enabled) async {
    final json = enabled
        ? await _api.postMap('/markets/$slug/favorite')
        : await _api.deleteMap('/markets/$slug/favorite');
    return Market.fromJson(json);
  }

  Future<Market> like(String slug, bool enabled) async {
    final json = enabled
        ? await _api.postMap('/markets/$slug/like')
        : await _api.deleteMap('/markets/$slug/like');
    return Market.fromJson(json);
  }

  Future<void> trackShare(String slug) async {
    await _api.postMap('/markets/$slug/share');
  }

  Future<MarketComment> createComment(String slug, String body) async {
    final json = await _api.postMap(
      '/markets/$slug/comments',
      data: {'body': body, 'client_locale': 'pt-br'},
    );
    return MarketComment.fromJson(json);
  }

  Future<MarketComment> reactToComment(
    int id,
    String reaction,
    bool enabled,
  ) async {
    final json = enabled
        ? await _api.postMap('/comments/$id/$reaction')
        : await _api.deleteMap('/comments/$id/$reaction');
    return MarketComment.fromJson(json);
  }

  Future<PredictionPreview> previewPrediction({
    required String slug,
    required int optionId,
    required int stakeAmount,
  }) async {
    final json = await _api.postMap(
      '/markets/$slug/prediction-preview',
      data: {
        'option_id': optionId,
        'stake_amount': stakeAmount,
        'client_locale': 'pt-br',
      },
    );
    return PredictionPreview.fromJson(json);
  }

  Future<void> createPrediction({
    required String slug,
    required int optionId,
    required int stakeAmount,
  }) async {
    await _api.postMap(
      '/markets/$slug/predict',
      data: {
        'option_id': optionId,
        'stake_amount': stakeAmount,
        'client_locale': 'pt-br',
      },
    );
  }

  Future<PositionActionPreview> previewPositionAction({
    required String slug,
    required String action,
    required int optionId,
    required int stakeAmount,
  }) async {
    final json = await _api.postMap(
      '/markets/$slug/position-preview',
      data: {
        'action': action,
        'option_id': optionId,
        'stake_amount': stakeAmount,
        'client_locale': 'pt-br',
      },
    );
    return PositionActionPreview.fromJson(json);
  }

  Future<PositionActionResult> createPositionAction({
    required String slug,
    required String action,
    required int optionId,
    required int stakeAmount,
  }) async {
    final json = await _api.postMap(
      '/markets/$slug/position-actions',
      data: {
        'action': action,
        'option_id': optionId,
        'stake_amount': stakeAmount,
        'client_locale': 'pt-br',
      },
    );
    return PositionActionResult.fromJson(json);
  }
}
