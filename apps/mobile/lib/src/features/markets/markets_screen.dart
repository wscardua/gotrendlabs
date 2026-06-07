import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/providers.dart';
import '../../theme.dart';
import '../auth/auth_controller.dart';
import 'market_cards.dart';
import 'market_models.dart';
import 'markets_providers.dart';

class TodayScreen extends ConsumerWidget {
  const TodayScreen({super.key});

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
        if (items.isEmpty) {
          return const _EmptyState(message: 'Nenhum mercado disponível agora.');
        }
        final featured = items.take(3).toList();
        return RefreshIndicator(
          onRefresh: () async => ref.invalidate(marketsProvider),
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Text(
                auth.user == null ? 'Hoje' : 'Hoje, ${auth.user!.displayName}',
                style: Theme.of(context).textTheme.headlineSmall,
              ),
              const SizedBox(height: 6),
              const Text(
                'Mercados sociais, reputação pública e GT₵ educativo.',
              ),
              const SizedBox(height: 16),
              MarketHeroCard(market: featured.first, api: api),
              const SizedBox(height: 18),
              Text('Tendências', style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 10),
              for (final market in featured.skip(1))
                MarketCompactCard(market: market, api: api),
              const SizedBox(height: 10),
              Text(
                'Mais mercados',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 10),
              for (final market in items.skip(3).take(8))
                MarketCompactCard(market: market, api: api),
            ],
          ),
        );
      },
    );
  }
}

class MarketsScreen extends ConsumerStatefulWidget {
  const MarketsScreen({super.key});

  @override
  ConsumerState<MarketsScreen> createState() => _MarketsScreenState();
}

class _MarketsScreenState extends ConsumerState<MarketsScreen> {
  String _category = '';
  String _status = '';

  @override
  Widget build(BuildContext context) {
    final markets = ref.watch(marketsProvider);
    final api = ref.watch(apiClientProvider);
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
          final categoryOk = _category.isEmpty || market.category == _category;
          final statusOk = _status.isEmpty || market.status == _status;
          return categoryOk && statusOk;
        }).toList();
        return Column(
          children: [
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
                  ? const _EmptyState(message: 'Nenhum mercado neste recorte.')
                  : RefreshIndicator(
                      onRefresh: () async => ref.invalidate(marketsProvider),
                      child: ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: filtered.length,
                        itemBuilder: (context, index) => MarketCompactCard(
                          market: filtered[index],
                          api: api,
                        ),
                      ),
                    ),
            ),
          ],
        );
      },
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

class _MarketsLoading extends StatelessWidget {
  const _MarketsLoading();

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: 6,
      itemBuilder: (context, index) => Container(
        height: index == 0 ? 260 : 98,
        margin: const EdgeInsets.only(bottom: 12),
        decoration: BoxDecoration(
          color: GtlColors.surface,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: GtlColors.border),
        ),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) => Center(
    child: Padding(padding: const EdgeInsets.all(24), child: Text(message)),
  );
}

class _ErrorState extends StatelessWidget {
  const _ErrorState({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.cloud_off, color: GtlColors.accentYellow),
            const SizedBox(height: 12),
            Text(message, textAlign: TextAlign.center),
            const SizedBox(height: 12),
            OutlinedButton(
              onPressed: onRetry,
              child: const Text('Tentar novamente'),
            ),
          ],
        ),
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
