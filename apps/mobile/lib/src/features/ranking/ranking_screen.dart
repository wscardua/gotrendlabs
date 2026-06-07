import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_client.dart';
import '../../core/formatters.dart';
import '../../theme.dart';
import '../../ui/gtl_components.dart';
import '../markets/markets_providers.dart';

class RankingScreen extends ConsumerStatefulWidget {
  const RankingScreen({super.key});

  @override
  ConsumerState<RankingScreen> createState() => _RankingScreenState();
}

class _RankingScreenState extends ConsumerState<RankingScreen> {
  String _category = '';
  String _subcategory = '';
  String _event = '';

  @override
  Widget build(BuildContext context) {
    final filters = RankingFilters(
      category: _category,
      subcategory: _subcategory,
      event: _event,
    );
    final ranking = ref.watch(rankingPayloadProvider(filters));
    return Scaffold(
      appBar: AppBar(title: const Text('Ranking')),
      body: GtlScreen(
        child: ranking.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (error, stack) => GtlStatePanel(
            icon: Icons.cloud_off,
            title: 'Ranking indisponível',
            body: ApiFailure.fromObject(error).message,
            color: GtlColors.accentYellow,
          ),
          data: (payload) {
            final rows = _listOfMaps(payload['rows']);
            final categories = _listOfMaps(payload['categories']);
            return ListView(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
              children: [
                const GtlEditorialHeader(
                  kicker: 'Reputação pública',
                  title: 'Ranking',
                  body: 'Quem se destaca nas previsões resolvidas?',
                  icon: Icons.leaderboard_outlined,
                ),
                const SizedBox(height: 12),
                _RankingFiltersCard(
                  categories: categories,
                  category: _category,
                  subcategory: _subcategory,
                  event: _event,
                  onCategory: (value) => setState(() {
                    _category = value;
                    _subcategory = '';
                    _event = '';
                  }),
                  onSubcategory: (value) => setState(() {
                    _subcategory = value;
                    _event = '';
                  }),
                  onEvent: (value) => setState(() => _event = value),
                  onClear: () => setState(() {
                    _category = '';
                    _subcategory = '';
                    _event = '';
                  }),
                ),
                const SizedBox(height: 12),
                if (rows.isEmpty)
                  const GtlSurface(
                    child: GtlEditorialHeader(
                      kicker: 'Recorte vazio',
                      title: 'Sem previsões resolvidas',
                      body:
                          'Ainda não há previsões resolvidas para este recorte.',
                      icon: Icons.hourglass_empty,
                    ),
                  )
                else
                  for (final row in rows) _RankingRowCard(row: row),
                const SizedBox(height: 12),
                const GtlSurface(
                  child: Text(
                    'O ranking considera previsões já resolvidas. Acertos em perguntas difíceis e previsões antecipadas pesam mais.',
                  ),
                ),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _RankingFiltersCard extends StatelessWidget {
  const _RankingFiltersCard({
    required this.categories,
    required this.category,
    required this.subcategory,
    required this.event,
    required this.onCategory,
    required this.onSubcategory,
    required this.onEvent,
    required this.onClear,
  });

  final List<Map<String, dynamic>> categories;
  final String category;
  final String subcategory;
  final String event;
  final ValueChanged<String> onCategory;
  final ValueChanged<String> onSubcategory;
  final ValueChanged<String> onEvent;
  final VoidCallback onClear;

  @override
  Widget build(BuildContext context) {
    final categoryItems = [
      const DropdownMenuItem(value: '', child: Text('Global')),
      for (final item in categories)
        DropdownMenuItem(
          value: item['slug']?.toString() ?? '',
          child: Text(item['name']?.toString() ?? ''),
        ),
    ];
    final selectedCategory = _selectedCategory();
    final subcategories = _listOfMaps(selectedCategory?['subcategories']);
    final subcategoryItems = [
      const DropdownMenuItem(value: '', child: Text('Todas')),
      for (final item in subcategories)
        DropdownMenuItem(
          value: item['slug']?.toString() ?? '',
          child: Text(item['name']?.toString() ?? ''),
        ),
    ];
    final selectedSubcategory = _selectedSubcategory(subcategories);
    final events = _listOfMaps(selectedSubcategory?['events']);
    final eventItems = [
      const DropdownMenuItem(value: '', child: Text('Todos')),
      for (final item in events)
        DropdownMenuItem(
          value: item['slug']?.toString() ?? '',
          child: Text(item['name']?.toString() ?? ''),
        ),
    ];

    return GtlSurface(
      color: GtlColors.surfaceGlass,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const GtlSectionTitle(title: 'Filtros', subtitle: 'Recorte público'),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            initialValue: _containsValue(categoryItems, category)
                ? category
                : '',
            decoration: const InputDecoration(labelText: 'Categoria'),
            items: categoryItems,
            onChanged: (value) => onCategory(value ?? ''),
          ),
          const SizedBox(height: 10),
          DropdownButtonFormField<String>(
            initialValue: _containsValue(subcategoryItems, subcategory)
                ? subcategory
                : '',
            decoration: const InputDecoration(labelText: 'Subcategoria'),
            items: subcategoryItems,
            onChanged: category.isEmpty
                ? null
                : (value) => onSubcategory(value ?? ''),
          ),
          const SizedBox(height: 10),
          DropdownButtonFormField<String>(
            initialValue: _containsValue(eventItems, event) ? event : '',
            decoration: const InputDecoration(labelText: 'Evento'),
            items: eventItems,
            onChanged: category.isEmpty || subcategory.isEmpty
                ? null
                : (value) => onEvent(value ?? ''),
          ),
          const SizedBox(height: 10),
          OutlinedButton.icon(
            onPressed: onClear,
            icon: const Icon(Icons.public),
            label: const Text('Global'),
          ),
        ],
      ),
    );
  }

  Map<String, dynamic>? _selectedCategory() {
    for (final item in categories) {
      if (item['slug'] == category) {
        return item;
      }
    }
    return null;
  }

  Map<String, dynamic>? _selectedSubcategory(
    List<Map<String, dynamic>> subcategories,
  ) {
    for (final item in subcategories) {
      if (item['slug'] == subcategory) {
        return item;
      }
    }
    return null;
  }

  bool _containsValue(List<DropdownMenuItem<String>> items, String value) {
    return items.any((item) => item.value == value);
  }
}

class _RankingRowCard extends StatelessWidget {
  const _RankingRowCard({required this.row});

  final Map<String, dynamic> row;

  @override
  Widget build(BuildContext context) {
    final handle = row['handle']?.toString() ?? '';
    final rawDisplayName = row['display_name']?.toString().trim() ?? '';
    final displayName = rawDisplayName.isNotEmpty ? rawDisplayName : handle;
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: GtlSurface(
        color: GtlColors.surfaceGlass,
        child: Row(
          children: [
            CircleAvatar(
              backgroundColor: GtlColors.accentBlue.withValues(alpha: 0.18),
              child: Text(safeInt(row['position']).toString()),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    displayName.isEmpty ? 'Usuário' : displayName,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 3),
                  Text(
                    '${_handleLabel(handle)} · ${row['strong_category'] ?? 'Geral'}',
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      _MiniMetric(
                        label: 'Reputação',
                        value: safeInt(row['reputation_score']).toString(),
                      ),
                      const SizedBox(width: 8),
                      _MiniMetric(
                        label: 'Acerto',
                        value: row['accuracy_indicator']?.toString() ?? '0%',
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

class _MiniMetric extends StatelessWidget {
  const _MiniMetric({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: GtlColors.surfaceInk,
        border: Border.all(color: GtlColors.border),
        borderRadius: BorderRadius.circular(GtlRadii.small),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5),
        child: Text('$label $value'),
      ),
    );
  }
}

List<Map<String, dynamic>> _listOfMaps(Object? value) {
  return ((value as List<dynamic>?) ?? <dynamic>[])
      .whereType<Map>()
      .map((item) => Map<String, dynamic>.from(item))
      .toList();
}

String _handleLabel(String value) {
  if (value.trim().isEmpty) {
    return '@usuario';
  }
  return value.startsWith('@') ? value : '@$value';
}
