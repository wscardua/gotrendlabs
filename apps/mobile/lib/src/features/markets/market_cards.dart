import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/api_client.dart';
import '../../core/formatters.dart';
import '../../theme.dart';
import '../../ui/gtl_components.dart';
import 'market_models.dart';
import 'sparkline_painter.dart';

class MarketHeroCard extends StatelessWidget {
  const MarketHeroCard({
    super.key,
    required this.market,
    required this.api,
    this.openOnTap = true,
    this.showStatus = true,
  });

  final Market market;
  final ApiClient api;
  final bool openOnTap;
  final bool showStatus;

  @override
  Widget build(BuildContext context) {
    final card = Ink(
      height: 334,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(GtlRadii.large),
        border: Border.all(color: GtlColors.borderStrong),
        color: GtlColors.surface,
        boxShadow: GtlShadows.glow(
          _statusColor(market),
          opacity: market.isOpen ? 0.18 : 0.10,
        ),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(GtlRadii.large),
        child: Stack(
          fit: StackFit.expand,
          children: [
            _MarketImage(market: market, api: api),
            DecoratedBox(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [
                    Colors.black.withValues(alpha: 0.08),
                    Colors.black.withValues(alpha: 0.24),
                    const Color(0xF2050608),
                  ],
                  stops: const [0.0, 0.42, 1.0],
                ),
              ),
            ),
            Positioned(
              top: 0,
              right: 0,
              bottom: 0,
              child: Container(
                width: 112,
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.centerRight,
                    end: Alignment.centerLeft,
                    colors: [
                      _statusColor(market).withValues(alpha: 0.20),
                      Colors.transparent,
                    ],
                  ),
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
                      GtlPill(
                        label: market.category.isEmpty
                            ? 'Mercado'
                            : market.category,
                        icon: Icons.category_outlined,
                      ),
                      if (showStatus)
                        GtlPill(
                          label: market.statusLabel,
                          icon: market.isOpen
                              ? Icons.radio_button_checked
                              : Icons.lock_clock,
                          color: _statusColor(market),
                          filled: true,
                        ),
                      ..._viewerPills(market),
                    ],
                  ),
                  const Spacer(),
                  Text(
                    market.title,
                    maxLines: 3,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.headlineMedium,
                  ),
                  const SizedBox(height: 16),
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      _ProbabilityPill(label: market.probabilityLabel),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Wrap(
                          spacing: 8,
                          runSpacing: 8,
                          children: [
                            _HeroMeta(
                              icon: Icons.savings_outlined,
                              label: market.volumeLabel,
                            ),
                            _HeroMeta(
                              icon: Icons.groups_2_outlined,
                              label:
                                  '${market.humanParticipants} participantes',
                            ),
                            _HeroMeta(
                              icon: Icons.timer_outlined,
                              label: market.timeRemainingLabel,
                            ),
                          ],
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
    return Material(
      color: Colors.transparent,
      child: openOnTap
          ? InkWell(
              borderRadius: BorderRadius.circular(GtlRadii.large),
              onTap: () => context.push('/markets/${market.slug}'),
              child: card,
            )
          : card,
    );
  }
}

class MarketCompactCard extends StatelessWidget {
  const MarketCompactCard({
    super.key,
    required this.market,
    required this.api,
    this.showStatus = true,
  });

