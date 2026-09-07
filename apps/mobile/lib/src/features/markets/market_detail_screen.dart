import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter/services.dart';
import 'package:share_plus/share_plus.dart';

import '../../core/api_client.dart';
import '../../core/environment.dart';
import '../../core/formatters.dart';
import '../../core/providers.dart';
import '../../theme.dart';
import '../../ui/gtl_components.dart';
import '../auth/auth_controller.dart';
import '../auth/login_sheet.dart';
import '../live_refresh.dart';
import 'market_cards.dart';
import 'market_models.dart';
import 'markets_providers.dart';
import 'prediction_ticket.dart';

enum MarketDetailTab { overview, community }

class MarketDetailScreen extends ConsumerStatefulWidget {
  const MarketDetailScreen({
    super.key,
    required this.slug,
    this.initialTab = MarketDetailTab.overview,
  });

  final String slug;
  final MarketDetailTab initialTab;

  @override
  ConsumerState<MarketDetailScreen> createState() => _MarketDetailScreenState();
}

class _MarketDetailScreenState extends ConsumerState<MarketDetailScreen> {
  late int _tab;
  final Set<String> _trackedViewSlugs = <String>{};

  @override
  void initState() {
    super.initState();
    _tab = widget.initialTab == MarketDetailTab.community ? 1 : 0;
    _refreshAfterFrame(widget.slug);
  }

