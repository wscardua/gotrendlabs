import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_client.dart';
import '../../theme.dart';
import '../../ui/gtl_components.dart';
import '../auth/auth_controller.dart';
import '../auth/login_sheet.dart';
import '../push/push_controller.dart';

class AlertsScreen extends ConsumerWidget {
  const AlertsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authControllerProvider);
    if (!auth.isAuthenticated) {
      return GtlScreen(
        child: GtlStatePanel(
          icon: Icons.notifications_none,
          title: 'Alertas pessoais',
          body:
              'Entre para ver alertas in-app de mercados favoritos, previsões e resoluções.',
          action: FilledButton(
            onPressed: () => showLoginSheet(context),
            child: const Text('Entrar'),
          ),
        ),
      );
    }
    final notifications = ref.watch(notificationsProvider);
    return GtlScreen(
      child: notifications.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) => GtlStatePanel(
          icon: Icons.cloud_off,
          title: 'Alertas indisponíveis',
          body: ApiFailure.fromObject(error).message,
          color: GtlColors.accentYellow,
        ),
        data: (items) => ListView(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
          children: [
            const GtlEditorialHeader(
              kicker: 'Central in-app',
              title: 'Alertas',
              body: 'Favoritos, previsões e resoluções em um só fluxo.',
            ),
            const SizedBox(height: 12),
            _PushStatusPanel(ref: ref),
            const SizedBox(height: 12),
            if (items.isEmpty)
              const GtlSurface(
                child: GtlEditorialHeader(
                  kicker: 'Sem sinal novo',
                  title: 'Nenhum alerta por enquanto',
                  body:
                      'Quando seus mercados mudarem, o resumo aparece nesta central.',
                  icon: Icons.done_all,
                ),
              )
            else
              for (final item in items)
                Padding(
                  padding: const EdgeInsets.only(bottom: 10),
                  child: GtlSurface(
                    padding: EdgeInsets.zero,
                    child: ListTile(
                      leading: const Icon(Icons.bolt_outlined),
                      title: Text(
                        (item as Map)['title']?.toString() ?? 'Alerta',
                      ),
                      subtitle: Text(item['body']?.toString() ?? ''),
                    ),
                  ),
                ),
          ],
        ),
      ),
    );
  }
}

class _PushStatusPanel extends StatelessWidget {
  const _PushStatusPanel({required this.ref});

  final WidgetRef ref;

  @override
  Widget build(BuildContext context) {
    final push = ref.watch(pushControllerProvider);
    final activeDevices = push.devices
        .where((device) => device.isActive && device.pushEnabled)
        .length;
    final isNoop = push.status == 'noop' || push.status == 'idle';
    return GtlSurface(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          GtlEditorialHeader(
            kicker: 'Push mobile',
            title: isNoop
                ? 'Preparado para Firebase'
                : activeDevices > 0
                    ? 'Dispositivo registrado'
                    : 'Sem dispositivo ativo',
            body: isNoop
                ? 'A interface está pronta, mas o provider Firebase ainda não foi configurado.'
                : push.error.isNotEmpty
                    ? push.error
                    : 'Você pode consultar e revogar dispositivos sem sair da central de alertas.',
            icon: Icons.notifications_active_outlined,
          ),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              OutlinedButton.icon(
                onPressed: () => ref.read(pushControllerProvider.notifier).load(),
                icon: const Icon(Icons.sync),
                label: const Text('Atualizar push'),
              ),
              for (final device in push.devices.where(
                (device) => device.isActive && device.pushEnabled,
              ))
                OutlinedButton.icon(
                  onPressed: () => ref
                      .read(pushControllerProvider.notifier)
                      .revokeDevice(device.id),
                  icon: const Icon(Icons.notifications_off_outlined),
                  label: Text('Revogar ${device.platform}'),
                ),
            ],
          ),
        ],
      ),
    );
  }
}
