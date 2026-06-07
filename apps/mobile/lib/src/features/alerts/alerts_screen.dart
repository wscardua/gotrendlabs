import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../auth/auth_controller.dart';
import '../auth/login_sheet.dart';

class AlertsScreen extends ConsumerWidget {
  const AlertsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authControllerProvider);
    if (!auth.isAuthenticated) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.notifications_none, size: 42),
              const SizedBox(height: 12),
              const Text(
                'Entre para ver alertas in-app de mercados favoritos, previsões e resoluções.',
              ),
              const SizedBox(height: 12),
              FilledButton(
                onPressed: () => showLoginSheet(context),
                child: const Text('Entrar'),
              ),
            ],
          ),
        ),
      );
    }
    final notifications = ref.watch(notificationsProvider);
    return notifications.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (error, stack) => Center(child: Text(error.toString())),
      data: (items) => ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text('Alertas', style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: 12),
          if (items.isEmpty)
            const Card(
              child: Padding(
                padding: EdgeInsets.all(16),
                child: Text('Nenhum alerta por enquanto.'),
              ),
            )
          else
            for (final item in items)
              Card(
                child: ListTile(
                  title: Text((item as Map)['title']?.toString() ?? 'Alerta'),
                  subtitle: Text(item['body']?.toString() ?? ''),
                ),
              ),
        ],
      ),
    );
  }
}