  @override
  void didUpdateWidget(covariant MarketDetailScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.slug != oldWidget.slug ||
        widget.initialTab != oldWidget.initialTab) {
      _tab = widget.initialTab == MarketDetailTab.community ? 1 : 0;
    }
    if (widget.slug != oldWidget.slug) {
      _refreshAfterFrame(widget.slug);
    }
  }

  void _refreshAfterFrame(String slug) {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) {
        invalidateMarketData(ref, slug: slug);
      }
    });
  }

  Future<void> _trackMarketView(String slug) async {
    try {
      await ref.read(marketsRepositoryProvider).trackView(slug);
    } catch (_) {
      // Tracking acompanha a semântica web, mas nunca bloqueia o detalhe.
    }
  }

  void _trackMarketViewAfterRender(String slug) {
    if (_trackedViewSlugs.contains(slug)) {
      return;
    }
    _trackedViewSlugs.add(slug);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) {
        _trackedViewSlugs.remove(slug);
        return;
      }
      unawaited(_trackMarketView(slug));
    });
  }

  @override
  Widget build(BuildContext context) {
    final detail = ref.watch(marketDetailProvider(widget.slug));
    final api = ref.watch(apiClientProvider);
    return Scaffold(
      body: detail.when(
        loading: () =>
            const GtlScreen(child: Center(child: CircularProgressIndicator())),
        error: (error, stack) => GtlScreen(
          child: GtlStatePanel(
            icon: Icons.cloud_off,
            title: 'Detalhe indisponível',
            body: ApiFailure.fromObject(error).message,
            color: GtlColors.accentYellow,
          ),
        ),
        data: (market) {
          _trackMarketViewAfterRender(market.slug);
          return GtlScreen(
            child: CustomScrollView(
              slivers: [
                SliverAppBar(
                  expandedHeight: 330,
                  pinned: true,
                  backgroundColor: GtlColors.background,
                  surfaceTintColor: Colors.transparent,
                  actions: [_MarketActionButtons(market: market)],
                  flexibleSpace: FlexibleSpaceBar(
                    background: Padding(
                      padding: EdgeInsets.fromLTRB(
                        10,
                        MediaQuery.paddingOf(context).top + 10,
                        10,
                        0,
                      ),
                      child: MarketHeroCard(
                        market: market,
                        api: api,
                        openOnTap: false,
                      ),
                    ),
                  ),
                ),
                SliverToBoxAdapter(
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(16, 18, 16, 28),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        SegmentedButton<int>(
                          segments: const [
                            ButtonSegment(
                              value: 0,
                              label: Text('Visão geral'),
                              icon: Icon(Icons.auto_graph),
                            ),
                            ButtonSegment(
                              value: 1,
                              label: Text('Comunidade'),
                              icon: Icon(Icons.forum_outlined),
                            ),
                          ],
                          selected: {_tab},
                          onSelectionChanged: (value) =>
                              setState(() => _tab = value.first),
                        ),
                        const SizedBox(height: 16),
                        if (_tab == 0)
                          _OverviewTab(market: market)
                        else
                          _CommunityTab(market: market),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _MarketActionButtons extends ConsumerWidget {
  const _MarketActionButtons({required this.market});

  final Market market;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authControllerProvider);
    return Row(
      children: [
        IconButton(
          tooltip: 'Favoritar',
          onPressed: () =>
              _mutate(context, ref, auth.isAuthenticated, favorite: true),
          icon: Icon(
            market.viewerHasFavorite ? Icons.bookmark : Icons.bookmark_border,
          ),
          style: IconButton.styleFrom(
            backgroundColor: GtlColors.surfaceGlass,
            foregroundColor: GtlColors.textPrimary,
          ),
        ),
        IconButton(
          tooltip: 'Curtir',
          onPressed: () =>
              _mutate(context, ref, auth.isAuthenticated, favorite: false),
          icon: Icon(
            market.viewerHasLike ? Icons.favorite : Icons.favorite_border,
          ),
          style: IconButton.styleFrom(
            backgroundColor: GtlColors.surfaceGlass,
            foregroundColor: market.viewerHasLike
                ? GtlColors.accentRed
                : GtlColors.textPrimary,
          ),
        ),
        IconButton(
          tooltip: 'Compartilhar',
          onPressed: () => _shareMarket(context, ref, market),
          icon: const Icon(Icons.ios_share),
          style: IconButton.styleFrom(
            backgroundColor: GtlColors.surfaceGlass,
            foregroundColor: GtlColors.textPrimary,
          ),
        ),
      ],
    );
  }

  Future<void> _mutate(
    BuildContext context,
    WidgetRef ref,
    bool authenticated, {
    required bool favorite,
  }) async {
    if (!authenticated) {
      await showLoginSheet(context);
      return;
    }
    try {
      if (favorite) {
        await ref
            .read(marketsRepositoryProvider)
            .favorite(market.slug, !market.viewerHasFavorite);
      } else {
        await ref
            .read(marketsRepositoryProvider)
            .like(market.slug, !market.viewerHasLike);
      }
      ref.invalidate(marketsProvider);
      ref.invalidate(marketDetailProvider(market.slug));
    } catch (error) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(ApiFailure.fromObject(error).message)),
        );
      }
    }
  }
}

class _OverviewTab extends ConsumerWidget {
  const _OverviewTab({required this.market});

  final Market market;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        GtlSurface(
          color: GtlColors.surfaceGlass,
          child: GtlEditorialHeader(
            kicker: market.category,
            title: market.title,
            body: market.summary.isEmpty
                ? (market.subcategory.isEmpty
                      ? market.event
                      : market.subcategory)
                : market.summary,
            icon: Icons.public,
          ),
        ),
        const SizedBox(height: 12),
        MarketMetricPanel(market: market),
        const SizedBox(height: 12),
        MarketSparklineCard(market: market),
        const SizedBox(height: 12),
        GtlSurface(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const GtlSectionTitle(
                title: 'Critério de resolução',
                subtitle: 'Fonte auditável antes do resultado',
              ),
              const SizedBox(height: 10),
              Text(
                market.resolutionCriteria.isEmpty
                    ? 'Critério não informado.'
                    : market.resolutionCriteria,
              ),
              if (market.isResolved || market.isSealed) ...[
                const SizedBox(height: 14),
                const GtlSectionTitle(title: 'Resultado oficial'),
                const SizedBox(height: 8),
                Text(
                  market.resolutionNote.isEmpty
                      ? 'Resolvido em ${market.resolvedAtLabel}'
                      : market.resolutionNote,
                ),
              ],
            ],
          ),
        ),
        const SizedBox(height: 12),
        PredictionTicket(market: market),
        if (market.integrity.definitionRegistered) ...[
          const SizedBox(height: 12),
          GtlSurface(
            color: GtlColors.surfaceGlass,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                GtlSectionTitle(
                  title: 'Integridade do mercado',
                  subtitle: _integritySummary(market),
                ),
                const SizedBox(height: 10),
                OutlinedButton.icon(
                  onPressed: () => _showIntegritySheet(context, ref, market),
                  icon: const Icon(Icons.verified_user_outlined),
                  label: const Text('Verificar integridade'),
                ),
              ],
            ),
          ),
        ],
      ],
    );
  }

  Future<void> _showIntegritySheet(
    BuildContext context,
    WidgetRef ref,
    Market market,
  ) async {
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (sheetContext) => _IntegritySheet(
        market: market,
        load: () async {
          final repository = ref.read(marketsRepositoryProvider);
          return (
            proof: await repository.integrity(market.slug),
            verification: await repository.verifyIntegrity(market.slug),
          );
        },
      ),
    );
  }
}

