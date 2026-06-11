import '../../core/formatters.dart';

class MarketOption {
  const MarketOption({
    required this.id,
    required this.label,
    required this.probability,
    required this.probabilityExact,
    required this.hint,
    required this.sparklinePath,
  });

  final int id;
  final String label;
  final int probability;
  final double probabilityExact;
  final String hint;
  final String sparklinePath;

  factory MarketOption.fromJson(Map<String, dynamic> json) {
    return MarketOption(
      id: safeInt(json['id']),
      label: safeString(json['label']),
      probability: safeInt(json['probability']),
      probabilityExact: safeDouble(json['probability_exact']),
      hint: safeString(json['hint']),
      sparklinePath: safeString(json['sparkline_path']),
    );
  }
}

class MarketComment {
  const MarketComment({
    required this.id,
    required this.authorHandle,
    required this.authorDisplayName,
    required this.authorIsBot,
    required this.body,
    required this.createdAtLabel,
    required this.likeCount,
    required this.dislikeCount,
    this.viewerReaction,
  });

  final int id;
  final String authorHandle;
  final String authorDisplayName;
  final bool authorIsBot;
  final String body;
  final String createdAtLabel;
  final int likeCount;
  final int dislikeCount;
  final String? viewerReaction;

  factory MarketComment.fromJson(Map<String, dynamic> json) {
    return MarketComment(
      id: safeInt(json['id']),
      authorHandle: safeString(json['author_handle']),
      authorDisplayName: safeString(json['author_display_name']),
      authorIsBot: safeBool(json['author_is_bot']),
      body: safeString(json['body']),
      createdAtLabel: safeString(
        json['created_at_label'],
        safeString(json['created_at']),
      ),
      likeCount: safeInt(json['like_count']),
      dislikeCount: safeInt(json['dislike_count']),
      viewerReaction: json['viewer_reaction']?.toString(),
    );
  }
}

class Market {
  const Market({
    required this.slug,
    required this.title,
    required this.category,
    required this.subcategory,
    required this.event,
    required this.kind,
    required this.status,
    required this.statusLabel,
    required this.primaryOutcome,
    required this.primaryProbability,
    required this.primaryProbabilityExact,
    required this.humanVolumeGtl,
    required this.humanParticipants,
    required this.commentCount,
    required this.likeCount,
    required this.viewCount,
    required this.shareCount,
    required this.isFeatured,
    required this.closesIn,
    required this.closeLabel,
    required this.imageUrl,
    required this.thumb,
    required this.thumbColor,
    required this.summary,
    required this.resolutionCriteria,
    required this.resolutionNote,
    required this.resolvedAtLabel,
    required this.viewerHasPrediction,
    required this.viewerHasFavorite,
    required this.viewerHasLike,
    required this.options,
    required this.comments,
    required this.sparklinePath,
    required this.sparklineSeries,
  });

  final String slug;
  final String title;
  final String category;
  final String subcategory;
  final String event;
  final String kind;
  final String status;
  final String statusLabel;
  final String primaryOutcome;
  final int primaryProbability;
  final double primaryProbabilityExact;
  final int humanVolumeGtl;
  final int humanParticipants;
  final int commentCount;
  final int likeCount;
  final int viewCount;
  final int shareCount;
  final bool isFeatured;
  final String closesIn;
  final String closeLabel;
  final String imageUrl;
  final String thumb;
  final String thumbColor;
  final String summary;
  final String resolutionCriteria;
  final String resolutionNote;
  final String resolvedAtLabel;
  final bool viewerHasPrediction;
  final bool viewerHasFavorite;
  final bool viewerHasLike;
  final List<MarketOption> options;
  final List<MarketComment> comments;
  final String sparklinePath;
  final List<Map<String, dynamic>> sparklineSeries;

  bool get isOpen => status == 'open';
  bool get isResolved => status == 'resolved';
  bool get isLocked => status == 'locked';
  String get probabilityLabel => formatProbability(primaryProbability);
  String get volumeLabel => formatGtl(humanVolumeGtl);
  String get timeRemainingLabel {
    final short = closesIn.trim();
    if (short.isNotEmpty && short != 'fim') {
      return short;
    }
    final label = closeLabel.trim();
    if (label.isNotEmpty) {
      return label;
    }
    return statusLabel;
  }

  int get engagementScore {
    final featuredBoost = isFeatured ? 1000000 : 0;
    return featuredBoost +
        (humanParticipants * 1000) +
        (humanVolumeGtl * 3) +
        (likeCount * 120) +
        (commentCount * 90) +
        (shareCount * 70) +
        viewCount;
  }

  factory Market.fromJson(Map<String, dynamic> json) {
    return Market(
      slug: safeString(json['slug']),
      title: safeString(json['title']),
      category: safeString(json['category']),
      subcategory: safeString(json['subcategory']),
      event: safeString(json['event']),
      kind: safeString(json['kind']),
      status: safeString(json['status']),
      statusLabel: safeString(json['status_label']),
      primaryOutcome: safeString(json['primary_outcome']),
      primaryProbability: safeInt(json['primary_probability']),
      primaryProbabilityExact: safeDouble(json['primary_probability_exact']),
      humanVolumeGtl: safeInt(json['human_volume_gtl']),
      humanParticipants: safeInt(json['human_participants']),
      commentCount: safeInt(json['comment_count']),
      likeCount: safeInt(json['market_like_count']),
      viewCount: safeInt(json['view_count']),
      shareCount: safeInt(json['share_count']),
      isFeatured: safeBool(json['is_featured']),
      closesIn: safeString(json['closes_in']),
      closeLabel: safeString(json['close_label']),
      imageUrl: safeString(json['image_url']),
      thumb: safeString(json['thumb']),
      thumbColor: safeString(json['thumb_color'], '#11151B'),
      summary: safeString(json['summary']),
      resolutionCriteria: safeString(json['resolution_criteria']),
      resolutionNote: safeString(json['resolution_note']),
      resolvedAtLabel: safeString(json['resolved_at_label']),
      viewerHasPrediction: safeBool(json['viewer_has_prediction']),
      viewerHasFavorite: safeBool(json['viewer_has_favorite']),
      viewerHasLike: safeBool(json['viewer_has_like']),
      options: ((json['options'] as List<dynamic>?) ?? <dynamic>[])
          .whereType<Map>()
          .map((item) => MarketOption.fromJson(Map<String, dynamic>.from(item)))
          .toList(),
      comments: ((json['comments'] as List<dynamic>?) ?? <dynamic>[])
          .whereType<Map>()
          .map(
            (item) => MarketComment.fromJson(Map<String, dynamic>.from(item)),
          )
          .toList(),
      sparklinePath: safeString(json['sparkline_path']),
      sparklineSeries:
          ((json['sparkline_series'] as List<dynamic>?) ?? <dynamic>[])
              .whereType<Map>()
              .map((item) => Map<String, dynamic>.from(item))
              .toList(),
    );
  }
}

class PredictionPreview {
  const PredictionPreview({
    required this.optionId,
    required this.stakeAmount,
    required this.probabilityExact,
    required this.estimatedReturn,
  });

  final int optionId;
  final int stakeAmount;
  final double probabilityExact;
  final int estimatedReturn;

  factory PredictionPreview.fromJson(Map<String, dynamic> json) {
    return PredictionPreview(
      optionId: safeInt(json['option_id']),
      stakeAmount: safeInt(json['stake_amount']),
      probabilityExact: safeDouble(json['probability_exact']),
      estimatedReturn: safeInt(json['estimated_return']),
    );
  }
}
