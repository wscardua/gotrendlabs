import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/providers.dart';
import '../../theme.dart';
import '../../ui/gtl_components.dart';
import '../markets/market_cards.dart';
import '../markets/markets_providers.dart';
import '../markets/markets_screen.dart';

class SearchScreen extends ConsumerStatefulWidget {
  const SearchScreen({super.key});

  @override
  ConsumerState<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends ConsumerState<SearchScreen> {
  String _query = '';

  @override
  Widget build(BuildContext context) {
    final markets = ref.watch(marketsProvider);
    final api = ref.watch(apiClientProvider);
    return GtlScreen(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const GtlEditorialHeader(
            kicker: 'Descoberta',
            title: 'Busca',
            body: 'Encontre mercados por pergunta, categoria ou evento.',
          ),
          const SizedBox(height: 14),
          TextField(
            onChanged: (value) => setState(() => _query = value),
            decoration: const InputDecoration(
              prefixIcon: Icon(Icons.search),
              labelText: 'Buscar mercados',
            ),
          ),
          const SizedBox(height: 16),
          Expanded(
            child: markets.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (error, stack) => GtlStatePanel(
                icon: Icons.cloud_off,
                title: 'Busca indisponível',
                body: error.toString(),
                color: GtlColors.accentYellow,
              ),
              data: (items) {
                final results = searchMarkets(items, _query);
                if (results.isEmpty) {
                  return const GtlStatePanel(
                    icon: Icons.travel_explore,
                    title: 'Nenhum mercado encontrado',
                    body: 'Experimente outra palavra, categoria ou evento.',
                    color: GtlColors.accentYellow,
                  );
                }
                return ListView.builder(
                  padding: const EdgeInsets.only(bottom: 24),
                  itemCount: results.length,
                  itemBuilder: (context, index) =>
                      MarketCompactCard(market: results[index], api: api),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
