import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_client.dart';
import '../../core/formatters.dart';
import '../../theme.dart';
import '../../ui/gtl_components.dart';
import '../auth/auth_controller.dart';
import '../auth/login_sheet.dart';
import 'market_models.dart';
import 'markets_providers.dart';

const _reinforcementAction = 'reinforcement';
const _revisionAction = 'revision';

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
  PositionActionPreview? _positionPreview;
  String _positionAction = _reinforcementAction;
  String? _expandedPositionAction;
  String? _error;
  bool _busy = false;
  bool _previewBusy = false;
  Timer? _previewDebounce;
  int _previewRequestId = 0;

  @override
  void initState() {
    super.initState();
    _syncPositionDefaults();
  }

  @override
  void didUpdateWidget(covariant PredictionTicket oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.market.slug != widget.market.slug ||
        oldWidget.market.viewerPosition.optionId !=
            widget.market.viewerPosition.optionId ||
        oldWidget.market.viewerPosition.canReinforce !=
            widget.market.viewerPosition.canReinforce ||
        oldWidget.market.viewerPosition.canRevise !=
            widget.market.viewerPosition.canRevise) {
      _syncPositionDefaults(clearPreview: true);
    }
  }

  @override
  void dispose() {
    _previewDebounce?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);
    final market = widget.market;
    if (market.viewerPosition.hasPosition) {
      return _buildPositionDesk(context, auth.isAuthenticated);
    }
    return _buildInitialPrediction(context, auth.isAuthenticated);
  }

  Widget _buildInitialPrediction(BuildContext context, bool authenticated) {
    final market = widget.market;
    final selectedOption = _selectedOption(market);
    final blocked = !market.isOpen;
    final blockedMessage = market.isOpen
        ? ''
        : 'Este mercado está ${market.statusLabel.toLowerCase()} e não aceita novas previsões.';

    return GtlSurface(
      color: GtlColors.surfaceGlass,
      glowColor: GtlColors.accentBlue,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const GtlEditorialHeader(
            kicker: 'Ação educativa',
            title: 'Ticket de previsão',
            body:
                'Escolha uma opção explicitamente. O preview e a criação vêm da FastAPI.',
            icon: Icons.trending_up,
          ),
          const SizedBox(height: 14),
          for (final option in market.options)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: ChoiceChip(
                selected: _optionId == option.id,
                onSelected: blocked
                    ? null
                    : (_) => _selectInitialOption(option.id, authenticated),
                avatar: Icon(
                  _optionId == option.id
                      ? Icons.check_circle
                      : Icons.radio_button_unchecked,
                  size: 18,
                ),
                label: SizedBox(
                  width: double.infinity,
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Expanded(
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
            ),
          if (blocked)
            _BlockedCallout(message: blockedMessage)
          else ...[
            const SizedBox(height: 2),
            _StakeSlider(
              label: 'Crédito reservado',
              stake: _stake,
              onChanged: (value) => _setStake(value, authenticated),
            ),
            const SizedBox(height: 10),
            _PredictionPreviewPanel(
              selectedLabel: selectedOption?.label ?? 'Selecione',
              stake: _stake,
              preview: _preview,
              busy: _previewBusy,
            ),
            _ErrorText(error: _error),
            const SizedBox(height: 12),
            FilledButton.icon(
              onPressed: _busy ? null : () => _handlePrediction(authenticated),
              icon: _busy
                  ? const SizedBox.square(
                      dimension: 16,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.trending_up),
              label: Text(
                authenticated
                    ? 'Pré-visualizar e confirmar'
                    : 'Entrar para prever',
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildPositionDesk(BuildContext context, bool authenticated) {
    final market = widget.market;
    final position = market.viewerPosition;

    return GtlSurface(
      color: GtlColors.surfaceGlass,
      glowColor: GtlColors.accentCyan,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const GtlEditorialHeader(
            kicker: 'Sua posição',
            title: 'Sua posição atual',
            body:
                'Aumente sua posição ou troque sua escolha com uma prévia segura antes de confirmar.',
            icon: Icons.swap_horiz,
          ),
          const SizedBox(height: 14),
          _PositionSummaryPanel(position: position),
          if (position.activeEntries.isNotEmpty) ...[
            const SizedBox(height: 10),
            _PositionEntriesPanel(entries: position.activeEntries),
          ],
          if (position.history.isNotEmpty) ...[
            const SizedBox(height: 10),
            _PositionHistoryPanel(entries: position.history),
          ],
          const SizedBox(height: 12),
          _PositionActionFrame(
            title: 'Aumentar posição',
            subtitle: position.canReinforce
                ? 'Adicionar GT₵ à sua escolha atual'
                : position.reinforcementBlockedReason,
            icon: Icons.add_chart,
            expanded: _expandedPositionAction == _reinforcementAction,
            badgeLabel: position.canReinforce
                ? _remainingLabel(
                    position.reinforcementRemaining,
                    singular: 'aumento',
                    plural: 'aumentos',
                  )
                : 'Bloqueado',
            enabled: position.canReinforce,
            onTap: () => _selectPositionAction(_reinforcementAction),
            child: _buildPositionActionContent(
              context: context,
              authenticated: authenticated,
              action: _reinforcementAction,
            ),
          ),
          const SizedBox(height: 12),
          _PositionActionFrame(
            title: 'Trocar escolha',
            subtitle: position.canRevise
                ? 'Mover sua posição para outra opção'
                : position.revisionBlockedReason,
            icon: Icons.change_circle_outlined,
            expanded: _expandedPositionAction == _revisionAction,
            badgeLabel: position.canRevise
                ? _remainingLabel(
                    position.revisionRemaining,
                    singular: 'troca',
                    plural: 'trocas',
                  )
                : 'Bloqueado',
            enabled: position.canRevise,
            onTap: () => _selectPositionAction(_revisionAction),
            child: _buildPositionActionContent(
              context: context,
              authenticated: authenticated,
              action: _revisionAction,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPositionActionContent({
    required BuildContext context,
    required bool authenticated,
    required String action,
  }) {
    final market = widget.market;
    final position = market.viewerPosition;
    final isRevision = action == _revisionAction;
    final activeOption = _activeOption(market);
    final selectedOption = _selectedOption(market);
    final allowed = isRevision ? position.canRevise : position.canReinforce;
    final selectedOptionId = _selectedPositionOptionId;
    final validPreview =
        selectedOptionId != null &&
        _positionPreview?.allowed == true &&
        _positionPreview!.matches(
          action: action,
          optionId: selectedOptionId,
          stakeAmount: _positionStake,
        );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (isRevision) ...[
          _RevisionSummary(position: position),
          const SizedBox(height: 10),
          if (position.canRevise)
            _PositionOptionList(
              market: market,
              selectedOptionId: _optionId,
              excludeOptionId: position.optionId,
              onSelected: (optionId) =>
                  _selectPositionOption(optionId, authenticated),
            )
          else
            _BlockedCallout(message: position.revisionBlockedReason),
        ] else ...[
          _ActiveOptionTile(option: activeOption, position: position),
          const SizedBox(height: 10),
          if (position.canReinforce)
            _StakeSlider(
              label: 'GT₵ para aumentar',
              stake: _stake,
              onChanged: (value) => _setStake(value, authenticated),
            )
          else
            _BlockedCallout(message: position.reinforcementBlockedReason),
        ],
        if (allowed) ...[
          const SizedBox(height: 10),
          _PositionPreviewPanel(
            action: action,
            selectedLabel: selectedOption?.label ?? activeOption?.label ?? '-',
            preview: _positionPreview,
            busy: _previewBusy,
          ),
        ],
        _ErrorText(error: _error),
        if (allowed) ...[
          const SizedBox(height: 12),
          FilledButton.icon(
            onPressed: _busy
                ? null
                : () => _handlePositionAction(
                    authenticated: authenticated,
                    hasValidPreview: validPreview,
                  ),
            icon: _busy
                ? const SizedBox.square(
                    dimension: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : Icon(
                    isRevision ? Icons.change_circle_outlined : Icons.add_chart,
                  ),
            label: Text(
              authenticated
                  ? isRevision
                        ? validPreview
                              ? 'Confirmar troca'
                              : 'Pré-visualizar troca'
                        : validPreview
                        ? 'Confirmar aumento'
                        : 'Pré-visualizar aumento'
                  : 'Entrar para participar',
            ),
          ),
          if (authenticated && !validPreview) ...[
            const SizedBox(height: 8),
            Text(
              'A confirmação só aparece depois de uma prévia válida da API.',
              style: Theme.of(
                context,
              ).textTheme.bodySmall?.copyWith(color: GtlColors.textSecondary),
            ),
          ],
        ],
      ],
    );
  }

  Future<void> _handlePrediction(bool authenticated) async {
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
      _setFailure(error, busy: false);
    }
  }

  Future<void> _handlePositionAction({
    required bool authenticated,
    required bool hasValidPreview,
  }) async {
    if (!authenticated) {
      await showLoginSheet(context);
      return;
    }
    final optionId = _selectedPositionOptionId;
    if (optionId == null) {
      setState(() => _error = 'Selecione uma opção antes de continuar.');
      return;
    }
    if (!_isCurrentPositionActionAllowed) {
      setState(() => _error = _currentBlockedReason);
      return;
    }
    if (!hasValidPreview) {
      await _loadPreviewFromApi(openConfirmation: true);
      return;
    }
    await _confirmPositionAction();
  }

  Future<void> _confirmPrediction() async {
    final selectedOption = _selectedOption(widget.market);
    final confirmed = await _showConfirmationSheet(
      title: 'Confirmar previsão',
      body:
          'A API vai validar saldo, status do mercado e duplicidade antes de registrar.',
      icon: Icons.verified_outlined,
      content: _PredictionPreviewPanel(
        selectedLabel: selectedOption?.label ?? 'Selecione',
        stake: _stake,
        preview: _preview,
        busy: false,
      ),
      confirmLabel: 'Confirmar',
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
      _invalidateMarketState();
      setState(() => _busy = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Previsão registrada pela API.')),
        );
      }
    } catch (error) {
      _setFailure(error, busy: false);
    }
  }

  Future<void> _confirmPositionAction() async {
    final optionId = _selectedPositionOptionId;
    final preview = _positionPreview;
    if (optionId == null || preview == null || !preview.allowed) {
      setState(() => _error = 'Gere uma prévia válida antes de confirmar.');
      return;
    }
    final confirmed = await _showConfirmationSheet(
      title: _positionAction == _revisionAction
          ? 'Confirmar troca'
          : 'Confirmar aumento',
      body: _positionAction == _revisionAction
          ? 'A API vai encerrar os movimentos ativos, aplicar o custo informado e abrir sua nova posição.'
          : 'A API vai adicionar GT₵ à mesma escolha ativa.',
      icon: _positionAction == _revisionAction
          ? Icons.change_circle_outlined
          : Icons.add_chart,
      content: _PositionPreviewPanel(
        action: _positionAction,
        selectedLabel:
            _selectedOption(widget.market)?.label ??
            _activeOption(widget.market)?.label ??
            '-',
        preview: preview,
        busy: false,
      ),
      confirmLabel: _positionAction == _revisionAction
          ? 'Confirmar troca'
          : 'Confirmar aumento',
    );
    if (confirmed != true) {
      return;
    }
    setState(() => _busy = true);
    try {
      await ref
          .read(marketsRepositoryProvider)
          .createPositionAction(
            slug: widget.market.slug,
            action: _positionAction,
            optionId: optionId,
            stakeAmount: _positionStake,
          );
      _invalidateMarketState();
      setState(() => _busy = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              _positionAction == _revisionAction
                  ? 'Escolha trocada.'
                  : 'Posição aumentada.',
            ),
          ),
        );
      }
    } catch (error) {
      _setFailure(error, busy: false);
    }
  }

  Future<bool?> _showConfirmationSheet({
    required String title,
    required String body,
    required IconData icon,
    required Widget content,
    required String confirmLabel,
  }) {
    return showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      backgroundColor: GtlColors.surfaceElevated,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(
          top: Radius.circular(GtlRadii.large),
        ),
      ),
      builder: (context) => SafeArea(
        child: LayoutBuilder(
          builder: (context, _) {
            final maxHeight = MediaQuery.sizeOf(context).height * 0.86;
            return ConstrainedBox(
              constraints: BoxConstraints(maxHeight: maxHeight),
              child: SingleChildScrollView(
                padding: EdgeInsets.fromLTRB(
                  20,
                  20,
                  20,
                  MediaQuery.viewInsetsOf(context).bottom + 20,
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    GtlEditorialHeader(
                      kicker: 'Confirmação',
                      title: title,
                      body: body,
                      icon: icon,
                    ),
                    const SizedBox(height: 14),
                    content,
                    const SizedBox(height: 18),
                    FilledButton.icon(
                      onPressed: () => Navigator.of(context).pop(true),
                      icon: const Icon(Icons.check),
                      label: Text(confirmLabel),
                    ),
                    const SizedBox(height: 4),
                    TextButton(
                      onPressed: () => Navigator.of(context).pop(false),
                      child: const Text('Voltar'),
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

  Future<void> _loadPreviewFromApi({bool openConfirmation = false}) async {
    final requestId = _previewRequestId;
    final optionId = widget.market.viewerPosition.hasPosition
        ? _selectedPositionOptionId
        : _optionId;
    final stake = _positionStake;
    if (optionId == null) {
      if (mounted) {
        setState(() => _previewBusy = false);
      }
      return;
    }
    try {
      if (widget.market.viewerPosition.hasPosition) {
        final preview = await ref
            .read(marketsRepositoryProvider)
            .previewPositionAction(
              slug: widget.market.slug,
              action: _positionAction,
              optionId: optionId,
              stakeAmount: stake,
            );
        if (!_previewIsCurrent(requestId, optionId, stake)) {
          return;
        }
        setState(() {
          _positionPreview = preview;
          _previewBusy = false;
          _error = preview.allowed && preview.blockedReason.isEmpty
              ? null
              : preview.blockedReason;
        });
        if (openConfirmation && preview.allowed && mounted) {
          await _confirmPositionAction();
        }
      } else {
        final preview = await ref
            .read(marketsRepositoryProvider)
            .previewPrediction(
              slug: widget.market.slug,
              optionId: optionId,
              stakeAmount: stake,
            );
        if (!_previewIsCurrent(requestId, optionId, stake)) {
          return;
        }
        setState(() {
          _preview = preview;
          _previewBusy = false;
        });
      }
    } catch (error) {
      if (!mounted || requestId != _previewRequestId) {
        return;
      }
      _setFailure(error, busy: false, previewBusy: false);
    }
  }

  bool _previewIsCurrent(int requestId, int optionId, int stake) {
    return mounted &&
        requestId == _previewRequestId &&
        optionId == _selectedPositionOptionId &&
        stake == _positionStake;
  }

  void _selectInitialOption(int optionId, bool authenticated) {
    setState(() {
      _optionId = optionId;
      _preview = null;
      _error = null;
    });
    _schedulePreview(authenticated);
  }

  void _selectPositionOption(int optionId, bool authenticated) {
    setState(() {
      _optionId = optionId;
      _positionPreview = null;
      _error = null;
    });
    _schedulePreview(authenticated);
  }

  void _selectPositionAction(String action) {
    final willCollapse = _expandedPositionAction == action;
    _previewDebounce?.cancel();
    _previewRequestId += 1;
    setState(() {
      _expandedPositionAction = willCollapse ? null : action;
      if (!willCollapse) {
        _positionAction = action;
        _optionId = action == _reinforcementAction
            ? widget.market.viewerPosition.optionId
            : null;
      }
      _positionPreview = null;
      _error = null;
      _previewBusy = false;
    });
  }

  void _setStake(int stake, bool authenticated) {
    setState(() {
      _stake = stake;
      _preview = null;
      _positionPreview = null;
      _error = null;
    });
    _schedulePreview(authenticated);
  }

  void _schedulePreview(bool authenticated) {
    _previewDebounce?.cancel();
    _previewRequestId += 1;
    final optionId = widget.market.viewerPosition.hasPosition
        ? _selectedPositionOptionId
        : _optionId;
    if (widget.market.viewerPosition.hasPosition &&
        _expandedPositionAction == null) {
      if (_previewBusy) {
        setState(() => _previewBusy = false);
      }
      return;
    }
    if (!authenticated ||
        optionId == null ||
        !_isCurrentPositionActionAllowed) {
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

  void _syncPositionDefaults({bool clearPreview = false}) {
    final position = widget.market.viewerPosition;
    if (!position.hasPosition) {
      return;
    }
    if (position.canReinforce) {
      _positionAction = _reinforcementAction;
      _optionId = position.optionId;
    } else if (position.canRevise) {
      _positionAction = _revisionAction;
      _optionId = null;
    } else {
      _positionAction = _reinforcementAction;
      _optionId = position.optionId;
    }
    _expandedPositionAction = null;
    if (clearPreview) {
      _preview = null;
      _positionPreview = null;
      _error = null;
      _previewBusy = false;
    }
  }

  void _invalidateMarketState() {
    ref.invalidate(marketsProvider);
    ref.invalidate(marketDetailProvider(widget.market.slug));
    ref.invalidate(walletProvider);
  }

  void _setFailure(Object error, {required bool busy, bool? previewBusy}) {
    if (!mounted) {
      return;
    }
    setState(() {
      _busy = busy;
      _previewBusy = previewBusy ?? _previewBusy;
      _error = ApiFailure.fromObject(error).message;
    });
  }

  MarketOption? _selectedOption(Market market) {
    for (final option in market.options) {
      if (option.id == _selectedPositionOptionId || option.id == _optionId) {
        return option;
      }
    }
    return null;
  }

  MarketOption? _activeOption(Market market) {
    final activeOptionId = market.viewerPosition.optionId;
    if (activeOptionId == null) {
      return null;
    }
    for (final option in market.options) {
      if (option.id == activeOptionId) {
        return option;
      }
    }
    return null;
  }

  int? get _selectedPositionOptionId {
    if (!widget.market.viewerPosition.hasPosition) {
      return _optionId;
    }
    if (_positionAction == _reinforcementAction) {
      return widget.market.viewerPosition.optionId;
    }
    return _optionId;
  }

  int get _positionStake =>
      widget.market.viewerPosition.hasPosition &&
          _positionAction == _revisionAction
      ? 0
      : _stake;

  bool get _isCurrentPositionActionAllowed {
    if (!widget.market.viewerPosition.hasPosition) {
      return true;
    }
    final position = widget.market.viewerPosition;
    return _positionAction == _reinforcementAction
        ? position.canReinforce
        : position.canRevise;
  }

  String get _currentBlockedReason {
    final position = widget.market.viewerPosition;
    final message = _positionAction == _reinforcementAction
        ? position.reinforcementBlockedReason
        : position.revisionBlockedReason;
    return message.isEmpty ? 'Esta ação não está disponível agora.' : message;
  }
}

class _StakeSlider extends StatelessWidget {
  const _StakeSlider({
    required this.label,
    required this.stake,
    required this.onChanged,
  });

  final String label;
  final int stake;
  final ValueChanged<int> onChanged;

  @override
  Widget build(BuildContext context) {
    return GtlSurface(
      color: GtlColors.surfaceInk,
      padding: const EdgeInsets.fromLTRB(12, 10, 12, 4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Expanded(child: Text(label)),
              Text(
                formatGtl(stake),
                style: Theme.of(context).textTheme.titleMedium,
              ),
            ],
          ),
          Slider(
            min: 1,
            max: 500,
            divisions: 499,
            value: stake.toDouble(),
            label: formatGtl(stake),
            onChanged: (value) => onChanged(value.round()),
          ),
        ],
      ),
    );
  }
}

class _PositionSummaryPanel extends StatelessWidget {
  const _PositionSummaryPanel({required this.position});

  final ViewerPositionSummary position;

  @override
  Widget build(BuildContext context) {
    return GtlSurface(
      color: GtlColors.surfaceInk,
      child: Column(
        children: [
          _PreviewRow(
            label: 'Sua escolha',
            value: position.optionLabel.isEmpty ? '-' : position.optionLabel,
          ),
          const Divider(height: 18),
          _PreviewRow(
            label: 'Movimentos ativos',
            value: '${position.positionCount}',
          ),
          const Divider(height: 18),
          _PreviewRow(
            label: 'Total ativo',
            value: formatGtl(position.activeStakeAmount),
          ),
          const Divider(height: 18),
          _PreviewRow(
            label: 'Crédito possível',
            value: formatGtl(position.potentialPayoutTotal),
          ),
          const Divider(height: 18),
          _PreviewRow(
            label: 'Aumentos restantes',
            value:
                '${position.reinforcementRemaining}/${position.reinforcementMaxCount}',
          ),
          const Divider(height: 18),
          _PreviewRow(
            label: 'Trocas restantes',
            value: '${position.revisionRemaining}',
          ),
        ],
      ),
    );
  }
}

class _PositionEntriesPanel extends StatelessWidget {
  const _PositionEntriesPanel({required this.entries});

  final List<ViewerPositionEntry> entries;

  @override
  Widget build(BuildContext context) {
    return GtlSurface(
      color: GtlColors.surfaceInk,
      padding: EdgeInsets.zero,
      child: Theme(
        data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
        child: Material(
          color: Colors.transparent,
          child: ExpansionTile(
            tilePadding: const EdgeInsets.symmetric(horizontal: 14),
            childrenPadding: const EdgeInsets.fromLTRB(14, 0, 14, 14),
            title: const Text('Detalhes da posição'),
            subtitle: Text(
              '${entries.length} movimento(s) ativos considerados pela API',
            ),
            children: [
              for (final entry in entries)
                Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: _PreviewRow(
                    label:
                        '#${entry.positionSequence} ${_actionLabel(entry.actionType)}',
                    value:
                        '${formatGtl(entry.stakeAmount)} · ${formatProbability(entry.probabilityAtEntry)}',
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class _PositionHistoryPanel extends StatelessWidget {
  const _PositionHistoryPanel({required this.entries});

  final List<ViewerPositionEntry> entries;

  @override
  Widget build(BuildContext context) {
    final visible = entries.take(5).toList();
    return GtlSurface(
      color: GtlColors.surfaceInk,
      padding: EdgeInsets.zero,
      child: Theme(
        data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
        child: Material(
          color: Colors.transparent,
          child: ExpansionTile(
            tilePadding: const EdgeInsets.symmetric(horizontal: 14),
            childrenPadding: const EdgeInsets.fromLTRB(14, 0, 14, 14),
            title: const Text('Histórico de mudanças'),
            subtitle: Text('${entries.length} movimento(s) auditáveis'),
            children: [
              for (final entry in visible)
                Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: _PreviewRow(
                    label:
                        '#${entry.positionSequence} ${_actionLabel(entry.actionType)}',
                    value:
                        '${entry.optionLabel} · ${formatGtl(entry.stakeAmount)}',
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class _PositionActionFrame extends StatelessWidget {
  const _PositionActionFrame({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.expanded,
    required this.badgeLabel,
    required this.enabled,
    required this.onTap,
    required this.child,
  });

  final String title;
  final String subtitle;
  final IconData icon;
  final bool expanded;
  final String badgeLabel;
  final bool enabled;
  final VoidCallback onTap;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final statusColor = enabled ? GtlColors.accentCyan : GtlColors.accentYellow;
    return GtlSurface(
      color: expanded
          ? GtlColors.surfaceInk
          : GtlColors.surfaceInk.withValues(alpha: 0.72),
      borderColor: expanded
          ? statusColor.withValues(alpha: 0.34)
          : GtlColors.border,
      padding: EdgeInsets.zero,
      child: Material(
        color: Colors.transparent,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            InkWell(
              borderRadius: BorderRadius.circular(GtlRadii.medium),
              onTap: onTap,
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Row(
                  children: [
                    Icon(icon, color: statusColor),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            title,
                            style: Theme.of(context).textTheme.titleMedium
                                ?.copyWith(fontWeight: FontWeight.w900),
                          ),
                          if (subtitle.trim().isNotEmpty) ...[
                            const SizedBox(height: 4),
                            Text(
                              subtitle,
                              style: Theme.of(context).textTheme.bodySmall
                                  ?.copyWith(
                                    color: enabled
                                        ? GtlColors.textSecondary
                                        : GtlColors.accentYellow,
                                  ),
                            ),
                          ],
                        ],
                      ),
                    ),
                    const SizedBox(width: 10),
                    _ActionBadge(label: badgeLabel, color: statusColor),
                    const SizedBox(width: 4),
                    Icon(
                      expanded
                          ? Icons.keyboard_arrow_up
                          : Icons.keyboard_arrow_down,
                      color: GtlColors.textSecondary,
                    ),
                  ],
                ),
              ),
            ),
            if (expanded)
              Padding(
                padding: const EdgeInsets.fromLTRB(14, 0, 14, 14),
                child: child,
              ),
          ],
        ),
      ),
    );
  }
}

class _ActionBadge extends StatelessWidget {
  const _ActionBadge({required this.label, required this.color});

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: color.withValues(alpha: 0.24)),
      ),
      child: Text(
        label,
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
          color: color,
          fontWeight: FontWeight.w900,
        ),
      ),
    );
  }
}

class _ActiveOptionTile extends StatelessWidget {
  const _ActiveOptionTile({required this.option, required this.position});

  final MarketOption? option;
  final ViewerPositionSummary position;

  @override
  Widget build(BuildContext context) {
    return GtlSurface(
      color: GtlColors.accentBlue.withValues(alpha: 0.10),
      borderColor: GtlColors.accentBlue.withValues(alpha: 0.34),
      child: Row(
        children: [
          const Icon(Icons.check_circle, color: GtlColors.accentBlue),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              option == null
                  ? 'Você vai aumentar a escolha ativa atual.'
                  : 'Aumentar ${option!.label} · ${formatProbability(option!.probability)}',
            ),
          ),
          Text(formatGtl(position.activeStakeAmount)),
        ],
      ),
    );
  }
}

class _RevisionSummary extends StatelessWidget {
  const _RevisionSummary({required this.position});

  final ViewerPositionSummary position;

  @override
  Widget build(BuildContext context) {
    return GtlSurface(
      color: GtlColors.surfaceInk,
      child: Column(
        children: [
          _PreviewRow(
            label: 'Movimentos que serão encerrados',
            value: '${position.positionCount} em ${position.optionLabel}',
          ),
          const Divider(height: 18),
          _PreviewRow(
            label: 'Total atual',
            value: formatGtl(position.activeStakeAmount),
          ),
          const Divider(height: 18),
          _PreviewRow(
            label: 'Custo da troca',
            value:
                '${formatGtl(position.revisionPenaltyAmount)} (${position.revisionPenaltyPercent}%)',
          ),
          const Divider(height: 18),
          _PreviewRow(
            label: 'Nova posição estimada',
            value: formatGtl(position.revisionNewStakeAmount),
          ),
        ],
      ),
    );
  }
}

class _PositionOptionList extends StatelessWidget {
  const _PositionOptionList({
    required this.market,
    required this.selectedOptionId,
    required this.excludeOptionId,
    required this.onSelected,
  });

  final Market market;
  final int? selectedOptionId;
  final int? excludeOptionId;
  final ValueChanged<int> onSelected;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        for (final option in market.options)
          if (option.id != excludeOptionId)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: ChoiceChip(
                selected: selectedOptionId == option.id,
                onSelected: (_) => onSelected(option.id),
                avatar: Icon(
                  selectedOptionId == option.id
                      ? Icons.check_circle
                      : Icons.radio_button_unchecked,
                  size: 18,
                ),
                label: SizedBox(
                  width: double.infinity,
                  child: Row(
                    children: [
                      Expanded(
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
            ),
      ],
    );
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
    return GtlSurface(
      color: GtlColors.surfaceInk,
      child: Column(
        children: [
          _PreviewRow(label: 'Opção escolhida', value: selectedLabel),
          const Divider(height: 18),
          _PreviewRow(
            label: 'Crédito possível se acertar',
            value: busy
                ? 'Atualizando...'
                : preview == null
                ? '-'
                : formatGtl(preview!.estimatedReturn),
          ),
          const Divider(height: 18),
          _PreviewRow(label: 'Crédito reservado', value: formatGtl(stake)),
        ],
      ),
    );
  }
}

class _PositionPreviewPanel extends StatelessWidget {
  const _PositionPreviewPanel({
    required this.action,
    required this.selectedLabel,
    required this.preview,
    required this.busy,
  });

  final String action;
  final String selectedLabel;
  final PositionActionPreview? preview;
  final bool busy;

  @override
  Widget build(BuildContext context) {
    final isRevision = action == _revisionAction;
    return GtlSurface(
      color: GtlColors.surfaceInk,
      child: Column(
        children: [
          _PreviewRow(
            label: 'Ação',
            value: isRevision
                ? 'Trocar para $selectedLabel'
                : 'Aumentar $selectedLabel',
          ),
          const Divider(height: 18),
          if (isRevision) ...[
            _PreviewRow(
              label: 'Movimentos encerrados',
              value: busy
                  ? 'Atualizando...'
                  : preview == null
                  ? '-'
                  : '${preview!.activePositionCount} (${formatGtl(preview!.activeStakeAmount)})',
            ),
            const Divider(height: 18),
            _PreviewRow(
              label: 'Custo da troca',
              value: preview == null
                  ? '-'
                  : '${formatGtl(preview!.penaltyAmount)} (${preview!.revisionPenaltyPercent}%)',
            ),
            const Divider(height: 18),
            _PreviewRow(
              label: 'Nova posição estimada',
              value: preview == null
                  ? '-'
                  : formatGtl(preview!.newPositionStakeAmount),
            ),
            const Divider(height: 18),
            _PreviewRow(
              label: 'Trocas restantes',
              value: preview == null ? '-' : '${preview!.revisionRemaining}',
            ),
          ] else ...[
            _PreviewRow(
              label: 'Aumento',
              value: busy
                  ? 'Atualizando...'
                  : preview == null
                  ? '-'
                  : '+${formatGtl(preview!.stakeAmount)}',
            ),
            const Divider(height: 18),
            _PreviewRow(
              label: 'Novo total ativo',
              value: preview == null
                  ? '-'
                  : formatGtl(preview!.positionTotalAfter),
            ),
            const Divider(height: 18),
            _PreviewRow(
              label: 'Aumentos restantes',
              value: preview == null
                  ? '-'
                  : '${preview!.reinforcementRemaining}',
            ),
          ],
          const Divider(height: 18),
          _PreviewRow(
            label: 'Crédito possível se acertar',
            value: preview == null ? '-' : formatGtl(preview!.estimatedReturn),
          ),
          if (preview?.allowed == false &&
              preview!.blockedReason.isNotEmpty) ...[
            const Divider(height: 18),
            Text(
              preview!.blockedReason,
              style: const TextStyle(color: GtlColors.accentYellow),
            ),
          ],
        ],
      ),
    );
  }
}

class _BlockedCallout extends StatelessWidget {
  const _BlockedCallout({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    if (message.trim().isEmpty) {
      return const SizedBox.shrink();
    }
    return Padding(
      padding: const EdgeInsets.only(top: 12),
      child: GtlSurface(
        color: GtlColors.accentYellow.withValues(alpha: 0.10),
        borderColor: GtlColors.accentYellow.withValues(alpha: 0.34),
        child: Row(
          children: [
            const Icon(Icons.lock_clock, color: GtlColors.accentYellow),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                message,
                style: const TextStyle(color: GtlColors.accentYellow),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ErrorText extends StatelessWidget {
  const _ErrorText({required this.error});

  final String? error;

  @override
  Widget build(BuildContext context) {
    if (error == null || error!.trim().isEmpty) {
      return const SizedBox.shrink();
    }
    return Padding(
      padding: const EdgeInsets.only(top: 8),
      child: Text(error!, style: const TextStyle(color: GtlColors.accentRed)),
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

String _actionLabel(String action) {
  return switch (action) {
    'reinforcement' => 'Aumento',
    'revision' => 'Troca',
    _ => 'Entrada inicial',
  };
}

String _remainingLabel(
  int count, {
  required String singular,
  required String plural,
}) {
  return count == 1 ? '1 $singular' : '$count $plural';
}
