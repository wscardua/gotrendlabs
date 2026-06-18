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
    required this.viewerPosition,
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
  final ViewerPositionSummary viewerPosition;
  final List<MarketOption> options;
  final List<MarketComment> comments;
  final String sparklinePath;
  final List<Map<String, dynamic>> sparklineSeries;

  bool get isOpen => status == 'open';
  bool get isResolved => status == 'resolved';
  bool get isLocked => status == 'locked';
  bool get viewerHasActivePosition => viewerPosition.hasPosition;
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
      viewerPosition: ViewerPositionSummary.fromJson(
        Map<String, dynamic>.from((json['viewer_position'] as Map?) ?? {}),
      ),
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

class ViewerPositionEntry {
  const ViewerPositionEntry({
    required this.id,
    required this.optionId,
    required this.optionLabel,
    required this.actionType,
    required this.positionSequence,
    required this.stakeAmount,
    required this.probabilityAtEntry,
    required this.potentialPayout,
    required this.createdAt,
    required this.status,
    this.supersededAt,
  });

  final int id;
  final int optionId;
  final String optionLabel;
  final String actionType;
  final int positionSequence;
  final int stakeAmount;
  final double probabilityAtEntry;
  final int potentialPayout;
  final String createdAt;
  final String status;
  final String? supersededAt;

  factory ViewerPositionEntry.fromJson(Map<String, dynamic> json) {
    return ViewerPositionEntry(
      id: safeInt(json['id']),
      optionId: safeInt(json['option_id']),
      optionLabel: safeString(json['option_label']),
      actionType: safeString(json['action_type'], 'initial'),
      positionSequence: safeInt(json['position_sequence'], 1),
      stakeAmount: safeInt(json['stake_amount']),
      probabilityAtEntry: safeDouble(json['probability_at_entry']),
      potentialPayout: safeInt(json['potential_payout']),
      createdAt: safeString(json['created_at']),
      status: safeString(json['status'], 'open'),
      supersededAt: json['superseded_at']?.toString(),
    );
  }
}

class ViewerPositionSummary {
  const ViewerPositionSummary({
    required this.hasPosition,
    this.optionId,
    required this.optionLabel,
    required this.activeStakeAmount,
    required this.potentialPayoutTotal,
    this.probabilityAtEntry,
    required this.positionCount,
    required this.reinforcementCount,
    required this.reinforcementRemaining,
    required this.reinforcementMaxCount,
    required this.revisionCount,
    required this.revisionRemaining,
    required this.revisionPenaltyPercent,
    required this.revisionPenaltyAmount,
    required this.revisionNewStakeAmount,
    required this.canReinforce,
    required this.canRevise,
    required this.reinforcementBlockedReason,
    required this.revisionBlockedReason,
    this.revisionCutoffAt,
    required this.activeEntries,
    required this.history,
  });

  final bool hasPosition;
  final int? optionId;
  final String optionLabel;
  final int activeStakeAmount;
  final int potentialPayoutTotal;
  final double? probabilityAtEntry;
  final int positionCount;
  final int reinforcementCount;
  final int reinforcementRemaining;
  final int reinforcementMaxCount;
  final int revisionCount;
  final int revisionRemaining;
  final int revisionPenaltyPercent;
  final int revisionPenaltyAmount;
  final int revisionNewStakeAmount;
  final bool canReinforce;
  final bool canRevise;
  final String reinforcementBlockedReason;
  final String revisionBlockedReason;
  final String? revisionCutoffAt;
  final List<ViewerPositionEntry> activeEntries;
  final List<ViewerPositionEntry> history;

  bool get hasActiveOption => optionId != null && optionId! > 0;