class _IntegritySheet extends StatelessWidget {
  const _IntegritySheet({required this.market, required this.load});

  final Market market;
  final Future<
    ({Map<String, dynamic> proof, Map<String, dynamic> verification})
  >
  Function()
  load;

  @override
  Widget build(BuildContext context) {
    return FractionallySizedBox(
      heightFactor: 0.92,
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: FutureBuilder(
            future: load(),
            builder: (context, snapshot) {
              if (snapshot.connectionState != ConnectionState.done) {
                return const SizedBox(
                  height: 260,
                  child: Center(child: CircularProgressIndicator()),
                );
              }
              if (snapshot.hasError || !snapshot.hasData) {
                return GtlStatePanel(
                  icon: Icons.cloud_off,
                  title: 'Verificação indisponível',
                  body: 'Não foi possível conferir agora. Tente novamente.',
                  color: GtlColors.accentYellow,
                );
              }
              final value = snapshot.data!;
              final proof = value.proof;
              final verification = value.verification;
              final definition = Map<String, dynamic>.from(
                (proof['definition'] as Map?) ?? const <String, dynamic>{},
              );
              final seal = Map<String, dynamic>.from(
                (proof['seal'] as Map?) ?? const <String, dynamic>{},
              );
              final sealPayload = Map<String, dynamic>.from(
                (seal['payload'] as Map?) ?? const <String, dynamic>{},
              );
              final predictionCommitments = Map<String, dynamic>.from(
                (proof['prediction_commitments'] as Map?) ??
                    const <String, dynamic>{},
              );
              final ledgerEvents =
                  (proof['ledger_events'] as List?) ?? const [];
              final protocol = safeString(
                proof['protocol_version'],
                market.integrity.protocolVersion,
              );
              final technicalDetails = <(String, String)>[
                ('Protocolo', protocol),
                ('Algoritmo', safeString(definition['algorithm'])),
                ('Hash da definição', safeString(definition['hash'])),
                ('Identificação da chave', safeString(definition['key_id'])),
                (
                  'Fingerprint da chave',
                  safeString(definition['key_fingerprint']),
                ),
                (
                  'Assinatura da definição',
                  safeString(definition['signature']),
                ),
                (
                  'Comprovantes agregados',
                  safeString(predictionCommitments['count'], '0'),
                ),
                ('Eventos do mercado', ledgerEvents.length.toString()),
                (
                  'Cadeia de eventos do mercado',
                  verification['market_events_valid'] == true
                      ? 'Verificada'
                      : 'Não verificada',
                ),
                (
                  'Cadeia global do ledger',
                  verification['ledger_chain_valid'] == true
                      ? 'Verificada'
                      : verification['ledger_chain_valid'] == false
                      ? 'Diferença detectada'
                      : verification['verification_status'] == 'unavailable'
                      ? 'Checkpoint ainda indisponível'
                      : 'Aguardando o próximo ciclo',
                ),
                (
                  'Checkpoint verificado até',
                  'Evento ${verification['ledger_verified_through_sequence'] ?? 0} de ${verification['ledger_current_sequence'] ?? 0}',
                ),
                if (verification['ledger_verified_at'] != null)
                  (
                    'Última auditoria global',
                    safeString(verification['ledger_verified_at']),
                  ),
                if (ledgerEvents.isNotEmpty) ...[
                  (
                    'Hash do último evento',
                    safeString((ledgerEvents.last as Map?)?['event_hash']),
                  ),
                  (
                    'Elo anterior',
                    safeString(
                      (ledgerEvents.last as Map?)?['previous_event_hash'],
                    ),
                  ),
                ],
                if (seal.isNotEmpty) ...[
                  ('Hash da finalização', safeString(seal['hash'])),
                  (
                    'Raiz das previsões',
                    safeString(sealPayload['predictions_root']),
                  ),
                  ('Assinatura da finalização', safeString(seal['signature'])),
                ],
              ];
              final definitionOk =
                  verification['definition_valid'] == true &&
                  verification['definition_matches_current'] != false;
              final predictionsOk =
                  verification['merkle_root_valid'] == true &&
                  verification['prediction_commitments_valid'] != false;
              final resultOk =
                  verification['seal_valid'] == true &&
                  verification['result_matches_current'] != false;
              final finalOk = verification['overall_valid'] == true;
              final finalFailed =
                  verification['verification_status'] == 'failed';
              Widget check(
                String label, {
                required String state,
                required IconData icon,
                required Color color,
              }) => ListTile(
                contentPadding: EdgeInsets.zero,
                leading: Icon(icon, color: color),
                title: Text(label),
                trailing: Text(state, style: TextStyle(color: color)),
              );
              return SingleChildScrollView(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const GtlSectionTitle(
                      title: 'Verificar integridade',
                      subtitle: 'Registro de Integridade Verificável',
                    ),
                    const SizedBox(height: 12),
                    const Text(
                      'Comparamos impressões digitais (hashes), assinaturas criptográficas e a sequência conectada dos registros para detectar alterações.',
                    ),
                    const SizedBox(height: 8),
                    check(
                      'Definição publicada',
                      state: definitionOk
                          ? 'Verificada'
                          : 'Diferença detectada',
                      icon: definitionOk
                          ? Icons.check_circle_outline
                          : Icons.error_outline,
                      color: definitionOk
                          ? GtlColors.accentGreen
                          : GtlColors.accentRed,
                    ),
                    check(
                      'Previsões',
                      state: market.integrity.isSealed
                          ? (predictionsOk
                                ? 'Verificadas'
                                : 'Diferença detectada')
                          : market.isOpen
                          ? 'Comprovantes em registro'
                          : market.status == 'canceled'
                          ? 'Registros preservados'
                          : 'Recebimento encerrado',
                      icon: market.integrity.isSealed
                          ? (predictionsOk
                                ? Icons.check_circle_outline
                                : Icons.error_outline)
                          : market.isOpen
                          ? Icons.sync_outlined
                          : Icons.inventory_2_outlined,
                      color: market.integrity.isSealed
                          ? (predictionsOk
                                ? GtlColors.accentGreen
                                : GtlColors.accentRed)
                          : market.isOpen
                          ? GtlColors.accentBlue
                          : GtlColors.muted,
                    ),
                    check(
                      'Resultado',
                      state: market.integrity.isSealed
                          ? (resultOk ? 'Verificado' : 'Diferença detectada')
                          : market.status == 'canceled'
                          ? 'Não se aplica'
                          : market.isResolved
                          ? 'Em revisão operacional'
                          : 'Aguardando',
                      icon: market.integrity.isSealed
                          ? (resultOk
                                ? Icons.check_circle_outline
                                : Icons.error_outline)
                          : market.isResolved
                          ? Icons.schedule
                          : Icons.horizontal_rule,
                      color: market.integrity.isSealed
                          ? (resultOk
                                ? GtlColors.accentGreen
                                : GtlColors.accentRed)
                          : market.isResolved
                          ? GtlColors.accentYellow
                          : GtlColors.muted,
                    ),
                    check(
                      'Histórico final',
                      state: market.integrity.isSealed
                          ? (finalOk
                                ? 'Finalizado e verificado'
                                : finalFailed
                                ? 'Diferença detectada'
                                : 'Conferência global pendente')
                          : market.integrity.isSealRetryPending
                          ? 'Nova tentativa pendente'
                          : market.integrity.isPendingSeal
                          ? 'Finalização prevista'
                          : 'Não se aplica',
                      icon: market.integrity.isSealed
                          ? (finalOk
                                ? Icons.verified_outlined
                                : finalFailed
                                ? Icons.error_outline
                                : Icons.sync_outlined)
                          : market.integrity.isPendingSeal ||
                                market.integrity.isSealRetryPending
                          ? Icons.schedule
                          : Icons.horizontal_rule,
                      color: market.integrity.isSealed
                          ? (finalOk
                                ? GtlColors.accentGreen
                                : finalFailed
                                ? GtlColors.accentRed
                                : GtlColors.accentBlue)
                          : market.integrity.isPendingSeal ||
                                market.integrity.isSealRetryPending
                          ? GtlColors.accentYellow
                          : GtlColors.muted,
                    ),
                    const SizedBox(height: 10),
                    GtlSurface(
                      color: GtlColors.surfaceInk,
                      padding: EdgeInsets.zero,
                      child: Theme(
                        data: Theme.of(
                          context,
                        ).copyWith(dividerColor: Colors.transparent),
                        child: Material(
                          color: Colors.transparent,
                          child: ExpansionTile(
                            title: const Text('Ver detalhes técnicos'),
                            subtitle: const Text(
                              'Hashes, assinaturas, chave, Seal e ledger',
                            ),
                            childrenPadding: const EdgeInsets.fromLTRB(
                              14,
                              0,
                              14,
                              14,
                            ),
                            children: [
                              for (final detail in technicalDetails)
                                _IntegrityTechnicalRow(
                                  label: detail.$1,
                                  value: detail.$2,
                                ),
                            ],
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 18),
                    Row(
                      children: [
                        Expanded(
                          child: OutlinedButton.icon(
                            onPressed: () => _copyTechnicalDetails(
                              context,
                              technicalDetails,
                            ),
                            icon: const Icon(Icons.copy_outlined),
                            label: const Text('Copiar detalhes'),
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: FilledButton(
                            onPressed: () => Navigator.pop(context),
                            child: const Text('Fechar'),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              );
            },
          ),
        ),
      ),
    );
  }

  Future<void> _copyTechnicalDetails(
    BuildContext context,
    List<(String, String)> details,
  ) async {
    await Clipboard.setData(
      ClipboardData(
        text: details
            .map(
              (detail) =>
                  '${detail.$1}: ${detail.$2.isEmpty ? '-' : detail.$2}',
            )
            .join('\n'),
      ),
    );
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Detalhes da integridade copiados.')),
      );
    }
  }
}

class _IntegrityTechnicalRow extends StatelessWidget {
  const _IntegrityTechnicalRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(label, style: Theme.of(context).textTheme.labelSmall),
          const SizedBox(height: 3),
          SelectableText(value.isEmpty ? '-' : value),
        ],
      ),
    );
  }
}

