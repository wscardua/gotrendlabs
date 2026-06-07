import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/formatters.dart';
import '../../theme.dart';
import '../auth/auth_controller.dart';
import '../auth/login_sheet.dart';

class WalletScreen extends ConsumerWidget {
  const WalletScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authControllerProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Wallet')),
      body: !auth.isAuthenticated
          ? _AuthRequired(onLogin: () => showLoginSheet(context))
          : ref
                .watch(ledgerProvider)
                .when(
                  loading: () =>
                      const Center(child: CircularProgressIndicator()),
                  error: (error, stack) =>
                      Center(child: Text(error.toString())),
                  data: (ledger) {
                    final wallet = Map<String, dynamic>.from(
                      (ledger['wallet'] as Map?) ?? const {},
                    );
                    final entries =
                        (ledger['entries'] as List<dynamic>?) ?? <dynamic>[];
                    return ListView(
                      padding: const EdgeInsets.all(16),
                      children: [
                        Card(
                          child: Padding(
                            padding: const EdgeInsets.all(18),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text('Saldo educativo'),
                                const SizedBox(height: 8),
                                Text(
                                  formatGtl(safeInt(wallet['available_gtl'])),
                                  style: Theme.of(
                                    context,
                                  ).textTheme.displaySmall,
                                ),
                                const SizedBox(height: 8),
                                Text(
                                  'Bloqueado: ${formatGtl(safeInt(wallet['locked_gtl']))}',
                                ),
                                const SizedBox(height: 8),
                                const Text(
                                  'GT₵ não representa dinheiro real, depósito, saque ou investimento.',
                                ),
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(height: 12),
                        Text(
                          'Extrato',
                          style: Theme.of(context).textTheme.titleLarge,
                        ),
                        const SizedBox(height: 8),
                        if (entries.isEmpty)
                          const Card(
                            child: Padding(
                              padding: EdgeInsets.all(16),
                              child: Text('Sem lançamentos recentes.'),
                            ),
                          )
                        else
                          for (final entry in entries.take(20))
                            Card(
                              child: ListTile(
                                title: Text(
                                  (entry as Map)['entry_type_label']
                                          ?.toString() ??
                                      entry['entry_type']?.toString() ??
                                      'Movimento',
                                ),
                                subtitle: Text(
                                  entry['description']?.toString() ?? '',
                                ),
                                trailing: Text(
                                  formatGtl(safeInt(entry['amount'])),
                                ),
                              ),
                            ),
                      ],
                    );
                  },
                ),
    );
  }
}

class _AuthRequired extends StatelessWidget {
  const _AuthRequired({required this.onLogin});

  final VoidCallback onLogin;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.lock_outline, color: GtlColors.accentYellow),
            const SizedBox(height: 12),
            const Text('Entre para ver saldo educativo, extrato e perfil.'),
            const SizedBox(height: 12),
            FilledButton(onPressed: onLogin, child: const Text('Entrar')),
          ],
        ),
      ),
    );
  }
}
