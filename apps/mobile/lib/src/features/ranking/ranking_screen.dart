import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/formatters.dart';
import '../markets/markets_providers.dart';

class RankingScreen extends ConsumerWidget {
  const RankingScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final ranking = ref.watch(rankingProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Ranking')),
      body: ranking.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) => Center(child: Text(error.toString())),
        data: (rows) => ListView.builder(
          padding: const EdgeInsets.all(16),
          itemCount: rows.length,
          itemBuilder: (context, index) {
            final row = rows[index];
            return Card(
              child: ListTile(
                leading: CircleAvatar(
                  child: Text(safeInt(row['position']).toString()),
                ),
                title: Text(
                  row['display_name']?.toString() ??
                      row['handle']?.toString() ??
                      'Usuário',
                ),
                subtitle: Text(
                  '@${row['handle']} · ${row['strong_category'] ?? 'Geral'}',
                ),
                trailing: Text(safeInt(row['reputation_score']).toString()),
              ),
            );
          },
        ),
      ),
    );
  }
}
