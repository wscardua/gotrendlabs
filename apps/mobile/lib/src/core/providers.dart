import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'api_client.dart';
import 'mobile_update_state.dart';

final apiClientProvider = Provider<ApiClient>(
  (ref) => ApiClient(
    onAppUpdateRequired: (payload) {
      final info = MobileUpdateInfo.fromApiResponse(payload);
      if (info.updateRequired) {
        ref.read(mobileUpdateOverrideProvider.notifier).show(info);
      }
    },
  ),
);