  final Market market;
  final ApiClient api;
  final bool showStatus;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: GtlSurface(
        padding: EdgeInsets.zero,
        color: GtlColors.surfaceGlass,
        onTap: () => context.push('/markets/${market.slug}'),
        child: Row(
          children: [
            SizedBox(
              width: 104,
              height: 118,
              child: ClipRRect(
                borderRadius: const BorderRadius.horizontal(
                  left: Radius.circular(GtlRadii.medium),
                ),
                child: Stack(
                  fit: StackFit.expand,
                  children: [
                    _MarketImage(market: market, api: api),
                    DecoratedBox(
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          begin: Alignment.topCenter,
                          end: Alignment.bottomCenter,
                          colors: [
                            Colors.transparent,
                            Colors.black.withValues(alpha: 0.56),
                          ],
                        ),
                      ),
                    ),
                    if (showStatus)
                      Positioned(
                        left: 8,
                        bottom: 8,
                        child: GtlPill(
                          label: market.statusLabel,
                          color: _statusColor(market),
                          filled: true,
                        ),
                      ),
                  ],
                ),
              ),
            ),
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            market.category.isEmpty
                                ? 'Mercado'
                                : market.category.toUpperCase(),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: Theme.of(context).textTheme.labelSmall
                                ?.copyWith(color: GtlColors.accentCyan),
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
                      style: Theme.of(
                        context,
                      ).textTheme.titleMedium?.copyWith(height: 1.08),
                    ),
                    if (_viewerPills(market).isNotEmpty) ...[
                      const SizedBox(height: 8),
                      Wrap(
                        spacing: 6,
                        runSpacing: 6,
                        children: _viewerPills(market, dense: true),
                      ),
                    ],
                    const SizedBox(height: 10),
                    Row(
                      children: [
                        _InlineMetric(
                          icon: Icons.savings_outlined,
                          label: market.volumeLabel,
                        ),
                        const SizedBox(width: 10),
                        _InlineMetric(
                          icon: Icons.forum_outlined,
                          label: '${market.commentCount}',
                        ),
                        const SizedBox(width: 8),
                        if (showStatus)
                          Expanded(
                            child: _InlineMetric(
                              icon: Icons.timer_outlined,
                              label: market.timeRemainingLabel,
                              flexible: true,
                            ),
                          )
                        else
                          Expanded(
                            child: Align(
                              alignment: Alignment.centerRight,
                              child: _InlineTimeRail(
                                label: market.timeRemainingLabel,
                                progress: _timeUrgencyProgress(market),
                              ),
                            ),
                          ),
                      ],
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

class MarketMetricPanel extends StatelessWidget {
  const MarketMetricPanel({super.key, required this.market});

  final Market market;

  @override
  Widget build(BuildContext context) {
    final metrics = [
      (
        'Probabilidade',
        market.probabilityLabel,
        Icons.stacked_line_chart,
        GtlColors.accentGreen,
      ),
      (
        'Volume GT₵',
        market.volumeLabel,
        Icons.savings_outlined,
        GtlColors.accentBlue,
      ),
      (
        'Participantes',
        market.humanParticipants.toString(),
        Icons.groups_2_outlined,
        GtlColors.accentCyan,
      ),
      (
        'Comentários',
        market.commentCount.toString(),
        Icons.forum_outlined,
        GtlColors.accentViolet,
      ),
      (
        'Encerra em',
        market.closesIn.isEmpty ? 'fim' : market.closesIn,
        Icons.timer_outlined,
        GtlColors.accentYellow,
      ),
      ('Status', market.statusLabel, Icons.flag_outlined, _statusColor(market)),
    ];
    return GtlSurface(
      color: GtlColors.surfaceGlass,
      padding: const EdgeInsets.all(14),
      child: Column(
        children: [
          for (var index = 0; index < metrics.length; index += 2) ...[
            SizedBox(
              height: 124,
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Expanded(child: _MetricFromRecord(metric: metrics[index])),
                  const SizedBox(width: 10),
                  Expanded(
                    child: _MetricFromRecord(metric: metrics[index + 1]),
                  ),
                ],
              ),
            ),
            if (index < metrics.length - 2) const SizedBox(height: 10),
          ],
        ],
      ),
    );
  }
}

class _MetricFromRecord extends StatelessWidget {
  const _MetricFromRecord({required this.metric});

  final (String, String, IconData, Color) metric;

