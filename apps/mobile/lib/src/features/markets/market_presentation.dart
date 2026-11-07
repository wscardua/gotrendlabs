import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'market_models.dart';

// Presentation time only; lifecycle remains authoritative in the API.
final marketClockProvider = Provider<DateTime Function()>(
  (ref) => DateTime.now,
);

final marketIsNewProvider = Provider.autoDispose.family<bool, Market>((
  ref,
  market,
) {
  final now = ref.watch(marketClockProvider)();
  final created = DateTime.tryParse(market.createdAt);
  if (market.isOpen && created != null) {
    final nextChange = created.isAfter(now)
        ? created
        : created.add(const Duration(hours: 48));
    if (nextChange.isAfter(now)) {
      final timer = Timer(nextChange.difference(now), ref.invalidateSelf);
      ref.onDispose(timer.cancel);
    }
  }
  return market.isNewAt(now);
});
