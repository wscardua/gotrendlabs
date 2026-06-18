import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_client.dart';
import '../../core/formatters.dart';
import '../../theme.dart';
import '../../ui/gtl_components.dart';
import '../auth/auth_controller.dart';
import '../auth/login_sheet.dart';
import '../live_refresh.dart';
import '../profile/badges_screen.dart';
import 'performance_providers.dart';

class PerformanceScreen extends ConsumerStatefulWidget {
  const PerformanceScreen({super.key});

  @override
  ConsumerState<PerformanceScreen> createState() => _PerformanceScreenState();
}

class _PerformanceScreenState extends ConsumerState<PerformanceScreen>
    with WidgetsBindingObserver {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      refreshPerformanceData(ref);
    });
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      refreshPerformanceData(ref);
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);
    final performance = auth.isAuthenticated
        ? ref.watch(performanceProvider)
        : null;
    return Scaffold(
      appBar: AppBar(title: const Text('Desempenho')),
      body: GtlScreen(
        child: !auth.isAuthenticated
            ? _PerformanceAuthRequired(onLogin: () => showLoginSheet(context))
            : performance!.when(
                loading: () => const Center(child: CircularProgressIndicator()),
                error: (error, stack) => GtlStatePanel(
                  icon: Icons.cloud_off,
                  title: 'Desempenho indisponível',
                  body: ApiFailure.fromObject(error).message,
                  color: GtlColors.accentYellow,
                  action: FilledButton.icon(
                    onPressed: () => refreshPerformanceData(ref),
                    icon: const Icon(Icons.refresh),
                    label: const Text('Atualizar'),
                  ),
                ),
                data: (payload) => RefreshIndicator(
                  onRefresh: () => refreshPerformanceData(ref),
                  child: ListView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
                    children: [
                      const GtlEditorialHeader(
                        kicker: 'Evolução preditiva',
                        title: 'Desempenho',
                        body:
                            'Dados atualizados com suas resoluções, reputação e conquistas.',
                        icon: Icons.query_stats,
                      ),
                      const SizedBox(height: 14),
                      _ScorecardPanel(scorecard: _map(payload['scorecard'])),
                      const SizedBox(height: 12),
                      _HistoryPanel(history: _maps(payload['history'])),
                      const SizedBox(height: 12),
                      _ProgressionPanel(
                        progression: _map(payload['progression']),
                      ),
                    ],
                  ),
                ),
              ),
      ),
    );
  }
}

class _ScorecardPanel extends StatelessWidget {
  const _ScorecardPanel({required this.scorecard});

  final Map<String, dynamic> scorecard;

  @override
  Widget build(BuildContext context) {
    final metrics = [
      (
        'Reputação',
        safeInt(scorecard['reputation_score']).toString(),
        Icons.auto_graph,
        GtlColors.accentBlue,
      ),
      (
        'Posição',
        '#${safeInt(scorecard['ranking_position'])}',
        Icons.leaderboard_outlined,
        GtlColors.accentCyan,
      ),
      (
        'Resolvidas',
        safeInt(scorecard['resolved_predictions_count']).toString(),
        Icons.verified_outlined,
        GtlColors.accentGreen,
      ),
      (
        'Precisão',
        safeString(scorecard['accuracy_indicator'], '0%'),
        Icons.my_location,
        GtlColors.accentYellow,
      ),
      (
        'Sequência',
        safeInt(scorecard['streak']).toString(),
        Icons.timeline,
        GtlColors.accentViolet,
      ),
      (
        'Categoria forte',
        safeString(scorecard['strong_category']).isNotEmpty
            ? safeString(scorecard['strong_category'])
            : 'Em formação',
        Icons.category_outlined,
        GtlColors.accentGreen,
      ),
    ];
    return GtlSurface(
      color: GtlColors.surfaceGlass,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const GtlSectionTitle(
            title: 'Placar',
            subtitle: 'Sinais atuais de evolução preditiva',
          ),
          const SizedBox(height: 12),
          GridView.count(
            crossAxisCount: 2,
            childAspectRatio: 1.58,
            mainAxisSpacing: 10,
            crossAxisSpacing: 10,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            children: [
              for (final metric in metrics)
                GtlMetricTile(
                  label: metric.$1,
                  value: metric.$2,
                  icon: metric.$3,
                  color: metric.$4,
                ),
            ],
          ),
        ],
      ),
    );
  }
}

class _HistoryPanel extends StatelessWidget {
  const _HistoryPanel({required this.history});

  final List<Map<String, dynamic>> history;

  @override
  Widget build(BuildContext context) {
    return GtlSurface(
      color: GtlColors.surfaceGlass,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const GtlSectionTitle(
            title: 'Histórico',
            subtitle: 'Últimas resoluções auditáveis',
          ),
          const SizedBox(height: 12),
          if (history.isEmpty)
            const _EmptyLine(
              icon: Icons.fact_check_outlined,
              title: 'Nenhuma previsão resolvida ainda',
              body:
                  'Quando seus mercados forem resolvidos, os impactos aparecerão aqui.',
            )
          else
            for (final item in history.take(8)) ...[
              _HistoryItem(item: item),
              if (item != history.take(8).last) const SizedBox(height: 10),
            ],
        ],
      ),
    );
  }
}

class _HistoryItem extends StatelessWidget {
  const _HistoryItem({required this.item});

  final Map<String, dynamic> item;

