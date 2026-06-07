import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_client.dart';
import '../../core/formatters.dart';
import '../../core/providers.dart';
import '../../theme.dart';
import '../auth/auth_controller.dart';
import '../auth/login_sheet.dart';

class WalletScreen extends ConsumerStatefulWidget {
  const WalletScreen({super.key});

  @override
  ConsumerState<WalletScreen> createState() => _WalletScreenState();
}

class _WalletScreenState extends ConsumerState<WalletScreen> {
  bool _requestingRecharge = false;

  @override
  Widget build(BuildContext context) {
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
                    final recharge = ref.watch(walletRechargeRequestsProvider);
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
                        recharge.when(
                          loading: () => const _RechargeLoadingCard(),
                          error: (error, stack) =>
                              _RechargeErrorCard(message: error.toString()),
                          data: (data) => _RechargeCard(
                            data: data,
                            requesting: _requestingRecharge,
                            onRequest: _requestRecharge,
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

  Future<void> _requestRecharge() async {
    setState(() => _requestingRecharge = true);
    try {
      await ref
          .read(apiClientProvider)
          .postMap('/users/me/wallet/recharge-requests');
      ref.invalidate(walletRechargeRequestsProvider);
      ref.invalidate(ledgerProvider);
      ref.invalidate(walletProvider);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Solicitação de recarga enviada para análise.'),
          ),
        );
      }
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(ApiFailure.fromObject(error).message)),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _requestingRecharge = false);
      }
    }
  }
}

class _RechargeCard extends StatelessWidget {
  const _RechargeCard({
    required this.data,
    required this.requesting,
    required this.onRequest,
  });

  final Map<String, dynamic> data;
  final bool requesting;
  final VoidCallback onRequest;

  @override
  Widget build(BuildContext context) {
    final requests = ((data['requests'] as List<dynamic>?) ?? <dynamic>[])
        .whereType<Map>()
        .map((item) => Map<String, dynamic>.from(item))
        .toList();
    final pending = _pendingRequest(requests);
    final eligible = safeBool(data['eligible']);
    final available = safeInt(data['available_gtl']);
    final minBalance = safeInt(data['min_balance_gtl'], 100);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Fila Admin Ops'),
                      SizedBox(height: 4),
                      Text(
                        'Recarga controlada',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                    ],
                  ),
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    const Text('Crédito livre'),
                    Text(
                      formatGtl(available),
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(
              'Crédito educativo sob revisão administrativa, disponível quando seu crédito livre estiver em até ${formatGtl(minBalance)}.',
            ),
            const SizedBox(height: 12),
            const Row(
              children: [
                _RechargeStep(number: '1', label: 'Solicitação'),
                _RechargeStep(number: '2', label: 'Revisão'),
                _RechargeStep(number: '3', label: 'Crédito'),
              ],
            ),
            const SizedBox(height: 12),
            if (pending != null) ...[
              _RechargeStateBox(
                title: 'Status',
                value: 'Em análise',
                secondaryTitle: 'Enviada',
                secondaryValue:
                    pending['created_at_label']?.toString() ?? 'Agora',
              ),
              const SizedBox(height: 10),
              FilledButton.icon(
                onPressed: null,
                icon: const Icon(Icons.hourglass_top),
                label: const Text('Em análise'),
              ),
            ] else if (!eligible) ...[
              _RechargeStateBox(
                title: 'Elegibilidade',
                value: 'Crédito acima do limite',
                secondaryTitle: 'Limite atual',
                secondaryValue: formatGtl(minBalance),
              ),
              const SizedBox(height: 10),
              FilledButton.icon(
                onPressed: null,
                icon: const Icon(Icons.lock_outline),
                label: const Text('Recarga indisponível'),
              ),
            ] else ...[
              FilledButton.icon(
                onPressed: requesting ? null : onRequest,
                icon: requesting
                    ? const SizedBox.square(
                        dimension: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.add_card_outlined),
                label: const Text('Solicitar recarga educativa'),
              ),
            ],
            if (requests.isNotEmpty) ...[
              const SizedBox(height: 14),
              Row(
                children: [
                  const Expanded(child: Text('Histórico')),
                  Text(
                    'últimas 3',
                    style: Theme.of(context).textTheme.labelMedium,
                  ),
                ],
              ),
              const SizedBox(height: 8),
              for (final request in requests.take(3))
                _RechargeHistoryRow(request: request),
            ],
          ],
        ),
      ),
    );
  }

  Map<String, dynamic>? _pendingRequest(List<Map<String, dynamic>> requests) {
    for (final request in requests) {
      if (request['status'] == 'pending') {
        return request;
      }
    }
    return null;
  }
}

class _RechargeStep extends StatelessWidget {
  const _RechargeStep({required this.number, required this.label});

  final String number;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: DecoratedBox(
        decoration: BoxDecoration(
          border: Border.all(color: GtlColors.border),
          borderRadius: BorderRadius.circular(8),
          color: GtlColors.surfaceElevated,
        ),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 10),
          child: Column(
            children: [
              Text(number, style: const TextStyle(fontWeight: FontWeight.w900)),
              const SizedBox(height: 4),
              FittedBox(child: Text(label)),
            ],
          ),
        ),
      ),
    );
  }
}

class _RechargeStateBox extends StatelessWidget {
  const _RechargeStateBox({
    required this.title,
    required this.value,
    required this.secondaryTitle,
    required this.secondaryValue,
  });

  final String title;
  final String value;
  final String secondaryTitle;
  final String secondaryValue;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: GtlColors.surfaceElevated,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: GtlColors.border),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            Expanded(
              child: _StateMetric(label: title, value: value),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _StateMetric(
                label: secondaryTitle,
                value: secondaryValue,
                alignEnd: true,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _StateMetric extends StatelessWidget {
  const _StateMetric({
    required this.label,
    required this.value,
    this.alignEnd = false,
  });

  final String label;
  final String value;
  final bool alignEnd;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: alignEnd
          ? CrossAxisAlignment.end
          : CrossAxisAlignment.start,
      children: [
        Text(label, style: Theme.of(context).textTheme.labelMedium),
        const SizedBox(height: 4),
        Text(
          value,
          textAlign: alignEnd ? TextAlign.end : TextAlign.start,
          style: const TextStyle(fontWeight: FontWeight.w900),
        ),
      ],
    );
  }
}

class _RechargeHistoryRow extends StatelessWidget {
  const _RechargeHistoryRow({required this.request});

  final Map<String, dynamic> request;

  @override
  Widget build(BuildContext context) {
    final amount = request['amount_gtl'];
    final amountLabel = amount == null ? '-' : formatGtl(safeInt(amount));
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          Expanded(child: Text(request['created_at_label']?.toString() ?? '')),
          Text(
            request['status_label']?.toString() ??
                request['status']?.toString() ??
                '',
          ),
          const SizedBox(width: 12),
          SizedBox(
            width: 72,
            child: Text(amountLabel, textAlign: TextAlign.end),
          ),
        ],
      ),
    );
  }
}

class _RechargeLoadingCard extends StatelessWidget {
  const _RechargeLoadingCard();

  @override
  Widget build(BuildContext context) {
    return const Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Center(child: CircularProgressIndicator()),
      ),
    );
  }
}

class _RechargeErrorCard extends StatelessWidget {
  const _RechargeErrorCard({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Text(
          message,
          style: const TextStyle(color: GtlColors.accentRed),
        ),
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
