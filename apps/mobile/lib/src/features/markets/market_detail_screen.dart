import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:share_plus/share_plus.dart';

import '../../core/api_client.dart';
import '../../core/environment.dart';
import '../../core/providers.dart';
import '../auth/auth_controller.dart';
import '../auth/login_sheet.dart';
import 'market_cards.dart';
import 'market_models.dart';
import 'markets_providers.dart';
import 'prediction_ticket.dart';

class MarketDetailScreen extends ConsumerStatefulWidget {
  const MarketDetailScreen({super.key, required this.slug});

  final String slug;

  @override
  ConsumerState<MarketDetailScreen> createState() => _MarketDetailScreenState();
}

class _MarketDetailScreenState extends ConsumerState<MarketDetailScreen> {
  int _tab = 0;

  @override
  Widget build(BuildContext context) {
    final detail = ref.watch(marketDetailProvider(widget.slug));
    final api = ref.watch(apiClientProvider);
    return Scaffold(
      body: detail.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) =>
            Center(child: Text(ApiFailure.fromObject(error).message)),
        data: (market) => CustomScrollView(
          slivers: [
            SliverAppBar(
              expandedHeight: 300,
              pinned: true,
              actions: [_MarketActionButtons(market: market)],
              flexibleSpace: FlexibleSpaceBar(
                background: MarketHeroCard(market: market, api: api),
              ),
            ),
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.all(16),
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
                    const SizedBox(height: 14),
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
        ),
        IconButton(
          tooltip: 'Curtir',
          onPressed: () =>
              _mutate(context, ref, auth.isAuthenticated, favorite: false),
          icon: Icon(
            market.viewerHasLike ? Icons.favorite : Icons.favorite_border,
          ),
        ),
        IconButton(
          tooltip: 'Compartilhar',
          onPressed: () => _shareMarket(context, ref, market),
          icon: const Icon(Icons.ios_share),
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

class _OverviewTab extends StatelessWidget {
  const _OverviewTab({required this.market});

  final Market market;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text('${market.category} · ${market.subcategory} · ${market.event}'),
        const SizedBox(height: 14),
        MarketMetricPanel(market: market),
        const SizedBox(height: 12),
        MarketSparklineCard(market: market),
        const SizedBox(height: 12),
        PredictionTicket(market: market),
        const SizedBox(height: 12),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Critério de resolução',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 8),
                Text(
                  market.resolutionCriteria.isEmpty
                      ? 'Critério não informado.'
                      : market.resolutionCriteria,
                ),
                if (market.isResolved) ...[
                  const SizedBox(height: 12),
                  Text(
                    'Resultado oficial',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 6),
                  Text(
                    market.resolutionNote.isEmpty
                        ? 'Resolvido em ${market.resolvedAtLabel}'
                        : market.resolutionNote,
                  ),
                ],
              ],
            ),
          ),
        ),
      ],
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
          const Card(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Text('Ainda não há comentários visíveis neste mercado.'),
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
          Card(
            child: Padding(
              padding: const EdgeInsets.all(14),
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
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
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
