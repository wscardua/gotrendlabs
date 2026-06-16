import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api_client.dart';
import '../../theme.dart';
import '../../ui/gtl_components.dart';
import '../auth/auth_controller.dart';
import '../auth/login_sheet.dart';

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
                    child: Material(
                      color: Colors.transparent,
                      child: ListTile(
                        leading: const Icon(Icons.bolt_outlined),
                        title: Text(
                          (item as Map)['title']?.toString() ?? 'Alerta',
                        ),
                        subtitle: Text(item['body']?.toString() ?? ''),
                        trailing: _notificationRoute(item) == null
                            ? null
                            : const Icon(Icons.chevron_right),
                        onTap: _notificationRoute(item) == null
                            ? null
                            : () => context.push(_notificationRoute(item)!),
                      ),
                    ),
                  ),
                ),
          ],
        ),
      ),
    );
  }
}

String? _notificationRoute(Map item) {
  final eventType = item['event_type']?.toString() ?? '';
  final marketSlug = item['market_slug']?.toString().trim() ?? '';
  if (marketSlug.isNotEmpty) {
    return Uri(
      path: '/markets/$marketSlug',
      queryParameters: eventType == 'market_comment'
          ? {'tab': 'community'}
          : null,
    ).toString();
  }
  if (eventType == 'wallet_credit') {
    return '/wallet';
  }
  if (eventType == 'badge_awarded') {
    return '/badges';
  }
  return null;
}
