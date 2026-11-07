import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/providers.dart';
import '../../theme.dart';
import '../../ui/gtl_components.dart';
import '../auth/auth_controller.dart';
import '../live_refresh.dart';
import 'market_cards.dart';
import 'market_models.dart';
import 'markets_providers.dart';

class TodayScreen extends ConsumerWidget {
  const TodayScreen({super.key, this.onOpenDesk});

  final ValueChanged<MarketDeskFilter>? onOpenDesk;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final markets = ref.watch(marketsProvider);
    final api = ref.watch(apiClientProvider);
    final auth = ref.watch(authControllerProvider);
    return markets.when(
      loading: () => const _MarketsLoading(),
      error: (error, stack) => _ErrorState(
        message: error.toString(),
        onRetry: () => ref.invalidate(marketsProvider),
      ),
      data: (items) {
        final openMarkets = _successfulOpenMarkets(items);
        if (openMarkets.isEmpty) {
          return GtlScreen(
            child: _RefreshableEmptyState(
              message: 'Nenhum mercado aberto disponível agora.',
              onRefresh: () => refreshMarkets(ref),
            ),
          );
        }
        final featured = openMarkets.take(3).toList();
        return GtlScreen(
          child: RefreshIndicator(
            onRefresh: () => refreshMarkets(ref),
            child: ListView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
              children: [
                GtlEditorialHeader(
                  kicker: 'Radar social',
                  title: auth.user == null
                      ? 'Hoje'
                      : 'Hoje, ${auth.user!.displayName}',
                  body: 'Mercados sociais, reputação pública e GT₵ educativo.',
                ),
                const SizedBox(height: 18),
                MarketHeroCard(
                  market: featured.first,
                  api: api,
                  showStatus: false,
                ),
                if (auth.isAuthenticated) ...[
                  const SizedBox(height: 16),
                  _DeskSnapshot(markets: items, onOpenDesk: onOpenDesk),
                ],
                const SizedBox(height: 20),
                GtlSectionTitle(
                  title: 'Tendências',
                  subtitle: '${featured.length} leituras em destaque',
                ),
                const SizedBox(height: 12),
                for (final market in featured.skip(1))
                  MarketCompactCard(
                    market: market,
                    api: api,
                    showStatus: false,
                  ),
                const SizedBox(height: 8),
                const GtlSectionTitle(
                  title: 'Mais mercados',
                  subtitle: 'Explore outros consensos em formação',
                ),
                const SizedBox(height: 12),
                for (final market in openMarkets.skip(3).take(8))
                  MarketCompactCard(
                    market: market,
                    api: api,
                    showStatus: false,
                  ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class MarketsScreen extends ConsumerStatefulWidget {
  const MarketsScreen({
    super.key,
    this.initialDeskFilter = MarketDeskFilter.all,
  });

  final MarketDeskFilter initialDeskFilter;

  @override
  ConsumerState<MarketsScreen> createState() => _MarketsScreenState();
}

class _MarketsScreenState extends ConsumerState<MarketsScreen> {
  late MarketDeskFilter _deskFilter;
  String _category = '';
  bool _pendingExpanded = true;

  @override
  void initState() {
    super.initState();
    _deskFilter = widget.initialDeskFilter;
    _pendingExpanded = true;
  }

  @override
  void didUpdateWidget(covariant MarketsScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.initialDeskFilter != oldWidget.initialDeskFilter) {
      setState(() {
        _deskFilter = widget.initialDeskFilter;
        _pendingExpanded = true;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final markets = ref.watch(marketsProvider);
    final api = ref.watch(apiClientProvider);
    final auth = ref.watch(authControllerProvider);
    return markets.when(
      loading: () => const _MarketsLoading(),
      error: (error, stack) => _ErrorState(
        message: error.toString(),
        onRetry: () => ref.invalidate(marketsProvider),
      ),
      data: (items) {
        final categories =
            items
                .map((m) => m.category)
                .where((c) => c.isNotEmpty)
                .toSet()
                .toList()
              ..sort();
        final publicItems = items
            .where(
              (market) =>
                  [
                    'open',
                    'locked',
                    'resolved',
                    'sealed',
                  ].contains(market.status) &&
                  (_category.isEmpty || market.category == _category),
            )
            .toList();
        final filtered = publicItems
            .where(
              (market) => switch (_deskFilter) {
                MarketDeskFilter.all => market.isOpen,
                MarketDeskFilter.resolved =>
                  market.isResolved || market.isSealed,
                MarketDeskFilter.favorites => market.viewerHasFavorite,
                MarketDeskFilter.positions => market.viewerHasActivePosition,
                MarketDeskFilter.predictions => market.viewerHasPrediction,
              },
            )
            .toList();
        final pendingEntries =
            publicItems
                .asMap()
                .entries
                .where((entry) => entry.value.status == 'locked')
                .toList()
              ..sort((a, b) {
                final left = DateTime.tryParse(a.value.closeAt);
                final right = DateTime.tryParse(b.value.closeAt);
                if (left == null && right != null) return 1;
                if (right == null && left != null) return -1;
                final byDate = left == null ? 0 : right!.compareTo(left);
                return byDate != 0 ? byDate : a.key.compareTo(b.key);
              });
        final pending = pendingEntries.map((entry) => entry.value).toList();
        return GtlScreen(
          child: Column(
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
                child: GtlEditorialHeader(
                  kicker: 'Browse',
                  title: 'Mercados',
                  body: _deskFilter == MarketDeskFilter.all
                      ? '${filtered.length} ${filtered.length == 1 ? 'aberto' : 'abertos'} · ${pending.length} em apuração.'
                      : '${filtered.length} de ${items.length} mercados neste recorte.',
                ),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 8, 16, 4),
                child: _DeskSegmentedControl(
                  selected: _deskFilter,
                  authenticated: auth.isAuthenticated,
                  onChanged: (value) => setState(() {
                    _deskFilter = value;
                    _pendingExpanded = true;
                  }),
                ),
              ),
              SizedBox(
                height: 54,
                child: ListView(
                  scrollDirection: Axis.horizontal,
                  padding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 8,
                  ),
                  children: [
                    FilterChip(
                      label: const Text('Todas'),
                      selected: _category.isEmpty,
                      onSelected: (_) => setState(() => _category = ''),
                    ),
                    const SizedBox(width: 8),
                    for (final category in categories) ...[
                      FilterChip(
                        label: Text(category),
                        selected: _category == category,
                        onSelected: (_) => setState(() => _category = category),
                      ),
                      const SizedBox(width: 8),
                    ],
                  ],
                ),
              ),
              if (auth.isAuthenticated)
                Align(
                  alignment: Alignment.centerRight,
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: TextButton.icon(
                      onPressed: () => setState(() {
                        _deskFilter = MarketDeskFilter.positions;
                        _pendingExpanded = true;
                      }),
                      icon: const Icon(Icons.stacked_line_chart, size: 18),
                      label: const Text('Posições ativas'),
                    ),
                  ),
                ),
              Expanded(
                child: RefreshIndicator(
                  onRefresh: () => refreshMarkets(ref),
                  child: ListView(
                    key: ValueKey(_deskFilter),
                    physics: const AlwaysScrollableScrollPhysics(),
                    padding: const EdgeInsets.fromLTRB(16, 10, 16, 24),
                    children: [
                      if (_deskFilter == MarketDeskFilter.positions)
                        const GtlSectionTitle(title: 'Posições ativas'),
                      if (filtered.isEmpty)
                        _EmptyState(
                          message: _emptyMessage(
                            _deskFilter,
                            auth.isAuthenticated,
                          ),
                        ),
                      for (final market in filtered)
                        MarketCompactCard(market: market, api: api),
                      if (_deskFilter == MarketDeskFilter.all &&
                          pending.isNotEmpty) ...[
                        Semantics(
                          expanded: _pendingExpanded,
                          child: OutlinedButton.icon(
                            key: const ValueKey('pending-markets-toggle'),
                            onPressed: () => setState(
                              () => _pendingExpanded = !_pendingExpanded,
                            ),
                            icon: Icon(
                              _pendingExpanded
                                  ? Icons.expand_less
                                  : Icons.expand_more,
                            ),
                            label: Text(
                              'Em apuração — ${pending.length} ${pending.length == 1 ? 'mercado' : 'mercados'}',
                            ),
                          ),
                        ),
                        if (_pendingExpanded)
                          for (final market in pending)
                            MarketCompactCard(market: market, api: api),
                      ],
                      if (_deskFilter == MarketDeskFilter.all &&
                          filtered.isEmpty &&
                          pending.isEmpty)
                        TextButton(
                          onPressed: () => setState(
                            () => _deskFilter = MarketDeskFilter.resolved,
                          ),
                          child: const Text('Ver resolvidos'),
                        ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

List<Market> _successfulOpenMarkets(List<Market> items) {
  return items.where((market) => market.isOpen).toList()..sort((a, b) {
    final byScore = b.engagementScore.compareTo(a.engagementScore);
    if (byScore != 0) {
      return byScore;
    }
    return a.title.compareTo(b.title);
  });
}

enum MarketDeskFilter { all, resolved, favorites, predictions, positions }

class _DeskSegmentedControl extends StatelessWidget {
  const _DeskSegmentedControl({
    required this.selected,
    required this.authenticated,
    required this.onChanged,
  });

  final MarketDeskFilter selected;
  final bool authenticated;
  final ValueChanged<MarketDeskFilter> onChanged;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: SegmentedButton<MarketDeskFilter>(
        segments: [
          const ButtonSegment(
            value: MarketDeskFilter.all,
            label: Text('Em andamento'),
          ),
          const ButtonSegment(
            value: MarketDeskFilter.resolved,
            label: Text('Resolvidos'),
          ),
          if (authenticated) ...[
            const ButtonSegment(
              value: MarketDeskFilter.favorites,
              label: Text('Favoritos'),
            ),
            const ButtonSegment(
              value: MarketDeskFilter.predictions,
              label: Text('Minhas previsões'),
            ),
          ],
        ],
        emptySelectionAllowed: true,
        selected: selected == MarketDeskFilter.positions ? {} : {selected},
        onSelectionChanged: (value) {
          if (value.isNotEmpty) onChanged(value.first);
        },
      ),
    );
  }
}

class _DeskSnapshot extends StatelessWidget {
  const _DeskSnapshot({required this.markets, required this.onOpenDesk});

  final List<Market> markets;
  final ValueChanged<MarketDeskFilter>? onOpenDesk;

  @override
  Widget build(BuildContext context) {
    final positions = markets
        .where((market) => market.viewerHasActivePosition)
        .length;
    final favorites = markets
        .where((market) => market.viewerHasFavorite)
        .length;
    final openPositions = markets
        .where((market) => market.viewerHasActivePosition && market.isOpen)
        .length;
    if (positions == 0 && favorites == 0) {
      return const SizedBox.shrink();
    }
    return GtlSurface(
      color: GtlColors.surfaceGlass,
      padding: const EdgeInsets.all(14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const GtlSectionTitle(
            title: 'Sua mesa',
            subtitle: 'Retome posições e mercados salvos',
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: _DeskActionTile(
                  key: const ValueKey('desk-tile-positions'),
                  label: 'Posições',
                  value: positions.toString(),
                  icon: Icons.stacked_line_chart,
                  color: GtlColors.accentGreen,
                  onTap: positions == 0
                      ? null
                      : () => onOpenDesk?.call(MarketDeskFilter.positions),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _DeskActionTile(
                  key: const ValueKey('desk-tile-favorites'),
                  label: 'Favoritos',
                  value: favorites.toString(),
                  icon: Icons.bookmark_border,
                  color: GtlColors.accentYellow,
                  onTap: favorites == 0
                      ? null
                      : () => onOpenDesk?.call(MarketDeskFilter.favorites),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _DeskActionTile(
                  key: const ValueKey('desk-tile-open-positions'),
                  label: 'Abertas',
                  value: openPositions.toString(),
                  icon: Icons.lock_open_outlined,
                  color: GtlColors.accentBlue,
                  onTap: openPositions == 0
                      ? null
                      : () => onOpenDesk?.call(MarketDeskFilter.positions),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _DeskActionTile extends StatelessWidget {
  const _DeskActionTile({
    super.key,
    required this.label,
    required this.value,
    required this.icon,
    required this.color,
    this.onTap,
  });

  final String label;
  final String value;
  final IconData icon;
  final Color color;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return GtlSurface(
      padding: const EdgeInsets.all(12),
      color: GtlColors.surface,
      borderColor: color.withValues(alpha: 0.42),
      onTap: onTap,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: Theme.of(context).textTheme.labelSmall,
          ),
          const SizedBox(height: 6),
          Row(
            children: [
              Icon(icon, color: color, size: 18),
              const SizedBox(width: 6),
              Expanded(
                child: FittedBox(
                  fit: BoxFit.scaleDown,
                  alignment: Alignment.centerLeft,
                  child: Text(
                    value,
                    style: Theme.of(context).textTheme.headlineSmall,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

String _emptyMessage(MarketDeskFilter filter, bool authenticated) {
  if (!authenticated &&
      ![MarketDeskFilter.all, MarketDeskFilter.resolved].contains(filter)) {
    return 'Entre para ver seus mercados salvos e suas previsões.';
  }
  return switch (filter) {
    MarketDeskFilter.all => 'Nenhum mercado aberto no momento.',
    MarketDeskFilter.resolved => 'Nenhum mercado resolvido ainda.',
    MarketDeskFilter.favorites =>
      'Você ainda não marcou mercados como favoritos.',
    MarketDeskFilter.positions => 'Você ainda não tem posições ativas.',
    MarketDeskFilter.predictions => 'Você ainda não registrou previsões.',
  };
}

class _MarketsLoading extends StatelessWidget {
  const _MarketsLoading();

  @override
  Widget build(BuildContext context) {
    return GtlScreen(
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: 6,
        itemBuilder: (context, index) => Padding(
          padding: const EdgeInsets.only(bottom: 12),
          child: GtlSkeletonBlock(height: index == 0 ? 308 : 118),
        ),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) => GtlStatePanel(
    icon: Icons.travel_explore,
    title: 'Nada neste recorte',
    body: message,
    color: GtlColors.accentYellow,
  );
}

class _RefreshableEmptyState extends StatelessWidget {
  const _RefreshableEmptyState({
    required this.message,
    required this.onRefresh,
  });

  final String message;
  final RefreshCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: onRefresh,
      child: LayoutBuilder(
        builder: (context, constraints) {
          final minHeight = constraints.hasBoundedHeight
              ? (constraints.maxHeight - 48).clamp(240.0, double.infinity)
              : 360.0;
          return ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.fromLTRB(16, 24, 16, 24),
            children: [
              ConstrainedBox(
                constraints: BoxConstraints(minHeight: minHeight),
                child: Center(child: _EmptyState(message: message)),
              ),
            ],
          );
        },
      ),
    );
  }
}

class _ErrorState extends StatelessWidget {
  const _ErrorState({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return GtlStatePanel(
      icon: Icons.cloud_off,
      title: 'API indisponível',
      body: message,
      color: GtlColors.accentYellow,
      action: OutlinedButton.icon(
        onPressed: onRetry,
        icon: const Icon(Icons.refresh),
        label: const Text('Tentar novamente'),
      ),
    );
  }
}

List<Market> searchMarkets(List<Market> markets, String query) {
  final q = query.trim().toLowerCase();
  if (q.isEmpty) {
    return markets;
  }
  return markets
      .where(
        (market) =>
            '${market.title} ${market.category} ${market.subcategory} ${market.event}'
                .toLowerCase()
                .contains(q),
      )
      .toList();
}
