import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/providers.dart';
import '../auth/auth_controller.dart';

final performanceProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  ref.watch(authControllerProvider);
  final auth = ref.read(authControllerProvider);
  if (!auth.isAuthenticated) {
    return <String, dynamic>{};
  }
  return ref.read(apiClientProvider).getMap('/users/me/performance');
});
