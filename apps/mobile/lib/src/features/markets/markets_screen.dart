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
  String _status = '';

  @override
  void initState() {
    super.initState();
    _deskFilter = widget.initialDeskFilter;
  }

  @override
  void didUpdateWidget(covariant MarketsScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.initialDeskFilter != oldWidget.initialDeskFilter) {
      setState(() => _deskFilter = widget.initialDeskFilter);
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
        final filtered = items.where((market) {
          final deskOk = switch (_deskFilter) {
            MarketDeskFilter.all => true,
            MarketDeskFilter.favorites => market.viewerHasFavorite,
            MarketDeskFilter.positions => market.viewerHasActivePosition,
          };
          final categoryOk = _category.isEmpty || market.category == _category;
          final statusOk = _status.isEmpty || market.status == _status;
          return deskOk && categoryOk && statusOk;
        }).toList();
        return GtlScreen(
          child: Column(
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
                child: GtlEditorialHeader(
                  kicker: 'Browse',
                  title: 'Mercados',
                  body:
                      '${filtered.length} de ${items.length} mercados neste recorte.',
                ),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 8, 16, 4),
                child: _DeskSegmentedControl(
                  selected: _deskFilter,
                  authenticated: auth.isAuthenticated,
                  onChanged: (value) => setState(() => _deskFilter = value),
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
              SizedBox(
                height: 48,
                child: ListView(
                  scrollDirection: Axis.horizontal,
                  padding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 4,
                  ),
                  children: [
                    _StatusChip(
                      label: 'Todos',
                      value: '',
                      selected: _status,
                      onChanged: (value) => setState(() => _status = value),
                    ),
                    _StatusChip(
                      label: 'Abertos',
                      value: 'open',
                      selected: _status,
                      onChanged: (value) => setState(() => _status = value),
                    ),
                    _StatusChip(
                      label: 'Em apuração',
                      value: 'locked',
                      selected: _status,
                      onChanged: (value) => setState(() => _status = value),
                    ),
                    _StatusChip(
                      label: 'Resolvidos',
                      value: 'resolved',
                      selected: _status,
                      onChanged: (value) => setState(() => _status = value),
                    ),
                  ],
                ),
              ),
              Expanded(
                child: filtered.isEmpty
                    ? _RefreshableEmptyState(
                        message: _emptyMessage(
                          _deskFilter,
                          auth.isAuthenticated,
                        ),
                        onRefresh: () => refreshMarkets(ref),
                      )
                    : RefreshIndicator(
                        onRefresh: () => refreshMarkets(ref),
                        child: ListView.builder(
                          physics: const AlwaysScrollableScrollPhysics(),
                          padding: const EdgeInsets.fromLTRB(16, 10, 16, 24),
                          itemCount: filtered.length,
                          itemBuilder: (context, index) {
                            final market = filtered[index];
                            return MarketCompactCard(
                              market: market,
                              api: api,
                              showStatus:
                                  _status.isNotEmpty || market.status != 'open',
                            );
                          },
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

enum MarketDeskFilter { all, favorites, positions }

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
    return SegmentedButton<MarketDeskFilter>(
      segments: const [
        ButtonSegment(
          value: MarketDeskFilter.all,
          label: Text('Todos'),
          icon: Icon(Icons.grid_view),
        ),
        ButtonSegment(
          value: MarketDeskFilter.favorites,
          label: Text('Favoritos'),
          icon: Icon(Icons.bookmark_border),
        ),
        ButtonSegment(
          value: MarketDeskFilter.positions,
          label: Text('Posições'),
          icon: Icon(Icons.stacked_line_chart),
        ),
      ],
      selected: {selected},
      onSelectionChanged: authenticated
          ? (value) => onChanged(value.first)
          : (value) {
              if (value.first == MarketDeskFilter.all) {
                onChanged(value.first);
              }
            },
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
          Icon(icon, color: color, size: 18),
          const SizedBox(height: 10),
          FittedBox(
            fit: BoxFit.scaleDown,
            alignment: Alignment.centerLeft,
            child: Text(
              value,
              style: Theme.of(context).textTheme.headlineSmall,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            label,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: Theme.of(context).textTheme.labelSmall,
          ),
        ],
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({
    required this.label,
    required this.value,
    required this.selected,
    required this.onChanged,
  });

  final String label;
  final String value;
  final String selected;
  final ValueChanged<String> onChanged;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: ChoiceChip(
        label: Text(label),
        selected: selected == value,
        onSelected: (_) => onChanged(value),
      ),
    );
  }
}

String _emptyMessage(MarketDeskFilter filter, bool authenticated) {
  if (!authenticated && filter != MarketDeskFilter.all) {
    return 'Entre para ver seus mercados salvos e suas posições.';
  }
  return switch (filter) {
    MarketDeskFilter.all => 'Nenhum mercado neste recorte.',
    MarketDeskFilter.favorites =>
      'Você ainda não marcou mercados como favoritos.',
    MarketDeskFilter.positions => 'Você ainda não tem posições neste recorte.',
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