  @override
  Widget build(BuildContext context) {
    final won = item['won'] == true;
    final reputationDelta = safeInt(item['reputation_delta']);
    final gtcResult = safeInt(item['gtc_result']);
    final resultLabel = won
        ? 'Acertou'
        : item.containsKey('won')
        ? 'Não acertou'
        : safeString(item['result_label'], 'Resultado');
    final resultColor = won ? GtlColors.accentGreen : GtlColors.accentYellow;
    return DecoratedBox(
      decoration: BoxDecoration(
        color: GtlColors.surfaceInk,
        border: Border.all(color: GtlColors.border),
        borderRadius: BorderRadius.circular(GtlRadii.medium),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    safeString(item['market_title'], 'Mercado'),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
                const SizedBox(width: 8),
                GtlPill(
                  label: resultLabel,
                  icon: won ? Icons.check_circle_outline : Icons.info_outline,
                  color: resultColor,
                  filled: true,
                ),
              ],
            ),
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                GtlPill(
                  label: 'Previsão: ${safeString(item['option_label'], '-')}',
                  icon: Icons.psychology_alt_outlined,
                  color: GtlColors.accentBlue,
                ),
                if (safeString(item['winning_option_label']).isNotEmpty)
                  GtlPill(
                    label:
                        'Resultado: ${safeString(item['winning_option_label'])}',
                    icon: Icons.verified_outlined,
                    color: GtlColors.accentGreen,
                  ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: _InlineMetric(
                    label: 'Impacto reputação',
                    value: _signed(reputationDelta),
                    color: reputationDelta >= 0
                        ? GtlColors.accentGreen
                        : GtlColors.accentRed,
                  ),
                ),
                Expanded(
                  child: _InlineMetric(
                    label: 'GT₵ educativo',
                    value: safeString(
                      item['educational_result_label'],
                      formatGtl(gtcResult),
                    ),
                    color: gtcResult >= 0
                        ? GtlColors.accentGreen
                        : GtlColors.accentRed,
                  ),
                ),
              ],
            ),
            if (safeString(item['resolved_at_label']).isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(
                safeString(item['resolved_at_label']),
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _ProgressionPanel extends StatelessWidget {
  const _ProgressionPanel({required this.progression});

  final Map<String, dynamic> progression;

  @override
  Widget build(BuildContext context) {
    final badges = _maps(progression['badges']);
    final latest = _maps(progression['latest_awards']);
    final earnedCount = safeInt(progression['earned_badges_count']);
    final shown = latest.isNotEmpty ? latest : badges.take(5).toList();
    final api = ApiClient();
    return GtlSurface(
      color: GtlColors.surfaceGlass,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          GtlSectionTitle(
            title: 'Progressão',
            subtitle: 'Conquistas registradas no seu perfil',
            trailing: GtlPill(
              label: '$earnedCount',
              icon: Icons.workspace_premium_outlined,
              color: GtlColors.accentViolet,
              filled: true,
            ),
          ),
          const SizedBox(height: 12),
          if (shown.isEmpty)
            const _EmptyLine(
              icon: Icons.workspace_premium_outlined,
              title: 'Sem badges conquistadas',
              body:
                  'As conquistas aparecem aqui conforme sua participação evolui.',
            )
          else
            for (final badge in shown) ...[
              Row(
                children: [
                  BadgeArt(badge: badge, api: api, size: 44),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          safeString(badge['name'], 'Badge'),
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                        Text(
                          safeString(badge['description']),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              if (badge != shown.last) const SizedBox(height: 10),
            ],
          const SizedBox(height: 12),
          Text(
            'Próximos marcos aparecem quando houver dados suficientes para acompanhar com confiança.',
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ),
    );
  }
}

class _InlineMetric extends StatelessWidget {
  const _InlineMetric({
    required this.label,
    required this.value,
    required this.color,
  });

  final String label;
  final String value;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label.toUpperCase(),
          style: Theme.of(context).textTheme.labelSmall,
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: Theme.of(
            context,
          ).textTheme.titleMedium?.copyWith(color: color),
        ),
      ],
    );
  }
}

class _EmptyLine extends StatelessWidget {
  const _EmptyLine({
    required this.icon,
    required this.title,
    required this.body,
  });

  final IconData icon;
  final String title;
  final String body;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: GtlColors.surfaceInk,
        border: Border.all(color: GtlColors.border),
        borderRadius: BorderRadius.circular(GtlRadii.medium),
      ),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(
          children: [
            Icon(icon, color: GtlColors.accentBlue),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 4),
                  Text(body, style: Theme.of(context).textTheme.bodySmall),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _PerformanceAuthRequired extends StatelessWidget {
  const _PerformanceAuthRequired({required this.onLogin});

  final VoidCallback onLogin;

  @override
  Widget build(BuildContext context) {
    return GtlStatePanel(
      icon: Icons.lock_outline,
      title: 'Desempenho protegido',
      body: 'Entre para acompanhar reputação, resoluções e conquistas.',
      action: FilledButton(onPressed: onLogin, child: const Text('Entrar')),
    );
  }
}

Map<String, dynamic> _map(Object? value) {
  if (value is Map<String, dynamic>) {
    return value;
  }
  if (value is Map) {
    return Map<String, dynamic>.from(value);
  }
  return <String, dynamic>{};
}

List<Map<String, dynamic>> _maps(Object? value) {
  if (value is! List) {
    return <Map<String, dynamic>>[];
  }
  return value
      .whereType<Map>()
      .map((item) => Map<String, dynamic>.from(item))
      .toList();
}

String _signed(int value) {
  if (value > 0) {
    return '+$value';
  }
  return value.toString();
}
