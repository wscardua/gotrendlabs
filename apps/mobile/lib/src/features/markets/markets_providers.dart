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

final rankingProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final json = await ref.read(apiClientProvider).getMap('/rankings');
  return ((json['rows'] as List<dynamic>?) ?? <dynamic>[])
      .whereType<Map>()
      .map((item) => Map<String, dynamic>.from(item))
      .toList();
});
