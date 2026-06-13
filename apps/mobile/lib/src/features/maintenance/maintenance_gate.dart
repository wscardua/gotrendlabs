import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_client.dart';
import '../../core/formatters.dart';
import '../../core/providers.dart';
import '../../theme.dart';
import '../../ui/gtl_components.dart';

const _fallbackMaintenanceMessage =
    'Estamos em manutenção no app para deixar sua experiência mais estável. Voltamos em breve.';

class BackendHealth {
  const BackendHealth({
    required this.status,
    required this.mobileMaintenanceEnabled,
    required this.mobileMaintenanceMessage,
    this.backendUnavailable = false,
  });

  final String status;
  final bool mobileMaintenanceEnabled;
  final String mobileMaintenanceMessage;
  final bool backendUnavailable;

  bool get isHealthy => status == 'ok' && !backendUnavailable;

  factory BackendHealth.fromJson(Map<String, dynamic> json) {
    final maintenance = json['maintenance'] is Map
        ? Map<String, dynamic>.from(json['maintenance'] as Map)
        : <String, dynamic>{};
    return BackendHealth(
      status: safeString(json['status'], 'degraded').toLowerCase(),
      mobileMaintenanceEnabled: safeBool(maintenance['mobile_enabled']),
      mobileMaintenanceMessage: safeString(
        maintenance['mobile_message'],
        _fallbackMaintenanceMessage,
      ),
    );
  }

  factory BackendHealth.unavailable() {
    return const BackendHealth(
      status: 'unavailable',
      mobileMaintenanceEnabled: true,
      mobileMaintenanceMessage:
          'Não conseguimos carregar o backend agora. Estamos verificando e logo voltaremos.',
      backendUnavailable: true,
    );
  }
}

class MaintenanceRepository {
  const MaintenanceRepository(this._api);

  final ApiClient _api;

  Future<BackendHealth> check() async {
    try {
      final json = await _api.getMap('/health');
      final health = BackendHealth.fromJson(json);
      if (!health.isHealthy) {
        return BackendHealth(
          status: health.status,
          mobileMaintenanceEnabled: true,
          mobileMaintenanceMessage: health.mobileMaintenanceMessage,
          backendUnavailable: true,
        );
      }
      return health;
    } catch (_) {
      return BackendHealth.unavailable();
    }
  }
}

final maintenanceRepositoryProvider = Provider<MaintenanceRepository>(
  (ref) => MaintenanceRepository(ref.watch(apiClientProvider)),
);

final maintenanceControllerProvider = FutureProvider<BackendHealth>((ref) {
  return ref.watch(maintenanceRepositoryProvider).check();
});

class MaintenanceGate extends ConsumerWidget {
  const MaintenanceGate({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final health = ref.watch(maintenanceControllerProvider);
    return health.when(
      loading: () => const MaintenanceLoadingScreen(),
      error: (_, _) => MaintenanceScreen(
        health: BackendHealth.unavailable(),
        onRetry: () => ref.invalidate(maintenanceControllerProvider),
      ),
      data: (value) {
        if (!value.isHealthy || value.mobileMaintenanceEnabled) {
          return MaintenanceScreen(
            health: value,
            onRetry: () => ref.invalidate(maintenanceControllerProvider),
          );
        }
        return child;
      },
    );
  }
}

class MaintenanceLoadingScreen extends StatelessWidget {
  const MaintenanceLoadingScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const GtlScreen(
      child: Center(
        child: SizedBox.square(
          dimension: 28,
          child: CircularProgressIndicator(strokeWidth: 2),
        ),
      ),
    );
  }
}

class MaintenanceScreen extends ConsumerWidget {
  const MaintenanceScreen({
    super.key,
    required this.health,
    required this.onRetry,
  });

  final BackendHealth health;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return GtlScreen(
      child: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            return SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: ConstrainedBox(
                constraints: BoxConstraints(
                  minHeight: constraints.maxHeight - 48,
                ),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    GtlSurface(
                      padding: const EdgeInsets.all(22),
                      borderColor: health.backendUnavailable
                          ? GtlColors.accentYellow.withValues(alpha: 0.50)
                          : GtlColors.accentBlue.withValues(alpha: 0.50),
                      glowColor: health.backendUnavailable
                          ? GtlColors.accentYellow
                          : GtlColors.accentBlue,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const GtlBrandMark(size: 54),
                          const SizedBox(height: 20),
                          GtlPill(
                            label: health.backendUnavailable
                                ? 'Backend indisponível'
                                : 'Manutenção mobile',
                            icon: health.backendUnavailable
                                ? Icons.cloud_off_outlined
                                : Icons.construction_outlined,
                            color: health.backendUnavailable
                                ? GtlColors.accentYellow
                                : GtlColors.accentBlue,
                            filled: true,
                          ),
                          const SizedBox(height: 18),
                          Text(
                            'Voltamos em breve',
                            style: Theme.of(context).textTheme.headlineMedium,
                          ),
                          const SizedBox(height: 10),
                          Text(
                            health.mobileMaintenanceMessage,
                            style: Theme.of(context).textTheme.bodyLarge,
                          ),
                          const SizedBox(height: 24),
                          FilledButton.icon(
                            onPressed: onRetry,
                            icon: const Icon(Icons.refresh),
                            label: const Text('Tentar novamente'),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}
