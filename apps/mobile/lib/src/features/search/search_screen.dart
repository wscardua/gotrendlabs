import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/providers.dart';
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
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
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
              error: (error, stack) => Center(child: Text(error.toString())),
              data: (items) {
                final results = searchMarkets(items, _query);
                if (results.isEmpty) {
                  return const Center(
                    child: Text(
                      'Nenhum mercado encontrado. Experimente outra categoria.',
                    ),
                  );
                }
                return ListView.builder(
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