class _CommunityTab extends ConsumerStatefulWidget {
  const _CommunityTab({required this.market});

  final Market market;

  @override
  ConsumerState<_CommunityTab> createState() => _CommunityTabState();
}

class _CommunityTabState extends ConsumerState<_CommunityTab> {
  final _comment = TextEditingController();
  bool _busy = false;

  @override
  void dispose() {
    _comment.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (widget.market.comments.isEmpty)
          const GtlSurface(
            child: GtlEditorialHeader(
              kicker: 'Comunidade',
              title: 'Sem comentários ainda',
              body:
                  'A primeira leitura pública deste mercado ainda não chegou.',
              icon: Icons.forum_outlined,
            ),
          )
        else
          for (final comment in widget.market.comments)
            _CommentItem(market: widget.market, comment: comment),
        const SizedBox(height: 12),
        if (!auth.isAuthenticated)
          OutlinedButton.icon(
            onPressed: () => showLoginSheet(context),
            icon: const Icon(Icons.login),
            label: const Text('Entrar para comentar'),
          )
        else
          GtlSurface(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                TextField(
                  controller: _comment,
                  minLines: 2,
                  maxLines: 4,
                  decoration: const InputDecoration(labelText: 'Comentário'),
                ),
                const SizedBox(height: 10),
                FilledButton.icon(
                  onPressed: _busy ? null : _send,
                  icon: _busy
                      ? const SizedBox.square(
                          dimension: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.send),
                  label: const Text('Enviar comentário'),
                ),
              ],
            ),
          ),
      ],
    );
  }

  Future<void> _send() async {
    final text = _comment.text.trim();
    if (text.isEmpty) {
      return;
    }
    setState(() => _busy = true);
    try {
      await ref
          .read(marketsRepositoryProvider)
          .createComment(widget.market.slug, text);
      _comment.clear();
      ref.invalidate(marketDetailProvider(widget.market.slug));
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(ApiFailure.fromObject(error).message)),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _busy = false);
      }
    }
  }
}