  @override
  Widget build(BuildContext context) {
    return GtlMetricTile(
      label: metric.$1,
      value: metric.$2,
      icon: metric.$3,
      color: metric.$4,
    );
  }
}

class MarketSparklineCard extends StatelessWidget {
  const MarketSparklineCard({super.key, required this.market});

  final Market market;

  @override
  Widget build(BuildContext context) {
    return GtlSurface(
      color: GtlColors.surfaceGlass,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const GtlSectionTitle(
            title: 'Consenso',
            subtitle: 'Histórico compacto da leitura pública',
          ),
          const SizedBox(height: 12),
          _ConsensusChart(market: market),
          const SizedBox(height: 10),
          Text(compactText(market.summary, max: 160)),
        ],
      ),
    );
  }
}

class _ConsensusChart extends StatelessWidget {
  const _ConsensusChart({required this.market});

  final Market market;

  static const _colors = [
    GtlColors.accentBlue,
    GtlColors.accentGreen,
    GtlColors.accentYellow,
    GtlColors.accentViolet,
    GtlColors.accentRed,
    GtlColors.accentCyan,
  ];

  @override
  Widget build(BuildContext context) {
    final series = market.sparklineSeries
        .where((item) => safeString(item['path']).isNotEmpty)
        .toList();
    if (series.length < 2) {
      return SparklinePath(path: market.sparklinePath, height: 56);
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          height: 68,
          child: Stack(
            children: [
              for (var index = 0; index < series.length; index++)
                Positioned.fill(
                  child: SparklinePath(
                    path: safeString(series[index]['path']),
                    color: _colors[index % _colors.length],
                    height: 68,
                  ),
                ),
            ],
          ),
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 6,
          children: [
            for (var index = 0; index < series.length; index++)
              _SeriesLegend(
                color: _colors[index % _colors.length],
                label: safeString(series[index]['label'], 'Opção'),
              ),
          ],
        ),
      ],
    );
  }
}

class _SeriesLegend extends StatelessWidget {
  const _SeriesLegend({required this.color, required this.label});

  final Color color;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        DecoratedBox(
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(GtlRadii.pill),
          ),
          child: const SizedBox(width: 18, height: 4),
        ),
        const SizedBox(width: 5),
        ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 96),
          child: Text(
            label,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ),
      ],
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
      return CachedNetworkImage(
        imageUrl: image,
        fit: BoxFit.cover,
        placeholder: (context, url) => _FallbackMarketArt(market: market),
        errorWidget: (context, url, error) =>
            _FallbackMarketArt(market: market),
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
          colors: [
            color.withValues(alpha: 0.88),
            GtlColors.surfaceInk,
            GtlColors.surface,
          ],
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
                  color: Colors.black.withValues(alpha: 0.20),
                  borderRadius: BorderRadius.circular(GtlRadii.pill),
                  border: Border.all(
                    color: Colors.white.withValues(alpha: 0.16),
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

class _HeroMeta extends StatelessWidget {
  const _HeroMeta({required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 15, color: GtlColors.textSecondary),
        const SizedBox(width: 5),
        Text(
          label,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            color: GtlColors.textSecondary,
            fontWeight: FontWeight.w700,
          ),
        ),
      ],
    );
  }
}

class _InlineMetric extends StatelessWidget {
  const _InlineMetric({
    required this.icon,
    required this.label,
    this.flexible = false,
  });

  final IconData icon;
  final String label;
  final bool flexible;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: flexible
          ? MainAxisAlignment.end
          : MainAxisAlignment.start,
      mainAxisSize: flexible ? MainAxisSize.max : MainAxisSize.min,
      children: [
        Icon(icon, size: 14, color: GtlColors.muted),
        const SizedBox(width: 4),
        if (flexible)
          Flexible(child: _InlineMetricLabel(label: label))
        else
          _InlineMetricLabel(label: label),
      ],
    );
  }
}

