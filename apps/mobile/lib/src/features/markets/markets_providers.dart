import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/providers.dart';
import '../auth/auth_controller.dart';
import 'market_models.dart';
import 'markets_repository.dart';

final marketsRepositoryProvider = Provider<MarketsRepository>(
  (ref) => MarketsRepository(ref.watch(apiClientProvider)),
);

final marketsProvider = FutureProvider<List<Market>>((ref) async {
  ref.watch(authControllerProvider);
  return ref.read(marketsRepositoryProvider).listMarkets();
});

final marketDetailProvider = FutureProvider.family<Market, String>((
  ref,
  slug,
) async {
  ref.watch(authControllerProvider);
  return ref.read(marketsRepositoryProvider).detail(slug);
});

class RankingFilters {
  const RankingFilters({
    this.category = '',
    this.subcategory = '',
    this.event = '',
  });

  final String category;
  final String subcategory;
  final String event;

  @override
  bool operator ==(Object other) {
    return other is RankingFilters &&
        other.category == category &&
        other.subcategory == subcategory &&
        other.event == event;
  }

  @override
  int get hashCode => Object.hash(category, subcategory, event);
}

final rankingPayloadProvider =
    FutureProvider.family<Map<String, dynamic>, RankingFilters>((
      ref,
      filters,
    ) async {
      return ref
          .read(apiClientProvider)
          .getMap(
            '/rankings',
            query: {
              if (filters.category.isNotEmpty) 'category': filters.category,
              if (filters.subcategory.isNotEmpty)
                'subcategory': filters.subcategory,
              if (filters.event.isNotEmpty) 'event': filters.event,
            },
          );
    });

final rankingProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final json = await ref.watch(
    rankingPayloadProvider(const RankingFilters()).future,
  );
  return ((json['rows'] as List<dynamic>?) ?? <dynamic>[])
      .whereType<Map>()
      .map((item) => Map<String, dynamic>.from(item))
      .toList();
});