class _CommentItem extends ConsumerWidget {
  const _CommentItem({required this.market, required this.comment});

  final Market market;
  final MarketComment comment;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authControllerProvider);
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: GtlSurface(
        color: GtlColors.surfaceGlass,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CircleAvatar(
                  backgroundColor: comment.authorIsBot
                      ? GtlColors.accentViolet.withValues(alpha: 0.20)
                      : GtlColors.accentBlue.withValues(alpha: 0.16),
                  child: Icon(
                    comment.authorIsBot ? Icons.verified : Icons.person_outline,
                    color: comment.authorIsBot
                        ? GtlColors.accentViolet
                        : GtlColors.accentBlue,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    '@${comment.authorHandle} ${comment.authorIsBot ? '· IA oficial' : ''}',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
                Text(comment.createdAtLabel),
              ],
            ),
            const SizedBox(height: 8),
            Text(comment.body),
            const SizedBox(height: 8),
            Row(
              children: [
                TextButton.icon(
                  onPressed: auth.isAuthenticated
                      ? () => _react(
                          ref,
                          'like',
                          comment.viewerReaction != 'like',
                        )
                      : null,
                  icon: const Icon(Icons.thumb_up_alt_outlined, size: 18),
                  label: Text(comment.likeCount.toString()),
                ),
                TextButton.icon(
                  onPressed: auth.isAuthenticated
                      ? () => _react(
                          ref,
                          'dislike',
                          comment.viewerReaction != 'dislike',
                        )
                      : null,
                  icon: const Icon(Icons.thumb_down_alt_outlined, size: 18),
                  label: Text(comment.dislikeCount.toString()),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _react(WidgetRef ref, String reaction, bool enabled) async {
    await ref
        .read(marketsRepositoryProvider)
        .reactToComment(comment.id, reaction, enabled);
    ref.invalidate(marketDetailProvider(market.slug));
  }
}

String _integritySummary(Market market) {
  if (market.integrity.isSealed) {
    return 'O histórico foi finalizado e pode ser verificado.';
  }
  if (market.integrity.isSealRetryPending) {
    return 'Os registros foram preservados e aguardam uma nova tentativa de finalização.';
  }
  if (market.integrity.isVerificationFailed) {
    return 'Uma diferença de integridade precisa ser verificada.';
  }
  if (market.integrity.isCanceledPreserved) {
    return 'O mercado foi cancelado e os registros existentes foram preservados.';
  }
  if (market.integrity.isPendingSeal) {
    return market.sealDueAt.isEmpty
        ? 'O resultado foi registrado e aguarda finalização.'
        : 'O resultado foi registrado e aguarda finalização prevista para ${market.sealDueAt}.';
  }
  return 'A definição publicada foi registrada e pode ser conferida.';
}

Future<void> _shareMarket(
  BuildContext context,
  WidgetRef ref,
  Market market,
) async {
  final url = Uri.parse(
    AppEnvironment.publicWebBaseUrl,
  ).replace(path: '/markets/${market.slug}/').toString();
  try {
    await ref.read(marketsRepositoryProvider).trackShare(market.slug);
    ref.invalidate(marketsProvider);
    ref.invalidate(marketDetailProvider(market.slug));
  } catch (_) {
    // Compartilhar continua sendo uma acao local quando a telemetria falha.
  }
  await SharePlus.instance.share(
    ShareParams(
      title: market.title,
      subject: 'GoTrendLabs',
      text: '${market.title}\n\nAcompanhe este mercado no GoTrendLabs: $url',
    ),
  );
}
