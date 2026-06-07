import 'dart:async';

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
  int _stake = 80;
  PredictionPreview? _preview;
  String? _error;
  bool _busy = false;
  bool _previewBusy = false;
  Timer? _previewDebounce;
  int _previewRequestId = 0;

  @override
  void dispose() {
    _previewDebounce?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);
    final market = widget.market;
    final selectedOption = _selectedOption(market);
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
                      : (_) => _selectOption(option.id, auth.isAuthenticated),
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
              const SizedBox(height: 2),
              Row(
                children: [
                  const Text('Crédito reservado'),
                  Expanded(
                    child: Slider(
                      min: 1,
                      max: 500,
                      divisions: 499,
                      value: _stake.toDouble(),
                      label: formatGtl(_stake),
                      onChanged: (value) =>
                          _setStake(value.round(), auth.isAuthenticated),
                    ),
                  ),
                  SizedBox(
                    width: 78,
                    child: Text(formatGtl(_stake), textAlign: TextAlign.end),
                  ),
                ],
              ),
              _PredictionPreviewPanel(
                selectedLabel: selectedOption?.label ?? 'Selecione',
                stake: _stake,
                preview: _preview,
                busy: _previewBusy,
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

  MarketOption? _selectedOption(Market market) {
    for (final option in market.options) {
      if (option.id == _optionId) {
        return option;
      }
    }
    return null;
  }

  void _selectOption(int optionId, bool authenticated) {
    setState(() {
      _optionId = optionId;
      _preview = null;
      _error = null;
    });
    _schedulePreview(authenticated);
  }

  void _setStake(int stake, bool authenticated) {
    setState(() {
      _stake = stake;
      _preview = null;
      _error = null;
    });
    _schedulePreview(authenticated);
  }

  void _schedulePreview(bool authenticated) {
    _previewDebounce?.cancel();
    _previewRequestId += 1;
    if (!authenticated || _optionId == null) {
      if (_previewBusy) {
        setState(() => _previewBusy = false);
      }
      return;
    }
    setState(() => _previewBusy = true);
    _previewDebounce = Timer(
      const Duration(milliseconds: 300),
      _loadPreviewFromApi,
    );
  }

  Future<void> _loadPreviewFromApi() async {
    final requestId = _previewRequestId;
    final optionId = _optionId;
    final stake = _stake;
    if (optionId == null) {
      if (mounted) {
        setState(() => _previewBusy = false);
      }
      return;
    }
    try {
      final preview = await ref
          .read(marketsRepositoryProvider)
          .previewPrediction(
            slug: widget.market.slug,
            optionId: optionId,
            stakeAmount: stake,
          );
      if (!mounted ||
          requestId != _previewRequestId ||
          optionId != _optionId ||
          stake != _stake) {
        return;
      }
      setState(() {
        _preview = preview;
        _previewBusy = false;
      });
    } catch (error) {
      if (!mounted || requestId != _previewRequestId) {
        return;
      }
      setState(() {
        _previewBusy = false;
        _error = ApiFailure.fromObject(error).message;
      });
    }
  }

  Future<void> _confirmPrediction() async {
    final selectedOption = _selectedOption(widget.market);
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
            _PredictionPreviewPanel(
              selectedLabel: selectedOption?.label ?? 'Selecione',
              stake: _stake,
              preview: _preview,
              busy: false,
            ),
            const SizedBox(height: 12),
            const Text(
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

class _PredictionPreviewPanel extends StatelessWidget {
  const _PredictionPreviewPanel({
    required this.selectedLabel,
    required this.stake,
    required this.preview,
    required this.busy,
  });

  final String selectedLabel;
  final int stake;
  final PredictionPreview? preview;
  final bool busy;

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
        child: Column(
          children: [
            _PreviewRow(label: 'Opção escolhida', value: selectedLabel),
            const Divider(height: 16),
            _PreviewRow(
              label: 'Crédito possível se acertar',
              value: busy
                  ? 'Atualizando...'
                  : preview == null
                  ? '-'
                  : formatGtl(preview!.estimatedReturn),
            ),
            const Divider(height: 16),
            _PreviewRow(label: 'Crédito reservado', value: formatGtl(stake)),
          ],
        ),
      ),
    );
  }
}

class _PreviewRow extends StatelessWidget {
  const _PreviewRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          child: Text(label, style: Theme.of(context).textTheme.bodyMedium),
        ),
        const SizedBox(width: 12),
        Flexible(
          child: Text(
            value,
            textAlign: TextAlign.end,
            style: Theme.of(
              context,
            ).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w900),
          ),
        ),
      ],
    );
  }
}
