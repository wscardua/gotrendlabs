import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/api_client.dart';
import '../../core/formatters.dart';
import '../../theme.dart';
import 'market_models.dart';
import 'sparkline_painter.dart';

class MarketHeroCard extends StatelessWidget {
  const MarketHeroCard({super.key, required this.market, required this.api});

  final Market market;
  final ApiClient api;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => context.push('/markets/${market.slug}'),
      child: Container(
        height: 318,
        clipBehavior: Clip.antiAlias,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: GtlColors.border),
          color: GtlColors.surface,
        ),
        child: Stack(
          fit: StackFit.expand,
          children: [
            _MarketImage(market: market, api: api),
            const DecoratedBox(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [
                    Colors.transparent,
                    Color(0xD9050608),
                    Color(0xFF050608),
                  ],
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      _Chip(label: market.category),
                      _Chip(
                        label: market.statusLabel,
                        color: _statusColor(market),
                      ),
                    ],
                  ),
                  const Spacer(),
                  Text(
                    market.title,
                    maxLines: 3,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(
                      context,
                    ).textTheme.headlineSmall?.copyWith(height: 1.04),
                  ),
                  const SizedBox(height: 14),
                  Row(
                    children: [
                      _ProbabilityPill(label: market.probabilityLabel),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          '${market.volumeLabel} · ${market.humanParticipants} participantes',
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class MarketCompactCard extends StatelessWidget {
  const MarketCompactCard({super.key, required this.market, required this.api});

  final Market market;
  final ApiClient api;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        borderRadius: BorderRadius.circular(8),
        onTap: () => context.push('/markets/${market.slug}'),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Row(
            children: [
              SizedBox(
                width: 86,
                height: 86,
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(8),
                  child: _MarketImage(market: market, api: api),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            market.category,
                            style: Theme.of(context).textTheme.labelMedium,
                          ),
                        ),
                        _ProbabilityPill(
                          label: market.probabilityLabel,
                          dense: true,
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      market.title,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 10),
                    Text(
                      '${market.volumeLabel} · ${market.commentCount} comentários · ${market.closeLabel}',
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class MarketMetricPanel extends StatelessWidget {
  const MarketMetricPanel({super.key, required this.market});

  final Market market;

  @override
  Widget build(BuildContext context) {
    final metrics = [
      ('Probabilidade', market.probabilityLabel),
      ('Volume GT₵', market.volumeLabel),
      ('Participantes', market.humanParticipants.toString()),
      ('Comentários', market.commentCount.toString()),
      ('Encerra em', market.closesIn.isEmpty ? 'fim' : market.closesIn),
      ('Status', market.statusLabel),
    ];
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: GridView.count(
          crossAxisCount: 2,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          childAspectRatio: 2.15,
          mainAxisSpacing: 10,
          crossAxisSpacing: 10,
          children: [
            for (final metric in metrics)
              DecoratedBox(
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(8),
                  color: GtlColors.surfaceElevated,
                  border: Border.all(color: GtlColors.border),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(10),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        metric.$1.toUpperCase(),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: Theme.of(context).textTheme.labelSmall,
                      ),
                      const SizedBox(height: 4),
                      FittedBox(
                        fit: BoxFit.scaleDown,
                        alignment: Alignment.centerLeft,
                        child: Text(
                          metric.$2,
                          maxLines: 1,
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                      ),
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

class MarketSparklineCard extends StatelessWidget {
  const MarketSparklineCard({super.key, required this.market});

  final Market market;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Consenso', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 10),
            SparklinePath(path: market.sparklinePath),
            const SizedBox(height: 8),
            Text(compactText(market.summary, max: 160)),
          ],
        ),
      ),
    );
  }
}

class _MarketImage extends StatelessWidget {
  const _MarketImage({required this.market, required this.api});

  final Market market;
  final ApiClient api;

  @override
  Widget build(BuildContext context) {
    final image = api.resolveUrl(market.imageUrl);
    if (image.isNotEmpty) {
      return Stack(
        fit: StackFit.expand,
        children: [
          CachedNetworkImage(
            imageUrl: image,
            fit: BoxFit.cover,
            placeholder: (context, url) => _FallbackMarketArt(market: market),
            errorWidget: (context, url, error) =>
                _FallbackMarketArt(market: market),
          ),
        ],
      );
    }
    return _FallbackMarketArt(market: market);
  }
}

class _FallbackMarketArt extends StatelessWidget {
  const _FallbackMarketArt({required this.market});

  final Market market;

  @override
  Widget build(BuildContext context) {
    final color = _hexColor(market.thumbColor);
    return DecoratedBox(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [color.withValues(alpha: 0.8), GtlColors.surface],
        ),
      ),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final compact = constraints.maxHeight < 120;
          final textStyle = compact
              ? Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.w900,
                  color: Colors.white,
                )
              : Theme.of(context).textTheme.displaySmall?.copyWith(
                  fontSize: 54,
                  fontWeight: FontWeight.w900,
                );
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(10),
              child: DecoratedBox(
                decoration: BoxDecoration(
                  color: Colors.black.withValues(alpha: 0.16),
                  borderRadius: BorderRadius.circular(999),
                  border: Border.all(
                    color: Colors.white.withValues(alpha: 0.12),
                  ),
                ),
                child: Padding(
                  padding: EdgeInsets.symmetric(
                    horizontal: compact ? 10 : 18,
                    vertical: compact ? 10 : 18,
                  ),
                  child: market.thumb.trim().isEmpty
                      ? Icon(
                          Icons.auto_graph,
                          color: Colors.white.withValues(alpha: 0.86),
                          size: compact ? 28 : 46,
                        )
                      : FittedBox(
                          fit: BoxFit.scaleDown,
                          child: Text(
                            market.thumb,
                            maxLines: 1,
                            style: textStyle,
                          ),
                        ),
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}

class _Chip extends StatelessWidget {
  const _Chip({required this.label, this.color});

  final String label;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: (color ?? GtlColors.surfaceElevated).withValues(alpha: 0.82),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: GtlColors.border),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        child: Text(
          label,
          style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 12),
        ),
      ),
    );
  }
}

class _ProbabilityPill extends StatelessWidget {
  const _ProbabilityPill({required this.label, this.dense = false});

  final String label;
  final bool dense;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: GtlColors.accentGreen.withValues(alpha: 0.16),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(
          color: GtlColors.accentGreen.withValues(alpha: 0.56),
        ),
      ),
      child: Padding(
        padding: EdgeInsets.symmetric(
          horizontal: dense ? 8 : 12,
          vertical: dense ? 4 : 7,
        ),
        child: Text(
          label,
          style: TextStyle(
            color: GtlColors.accentGreen,
            fontWeight: FontWeight.w900,
            fontSize: dense ? 12 : 15,
          ),
        ),
      ),
    );
  }
}

Color _statusColor(Market market) {
  if (market.isOpen) {
    return GtlColors.accentGreen;
  }
  if (market.isResolved) {
    return GtlColors.accentViolet;
  }
  if (market.isLocked) {
    return GtlColors.accentYellow;
  }
  return GtlColors.surfaceElevated;
}

Color _hexColor(String value) {
  final normalized = value.replaceFirst('#', '');
  final parsed = int.tryParse('FF$normalized', radix: 16);
  return Color(parsed ?? 0xFF11151B);
}
