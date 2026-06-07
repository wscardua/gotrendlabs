import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../theme.dart';
import '../alerts/alerts_screen.dart';
import '../auth/auth_controller.dart';
import '../auth/login_sheet.dart';
import '../markets/markets_screen.dart';
import '../profile/badges_screen.dart';
import '../profile/profile_screen.dart';
import '../ranking/ranking_screen.dart';
import '../search/search_screen.dart';
import '../support/contribution_sheets.dart';
import '../wallet/wallet_screen.dart';

class ShellScreen extends ConsumerStatefulWidget {
  const ShellScreen({super.key});

  @override
  ConsumerState<ShellScreen> createState() => _ShellScreenState();
}

class _ShellScreenState extends ConsumerState<ShellScreen> {
  int _index = 0;

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);
    final pages = [
      const TodayScreen(),
      const InsightsScreen(),
      const MarketsScreen(),
      const AlertsScreen(),
      const SearchScreen(),
    ];
    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('GoTrendLabs', style: Theme.of(context).textTheme.titleLarge),
            Text(
              'Preveja antes do consenso.',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ),
        actions: [
          IconButton(
            tooltip: auth.isAuthenticated ? 'Perfil' : 'Entrar no perfil',
            onPressed: () {
              if (auth.isAuthenticated) {
                Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => const ProfileScreen()),
                );
              } else {
                showLoginSheet(context);
              }
            },
            icon: Icon(
              auth.isAuthenticated
                  ? Icons.account_circle_outlined
                  : Icons.person_outline,
            ),
          ),
          PopupMenuButton<String>(
            icon: const Icon(Icons.more_horiz),
            onSelected: (value) {
              if (value == 'wallet') {
                Navigator.of(
                  context,
                ).push(MaterialPageRoute(builder: (_) => const WalletScreen()));
              }
              if (value == 'ranking') {
                Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => const RankingScreen()),
                );
              }
              if (value == 'badges') {
                Navigator.of(
                  context,
                ).push(MaterialPageRoute(builder: (_) => const BadgesScreen()));
              }
              if (value == 'suggestion') {
                showSuggestionSheet(context);
              }
              if (value == 'feedback') {
                showFeedbackSheet(context);
              }
              if (value == 'logout') {
                ref.read(authControllerProvider.notifier).logout();
              }
            },
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: 'suggestion',
                child: ListTile(
                  leading: Icon(Icons.add_chart),
                  title: Text('Sugerir mercado'),
                  contentPadding: EdgeInsets.zero,
                ),
              ),
              const PopupMenuItem(
                value: 'feedback',
                child: ListTile(
                  leading: Icon(Icons.support_agent),
                  title: Text('Suporte/feedback'),
                  contentPadding: EdgeInsets.zero,
                ),
              ),
              const PopupMenuItem(
                value: 'badges',
                child: ListTile(
                  leading: Icon(Icons.workspace_premium_outlined),
                  title: Text('Badges'),
                  contentPadding: EdgeInsets.zero,
                ),
              ),
              const PopupMenuItem(
                value: 'wallet',
                child: ListTile(
                  leading: Icon(Icons.account_balance_wallet_outlined),
                  title: Text('Wallet'),
                  contentPadding: EdgeInsets.zero,
                ),
              ),
              const PopupMenuItem(
                value: 'ranking',
                child: ListTile(
                  leading: Icon(Icons.leaderboard_outlined),
                  title: Text('Ranking'),
                  contentPadding: EdgeInsets.zero,
                ),
              ),
              if (auth.isAuthenticated)
                const PopupMenuItem(
                  value: 'logout',
                  child: ListTile(
                    leading: Icon(Icons.logout),
                    title: Text('Sair'),
                    contentPadding: EdgeInsets.zero,
                  ),
                ),
            ],
          ),
        ],
      ),
      body: IndexedStack(index: _index, children: pages),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (value) => setState(() => _index = value),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.auto_graph), label: 'Hoje'),
          NavigationDestination(icon: Icon(Icons.insights), label: 'Insights'),
          NavigationDestination(icon: Icon(Icons.grid_view), label: 'Mercados'),
          NavigationDestination(
            icon: Icon(Icons.notifications_none),
            label: 'Alertas',
          ),
          NavigationDestination(icon: Icon(Icons.search), label: 'Busca'),
        ],
      ),
    );
  }
}

class InsightsScreen extends ConsumerWidget {
  const InsightsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text('Insights', style: Theme.of(context).textTheme.headlineSmall),
        const SizedBox(height: 10),
        const Text(
          'Comentários de IA oficial e análises aparecem aqui quando expostos pelo backend. O app não chama provedor LLM diretamente.',
        ),
        const SizedBox(height: 16),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                const Icon(Icons.verified, color: GtlColors.accentViolet),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    'Fonte de verdade: FastAPI, agentes oficiais auditados e comentários com selo.',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
