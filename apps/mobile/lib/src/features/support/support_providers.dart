import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/providers.dart';
import 'support_repository.dart';

final supportRepositoryProvider = Provider<SupportRepository>(
  (ref) => SupportRepository(ref.watch(apiClientProvider)),
);

final taxonomyProvider = FutureProvider<List<Map<String, dynamic>>>((
  ref,
) async {
  final json = await ref.read(apiClientProvider).getMap('/taxonomy');
  return ((json['categories'] as List<dynamic>?) ?? <dynamic>[])
      .whereType<Map>()
      .map((item) => Map<String, dynamic>.from(item))
      .where((category) => category['is_blocked'] != true)
      .toList();
});
