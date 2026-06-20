import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/api_client.dart';
import '../../core/formatters.dart';
import '../../core/mobile_update_state.dart';
import '../../core/providers.dart';
import '../../theme.dart';
import '../../ui/gtl_components.dart';

export '../../core/mobile_update_state.dart';

const _fallbackMaintenanceMessage =
    'Estamos em manutenção no app para deixar sua experiência mais estável. Voltamos em breve.';

class BackendHealth {
  const BackendHealth({
    required this.status,
    required this.mobileMaintenanceEnabled,
    required this.mobileMaintenanceMessage,
    this.backendUnavailable = false,
    this.updateRequired = false,
    this.updateAvailable = false,
    this.currentAppVersion = '',
    this.currentAppBuild,
    this.latestAndroidVersion = '',
    this.latestAndroidBuild = 0,
    this.downloadUrl = '',
    this.updateRequiredMessage =
        'Atualize o app para continuar usando o GoTrendLabs.',
  });

  final String status;
  final bool mobileMaintenanceEnabled;
  final String mobileMaintenanceMessage;
  final bool backendUnavailable;
  final bool updateRequired;
  final bool updateAvailable;
  final String currentAppVersion;
  final int? currentAppBuild;
  final String latestAndroidVersion;
  final int latestAndroidBuild;
  final String downloadUrl;
  final String updateRequiredMessage;

  bool get isHealthy => status == 'ok' && !backendUnavailable;
  MobileUpdateInfo get mobileUpdateInfo => MobileUpdateInfo(
    updateRequired: updateRequired,
    updateAvailable: updateAvailable,
    currentAppVersion: currentAppVersion,
    currentAppBuild: currentAppBuild,
    latestAndroidVersion: latestAndroidVersion,
    latestAndroidBuild: latestAndroidBuild,
    downloadUrl: downloadUrl,
    updateRequiredMessage: updateRequiredMessage,
  );

  factory BackendHealth.fromJson(Map<String, dynamic> json) {
    final maintenance = json['maintenance'] is Map
        ? Map<String, dynamic>.from(json['maintenance'] as Map)
        : <String, dynamic>{};
    final mobile = json['mobile'] is Map
        ? Map<String, dynamic>.from(json['mobile'] as Map)
        : <String, dynamic>{};
    return BackendHealth(
      status: safeString(json['status'], 'degraded').toLowerCase(),
      mobileMaintenanceEnabled: safeBool(maintenance['mobile_enabled']),
      mobileMaintenanceMessage: safeString(
        maintenance['mobile_message'],
        _fallbackMaintenanceMessage,
      ),
      updateRequired: safeBool(mobile['update_required']),
      updateAvailable: safeBool(mobile['update_available']),
      currentAppVersion: safeString(mobile['current_app_version']),
      currentAppBuild: mobile['current_app_build'] == null
          ? null
          : safeInt(mobile['current_app_build']),
      latestAndroidVersion: safeString(mobile['latest_android_version']),
      latestAndroidBuild: safeInt(mobile['latest_android_build']),
      downloadUrl: safeString(mobile['download_url']),
      updateRequiredMessage: safeString(
        mobile['update_required_message'],
        'Atualize o app para continuar usando o GoTrendLabs.',
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
      if (health.updateRequired) {
        return health;
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

class MaintenanceGate extends ConsumerStatefulWidget {
  const MaintenanceGate({super.key, required this.child});

  final Widget child;

  @override
  ConsumerState<MaintenanceGate> createState() => _MaintenanceGateState();
}

class _MaintenanceGateState extends ConsumerState<MaintenanceGate>
    with WidgetsBindingObserver {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      ref.invalidate(maintenanceControllerProvider);
    }
  }

  @override
  Widget build(BuildContext context) {
    final updateOverride = ref.watch(mobileUpdateOverrideProvider);
    if (updateOverride != null && updateOverride.updateRequired) {
      return RequiredUpdateScreen(
        info: updateOverride,
        onRetry: () {
          ref.read(mobileUpdateOverrideProvider.notifier).clear();
          ref.invalidate(maintenanceControllerProvider);
        },
      );
    }
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
        if (value.updateRequired) {
          return RequiredUpdateScreen(
            info: value.mobileUpdateInfo,
            onRetry: () => ref.invalidate(maintenanceControllerProvider),
          );
        }
        return widget.child;
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

class RequiredUpdateScreen extends ConsumerWidget {
  const RequiredUpdateScreen({
    super.key,
    required this.info,
    required this.onRetry,
  });

  final MobileUpdateInfo info;
  final VoidCallback onRetry;

  Future<void> _openDownload() async {
    final uri = Uri.tryParse(info.downloadUrl);
    if (uri == null) {
      return;
    }
    await launchUrl(uri, mode: LaunchMode.externalApplication);
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final installed = [
      if (info.currentAppVersion.isNotEmpty) info.currentAppVersion,
      if (info.currentAppBuild != null) 'build ${info.currentAppBuild}',
    ].join(' · ');
    final latest = [
      if (info.latestAndroidVersion.isNotEmpty) info.latestAndroidVersion,
      if (info.latestAndroidBuild > 0) 'build ${info.latestAndroidBuild}',
    ].join(' · ');
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
                      borderColor: GtlColors.accentYellow.withValues(
                        alpha: 0.50,
                      ),
                      glowColor: GtlColors.accentYellow,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const GtlBrandMark(size: 54),
                          const SizedBox(height: 20),
                          const GtlPill(
                            label: 'Atualização obrigatória',
                            icon: Icons.system_update_alt_outlined,
                            color: GtlColors.accentYellow,
                            filled: true,
                          ),
                          const SizedBox(height: 18),
                          Text(
                            'Atualize para continuar',
                            style: Theme.of(context).textTheme.headlineMedium,
                          ),
                          const SizedBox(height: 10),
                          Text(
                            info.updateRequiredMessage,
                            style: Theme.of(context).textTheme.bodyLarge,
                          ),
                          const SizedBox(height: 18),
                          if (installed.isNotEmpty)
                            _UpdateInfoRow(
                              label: 'Instalada',
                              value: installed,
                            ),
                          if (latest.isNotEmpty)
                            _UpdateInfoRow(label: 'Disponível', value: latest),
                          const SizedBox(height: 24),
                          FilledButton.icon(
                            onPressed: info.downloadUrl.isEmpty
                                ? null
                                : _openDownload,
                            icon: const Icon(Icons.open_in_new),
                            label: const Text('Atualizar'),
                          ),
                          const SizedBox(height: 10),
                          OutlinedButton.icon(
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

class _UpdateInfoRow extends StatelessWidget {
  const _UpdateInfoRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 8),
      child: Row(
        children: [
          SizedBox(
            width: 92,
            child: Text(label, style: Theme.of(context).textTheme.labelLarge),
          ),
          Expanded(
            child: Text(value, style: Theme.of(context).textTheme.bodyMedium),
          ),
        ],
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
