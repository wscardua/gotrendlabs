import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_client.dart';
import '../../core/formatters.dart';
import '../../theme.dart';
import '../auth/auth_controller.dart';
import '../auth/login_sheet.dart';
import 'market_models.dart';
import 'markets_providers.dart';

class PredictionTicket extends ConsumerStatefulWidget {
  const PredictionTicket({super.key, required this.market});

  final Market market;

  @override
  ConsumerState<PredictionTicket> createState() => _PredictionTicketState();
}

class _PredictionTicketState extends ConsumerState<PredictionTicket> {
  int? _optionId;
  int _stake = 10;
  PredictionPreview? _preview;
  String? _error;
  bool _busy = false;

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);
    final market = widget.market;
    final blocked = !market.isOpen || market.viewerHasPrediction;
    final blockedMessage = market.viewerHasPrediction
        ? 'Você já registrou uma previsão neste mercado.'
        : market.isOpen
        ? ''
        : 'Este mercado está ${market.statusLabel.toLowerCase()} e não aceita novas previsões.';

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              'Ticket de previsão',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 6),
            const Text(
              'Escolha uma opção explicitamente. O preview e a criação vêm da FastAPI.',
            ),
            const SizedBox(height: 12),
            for (final option in market.options)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: ChoiceChip(
                  selected: _optionId == option.id,
                  onSelected: blocked
                      ? null
                      : (_) => setState(() => _optionId = option.id),
                  label: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Flexible(
                        child: Text(
                          option.label,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(formatProbability(option.probability)),
                    ],
                  ),
                ),
              ),
            if (blocked) ...[
              const SizedBox(height: 8),
              Text(
                blockedMessage,
                style: const TextStyle(color: GtlColors.accentYellow),
              ),
            ] else ...[
              Row(
                children: [
                  const Text('Stake'),
                  Expanded(
                    child: Slider(
                      min: 1,
                      max: 500,
                      divisions: 499,
                      value: _stake.toDouble(),
                      label: formatGtl(_stake),
                      onChanged: (value) => setState(() {
                        _stake = value.round();
                        _preview = null;
                      }),
                    ),
                  ),
                  SizedBox(
                    width: 78,
                    child: Text(formatGtl(_stake), textAlign: TextAlign.end),
                  ),
                ],
              ),
              if (_preview != null)
                DecoratedBox(
                  decoration: BoxDecoration(
                    color: GtlColors.surfaceElevated,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: GtlColors.border),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Text(
                      'Preview: probabilidade ${_preview!.probabilityExact.toStringAsFixed(1)}%, retorno estimado ${formatGtl(_preview!.estimatedReturn)}.',
                    ),
                  ),
                ),
              if (_error != null) ...[
                const SizedBox(height: 8),
                Text(
                  _error!,
                  style: const TextStyle(color: GtlColors.accentRed),
                ),
              ],
              const SizedBox(height: 12),
              FilledButton.icon(
                onPressed: _busy
                    ? null
                    : () => _handleAction(auth.isAuthenticated),
                icon: _busy
                    ? const SizedBox.square(
                        dimension: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.trending_up),
                label: Text(
                  auth.isAuthenticated
                      ? 'Pré-visualizar e confirmar'
                      : 'Entrar para prever',
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Future<void> _handleAction(bool authenticated) async {
    if (!authenticated) {
      await showLoginSheet(context);
      return;
    }
    if (_optionId == null) {
      setState(() => _error = 'Selecione uma opção antes de continuar.');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    final repo = ref.read(marketsRepositoryProvider);
    try {
      final preview = await repo.previewPrediction(
        slug: widget.market.slug,
        optionId: _optionId!,
        stakeAmount: _stake,
      );
      setState(() {
        _preview = preview;
        _busy = false;
      });
      if (mounted) {
        await _confirmPrediction();
      }
    } catch (error) {
      setState(() {
        _busy = false;
        _error = ApiFailure.fromObject(error).message;
      });
    }
  }

  Future<void> _confirmPrediction() async {
    final confirmed = await showModalBottomSheet<bool>(
      context: context,
      backgroundColor: GtlColors.surfaceElevated,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (context) => Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              'Confirmar previsão',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 10),
            Text(
              'A API vai validar saldo, status do mercado e duplicidade antes de registrar.',
            ),
            const SizedBox(height: 18),
            FilledButton.icon(
              onPressed: () => Navigator.of(context).pop(true),
              icon: const Icon(Icons.check),
              label: const Text('Confirmar'),
            ),
            TextButton(
              onPressed: () => Navigator.of(context).pop(false),
              child: const Text('Revisar'),
            ),
          ],
        ),
      ),
    );
    if (confirmed != true || _optionId == null) {
      return;
    }
    setState(() => _busy = true);
    try {
      await ref
          .read(marketsRepositoryProvider)
          .createPrediction(
            slug: widget.market.slug,
            optionId: _optionId!,
            stakeAmount: _stake,
          );
      ref.invalidate(marketsProvider);
      ref.invalidate(marketDetailProvider(widget.market.slug));
      ref.invalidate(walletProvider);
      setState(() => _busy = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Previsão registrada pela API.')),
        );
      }
    } catch (error) {
      setState(() {
        _busy = false;
        _error = ApiFailure.fromObject(error).message;
      });
    }
  }
}
