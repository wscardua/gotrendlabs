import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_client.dart';
import '../../core/formatters.dart';
import '../../core/providers.dart';
import '../../theme.dart';
import '../../ui/gtl_components.dart';
import '../auth/auth_controller.dart';
import '../auth/login_sheet.dart';
import '../live_refresh.dart';

class WalletScreen extends ConsumerStatefulWidget {
  const WalletScreen({super.key});

  @override
  ConsumerState<WalletScreen> createState() => _WalletScreenState();
}

class _WalletScreenState extends ConsumerState<WalletScreen> {
  bool _requestingRecharge = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) {
        invalidateWalletData(ref);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Wallet')),
      body: GtlScreen(
        child: !auth.isAuthenticated
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
                      final recharge = ref.watch(
                        walletRechargeRequestsProvider,
                      );
                      return RefreshIndicator(
                        onRefresh: () => refreshWalletData(ref),
                        child: ListView(
                          physics: const AlwaysScrollableScrollPhysics(),
                          padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
                          children: [
                            _WalletBalanceHero(
                              availableGtl: safeInt(wallet['available_gtl']),
                              lockedGtl: safeInt(wallet['locked_gtl']),
                            ),
                            const SizedBox(height: 12),
                            const GtlSectionTitle(
                              title: 'Recarga educativa',
                              subtitle:
                                  'Solicitação controlada quando elegível',
                            ),
                            const SizedBox(height: 8),
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
                            const GtlSectionTitle(
                              title: 'Extrato',
                              subtitle:
                                  'Movimentos recentes conciliados pela API',
                            ),
                            const SizedBox(height: 8),
                            if (entries.isEmpty)
                              const GtlSurface(
                                child: GtlEditorialHeader(
                                  kicker: 'Histórico',
                                  title: 'Sem lançamentos recentes',
                                  body:
                                      'Quando houver reservas, resultados ou recargas, eles aparecem aqui.',
                                  icon: Icons.receipt_long,
                                ),
                              )
                            else
                              for (final entry in entries.take(20))
                                Padding(
                                  padding: const EdgeInsets.only(bottom: 10),
                                  child: GtlSurface(
                                    padding: EdgeInsets.zero,
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
                                ),
                          ],
                        ),
                      );
                    },
                  ),
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

class _WalletBalanceHero extends StatelessWidget {
  const _WalletBalanceHero({
    required this.availableGtl,
    required this.lockedGtl,
  });

  final int availableGtl;
  final int lockedGtl;

  @override
  Widget build(BuildContext context) {
    return GtlSurface(
      glowColor: GtlColors.accentCyan,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const GtlEditorialHeader(
            kicker: 'Wallet',
            title: 'Sua carteira',
            body:
                'GT₵ não representa dinheiro real, depósito, saque ou investimento.',
            icon: Icons.account_balance_wallet_outlined,
          ),
          const SizedBox(height: 16),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: GtlMetricTile(
                  label: 'Disponível',
                  value: formatGtl(availableGtl),
                  icon: Icons.savings_outlined,
                  color: GtlColors.accentGreen,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: GtlMetricTile(
                  label: 'Bloqueado',
                  value: formatGtl(lockedGtl),
                  icon: Icons.lock_clock,
                  color: GtlColors.accentYellow,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            'O valor bloqueado representa GT₵ reservado em posições abertas.',
            style: Theme.of(
              context,
            ).textTheme.bodySmall?.copyWith(color: GtlColors.textSecondary),
          ),
        ],
      ),
    );
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

    return GtlSurface(
      color: GtlColors.surfaceGlass,
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
        color: GtlColors.surfaceInk,
        borderRadius: BorderRadius.circular(GtlRadii.medium),
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
    return const GtlSurface(child: Center(child: CircularProgressIndicator()));
  }
}

class _RechargeErrorCard extends StatelessWidget {
  const _RechargeErrorCard({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return GtlSurface(
      child: Text(message, style: const TextStyle(color: GtlColors.accentRed)),
    );
  }
}

class _AuthRequired extends StatelessWidget {
  const _AuthRequired({required this.onLogin});

  final VoidCallback onLogin;

  @override
  Widget build(BuildContext context) {
    return GtlStatePanel(
      icon: Icons.lock_outline,
      title: 'Wallet protegida',
      body: 'Entre para ver saldo educativo, extrato e perfil.',
      color: GtlColors.accentYellow,
      action: FilledButton(onPressed: onLogin, child: const Text('Entrar')),
    );
  }
}