class _InlineMetricLabel extends StatelessWidget {
  const _InlineMetricLabel({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Text(
      label,
      maxLines: 1,
      overflow: TextOverflow.ellipsis,
      style: Theme.of(
        context,
      ).textTheme.bodySmall?.copyWith(color: GtlColors.textSecondary),
    );
  }
}

class _InlineTimeRail extends StatelessWidget {
  const _InlineTimeRail({required this.label, required this.progress});

  final String label;
  final double progress;

  @override
  Widget build(BuildContext context) {
    final urgencyColor = _timeUrgencyColor(progress);
    return ConstrainedBox(
      constraints: const BoxConstraints(maxWidth: 92),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Flexible(
            child: Text(
              label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: urgencyColor,
                fontWeight: FontWeight.w800,
              ),
            ),
          ),
          const SizedBox(width: 6),
          SizedBox(
            width: 36,
            child: ClipRRect(
              borderRadius: BorderRadius.circular(GtlRadii.pill),
              child: LinearProgressIndicator(
                minHeight: 4,
                value: progress,
                backgroundColor: urgencyColor.withValues(alpha: 0.16),
                valueColor: AlwaysStoppedAnimation<Color>(urgencyColor),
              ),
            ),
          ),
        ],
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
        color: GtlColors.accentGreen.withValues(alpha: 0.18),
        borderRadius: BorderRadius.circular(GtlRadii.pill),
        border: Border.all(
          color: GtlColors.accentGreen.withValues(alpha: 0.62),
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

List<Widget> _viewerPills(Market market, {bool dense = false}) {
  final pills = <Widget>[];
  if (market.viewerHasPrediction) {
    pills.add(
      GtlPill(
        label: dense ? 'Posição' : 'Sua posição',
        icon: dense ? null : Icons.stacked_line_chart,
        color: GtlColors.accentGreen,
        filled: true,
      ),
    );
  }
  if (market.viewerHasFavorite) {
    pills.add(
      GtlPill(
        label: dense ? 'Favorito' : 'Favorito',
        icon: dense ? null : Icons.bookmark,
        color: GtlColors.accentYellow,
        filled: true,
      ),
    );
  }
  return pills;
}

double _timeUrgencyProgress(Market market) {
  if (!market.isOpen) {
    return 1;
  }
  final remainingHours = _remainingHours(market.closesIn);
  if (remainingHours == null) {
    return 0.24;
  }
  const displayWindowHours = 30 * 24;
  final progress = 1 - (remainingHours / displayWindowHours);
  return progress.clamp(0.08, 0.96);
}

Color _timeUrgencyColor(double progress) {
  final normalized = progress.clamp(0.0, 1.0);
  if (normalized < 0.48) {
    return Color.lerp(
      GtlColors.accentCyan,
      GtlColors.accentGreen,
      normalized / 0.48,
    )!;
  }
  if (normalized < 0.78) {
    return Color.lerp(
      GtlColors.accentGreen,
      GtlColors.accentYellow,
      (normalized - 0.48) / 0.30,
    )!;
  }
  if (normalized >= 0.94) {
    return GtlColors.accentRed;
  }
  return Color.lerp(
    GtlColors.accentYellow,
    GtlColors.accentRed,
    (normalized - 0.78) / 0.22,
  )!;
}

double? _remainingHours(String value) {
  final normalized = value.trim().toLowerCase();
  if (normalized.isEmpty || normalized == 'fim') {
    return null;
  }
  final match = RegExp(r'^(\d+(?:[,.]\d+)?)([dhm])$').firstMatch(normalized);
  if (match == null) {
    return null;
  }
  final amount = double.tryParse(match.group(1)!.replaceAll(',', '.'));
  if (amount == null) {
    return null;
  }
  return switch (match.group(2)) {
    'd' => amount * 24,
    'h' => amount,
    'm' => amount / 60,
    _ => null,
  };
}

Color _hexColor(String value) {
  final normalized = value.replaceFirst('#', '');
  final parsed = int.tryParse('FF$normalized', radix: 16);
  return Color(parsed ?? 0xFF11151B);
}