  factory ViewerPositionSummary.fromJson(Map<String, dynamic> json) {
    final rawOptionId = json['option_id'];
    final parsedOptionId = rawOptionId == null ? null : safeInt(rawOptionId);
    return ViewerPositionSummary(
      hasPosition: safeBool(json['has_position']),
      optionId: parsedOptionId == 0 ? null : parsedOptionId,
      optionLabel: safeString(json['option_label']),
      activeStakeAmount: safeInt(json['active_stake_amount']),
      potentialPayoutTotal: safeInt(json['potential_payout_total']),
      probabilityAtEntry: json['probability_at_entry'] == null
          ? null
          : safeDouble(json['probability_at_entry']),
      positionCount: safeInt(json['position_count']),
      reinforcementCount: safeInt(json['reinforcement_count']),
      reinforcementRemaining: safeInt(json['reinforcement_remaining']),
      reinforcementMaxCount: safeInt(json['reinforcement_max_count']),
      revisionCount: safeInt(json['revision_count']),
      revisionRemaining: safeInt(json['revision_remaining']),
      revisionPenaltyPercent: safeInt(json['revision_penalty_percent']),
      revisionPenaltyAmount: safeInt(json['revision_penalty_amount']),
      revisionNewStakeAmount: safeInt(json['revision_new_stake_amount']),
      canReinforce: safeBool(json['can_reinforce']),
      canRevise: safeBool(json['can_revise']),
      reinforcementBlockedReason: safeString(
        json['reinforcement_blocked_reason'],
      ),
      revisionBlockedReason: safeString(json['revision_blocked_reason']),
      revisionCutoffAt: json['revision_cutoff_at']?.toString(),
      activeEntries: _parsePositionEntries(json['active_entries']),
      history: _parsePositionEntries(json['history']),
    );
  }

  static List<ViewerPositionEntry> _parsePositionEntries(Object? value) {
    return ((value as List<dynamic>?) ?? <dynamic>[])
        .whereType<Map>()
        .map(
          (item) =>
              ViewerPositionEntry.fromJson(Map<String, dynamic>.from(item)),
        )
        .toList();
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

class PositionActionPreview {
  const PositionActionPreview({
    required this.optionId,
    required this.action,
    required this.stakeAmount,
    required this.activeStakeAmount,
    required this.activePositionCount,
    required this.penaltyAmount,
    required this.revisionPenaltyPercent,
    required this.newPositionStakeAmount,
    required this.positionTotalAfter,
    required this.probabilityExact,
    required this.estimatedReturn,
    required this.reinforcementRemaining,
    required this.revisionRemaining,
    required this.allowed,
    required this.blockedReason,
  });

  final int optionId;
  final String action;
  final int stakeAmount;
  final int activeStakeAmount;
  final int activePositionCount;
  final int penaltyAmount;
  final int revisionPenaltyPercent;
  final int newPositionStakeAmount;
  final int positionTotalAfter;
  final double probabilityExact;
  final int estimatedReturn;
  final int reinforcementRemaining;
  final int revisionRemaining;
  final bool allowed;
  final String blockedReason;

  bool matches({
    required String action,
    required int optionId,
    required int stakeAmount,
  }) {
    return this.action == action &&
        this.optionId == optionId &&
        this.stakeAmount == stakeAmount;
  }

  factory PositionActionPreview.fromJson(Map<String, dynamic> json) {
    return PositionActionPreview(
      optionId: safeInt(json['option_id']),
      action: safeString(json['action']),
      stakeAmount: safeInt(json['stake_amount']),
      activeStakeAmount: safeInt(json['active_stake_amount']),
      activePositionCount: safeInt(json['active_position_count']),
      penaltyAmount: safeInt(json['penalty_amount']),
      revisionPenaltyPercent: safeInt(json['revision_penalty_percent']),
      newPositionStakeAmount: safeInt(json['new_position_stake_amount']),
      positionTotalAfter: safeInt(json['position_total_after']),
      probabilityExact: safeDouble(json['probability_exact']),
      estimatedReturn: safeInt(json['estimated_return']),
      reinforcementRemaining: safeInt(json['reinforcement_remaining']),
      revisionRemaining: safeInt(json['revision_remaining']),
      allowed: safeBool(json['allowed']),
      blockedReason: safeString(json['blocked_reason']),
    );
  }
}

class PositionActionResult {
  const PositionActionResult({
    required this.optionId,
    required this.action,
    required this.stakeAmount,
    required this.penaltyAmount,
    required this.potentialPayout,
    required this.viewerPosition,
  });

  final int optionId;
  final String action;
  final int stakeAmount;
  final int penaltyAmount;
  final int potentialPayout;
  final ViewerPositionSummary viewerPosition;

  factory PositionActionResult.fromJson(Map<String, dynamic> json) {
    return PositionActionResult(
      optionId: safeInt(json['option_id']),
      action: safeString(json['action']),
      stakeAmount: safeInt(json['stake_amount']),
      penaltyAmount: safeInt(json['penalty_amount']),
      potentialPayout: safeInt(json['potential_payout']),
      viewerPosition: ViewerPositionSummary.fromJson(
        Map<String, dynamic>.from((json['viewer_position'] as Map?) ?? {}),
      ),
    );
  }
}
