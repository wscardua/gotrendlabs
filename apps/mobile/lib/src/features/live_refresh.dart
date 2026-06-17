import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'auth/auth_controller.dart';
import 'markets/markets_providers.dart';

void invalidateMarketData(WidgetRef ref, {String? slug}) {
  ref.invalidate(marketsProvider);
  if (slug != null && slug.isNotEmpty) {
    ref.invalidate(marketDetailProvider(slug));
  }
}

void invalidateWalletData(WidgetRef ref) {
  ref.invalidate(walletProvider);
  ref.invalidate(ledgerProvider);
  ref.invalidate(walletRechargeRequestsProvider);
}

void invalidateNotifications(WidgetRef ref) {
  ref.invalidate(notificationsProvider);
}

void invalidateRankingData(WidgetRef ref, {RankingFilters? filters}) {
  if (filters == null) {
    ref.invalidate(rankingPayloadProvider);
  } else {
    ref.invalidate(rankingPayloadProvider(filters));
  }
  ref.invalidate(rankingProvider);
}

void invalidateLiveData(WidgetRef ref, {String? marketSlug}) {
  invalidateMarketData(ref, slug: marketSlug);
  invalidateRankingData(ref);
  if (ref.read(authControllerProvider).isAuthenticated) {
    invalidateWalletData(ref);
    invalidateNotifications(ref);
  }
}

Future<void> refreshMarkets(WidgetRef ref) async {
  invalidateMarketData(ref);
  await _ignoreRefreshError(ref.read(marketsProvider.future));
}

Future<void> refreshMarketDetail(WidgetRef ref, String slug) async {
  invalidateMarketData(ref, slug: slug);
  await Future.wait([
    _ignoreRefreshError(ref.read(marketsProvider.future)),
    _ignoreRefreshError(ref.read(marketDetailProvider(slug).future)),
  ]);
}

Future<void> refreshWalletData(WidgetRef ref) async {
  if (!ref.read(authControllerProvider).isAuthenticated) {
    return;
  }
  invalidateWalletData(ref);
  await Future.wait([
    _ignoreRefreshError(ref.read(walletProvider.future)),
    _ignoreRefreshError(ref.read(ledgerProvider.future)),
    _ignoreRefreshError(ref.read(walletRechargeRequestsProvider.future)),
  ]);
}

Future<void> refreshRankingData(WidgetRef ref, RankingFilters filters) async {
  invalidateRankingData(ref, filters: filters);
  await _ignoreRefreshError(ref.read(rankingPayloadProvider(filters).future));
}

Future<void> _ignoreRefreshError(Future<Object?> future) async {
  try {
    await future;
  } catch (_) {
    // A tela que observa o provider renderiza o erro; refresh manual só aguarda.
  }
}
