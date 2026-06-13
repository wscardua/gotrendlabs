import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/providers.dart';
import '../../theme.dart';
import '../../ui/gtl_components.dart';
import '../alerts/alerts_screen.dart';
import '../auth/auth_controller.dart';
import '../auth/login_sheet.dart';
import '../info/about_screen.dart';
import '../info/trust_screen.dart';
import '../markets/markets_screen.dart';
import '../profile/badges_screen.dart';
import '../profile/profile_screen.dart';
import '../ranking/ranking_screen.dart';
import '../search/search_screen.dart';
import '../support/contribution_sheets.dart';
import '../wallet/wallet_screen.dart';

class ShellScreen extends ConsumerStatefulWidget {
  const ShellScreen({super.key, this.initialIndex = 0});

  final int initialIndex;

  @override
  ConsumerState<ShellScreen> createState() => _ShellScreenState();
}

class _ShellScreenState extends ConsumerState<ShellScreen>
    with WidgetsBindingObserver {
  static const _notificationsRefreshInterval = Duration(seconds: 30);

  late int _index;
  MarketDeskFilter _marketDeskFilter = MarketDeskFilter.all;
  Timer? _notificationsRefreshTimer;

  @override
  void initState() {
    super.initState();
    _index = widget.initialIndex.clamp(0, 4);
    WidgetsBinding.instance.addObserver(this);
    _notificationsRefreshTimer = Timer.periodic(
      _notificationsRefreshInterval,
      (_) => _refreshNotifications(),
    );
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _notificationsRefreshTimer?.cancel();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _refreshNotifications();
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);
    final notifications = ref.watch(notificationsProvider);
    final unreadNotifications = notifications.maybeWhen(
      data: _unreadNotificationCount,
      orElse: () => 0,
    );
    final pages = [
      TodayScreen(onOpenDesk: _openMarketDesk),
      const RankingScreen(),
      MarketsScreen(initialDeskFilter: _marketDeskFilter),
      const AlertsScreen(),
      const SearchScreen(),
    ];
    return Scaffold(
      appBar: AppBar(
        toolbarHeight: 72,
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const GtlBrandMark(size: 44),
            const SizedBox(width: 10),
            Flexible(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'GoTrendLabs',
                    style: Theme.of(context).textTheme.titleLarge,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  Text(
                    'Preveja antes do consenso.',
                    style: Theme.of(context).textTheme.bodySmall,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
          ],
        ),
        actions: [
          _RoundIconButton(
            tooltip: auth.sessionLocked
                ? 'Desbloquear sessão'
                : auth.isAuthenticated
                ? 'Perfil'
                : 'Entrar no perfil',
            icon: auth.sessionLocked
                ? Icons.lock_outline
                : auth.isAuthenticated
                ? Icons.account_circle_outlined
                : Icons.person_outline,
            onPressed: () {
              if (auth.isAuthenticated) {
                Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => const ProfileScreen()),
                );
              } else {
                showLoginSheet(context);
              }
            },
          ),
          PopupMenuButton<String>(
            icon: const Icon(Icons.more_horiz),
            color: GtlColors.surfaceElevated,
            surfaceTintColor: Colors.transparent,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(GtlRadii.medium),
              side: const BorderSide(color: GtlColors.border),
            ),
            onSelected: (value) {
              if (value == 'wallet') {
                Navigator.of(
                  context,
                ).push(MaterialPageRoute(builder: (_) => const WalletScreen()));
              }
              if (value == 'insights') {
                Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => const InsightsScreen()),
                );
              }
              if (value == 'badges') {
                Navigator.of(
                  context,
                ).push(MaterialPageRoute(builder: (_) => const BadgesScreen()));
              }
              if (value == 'feedback') {
                showFeedbackSheet(context);
              }
              if (value == 'trust') {
                Navigator.of(
                  context,
                ).push(MaterialPageRoute(builder: (_) => const TrustScreen()));
              }
              if (value == 'about') {
                Navigator.of(
                  context,
                ).push(MaterialPageRoute(builder: (_) => const AboutScreen()));
              }
              if (value == 'logout') {
                ref.read(authControllerProvider.notifier).logout();
              }
            },
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: 'wallet',
                child: ListTile(
                  leading: Icon(Icons.account_balance_wallet_outlined),
                  title: Text('Wallet'),
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
                value: 'insights',
                child: ListTile(
                  leading: Icon(Icons.insights_outlined),
                  title: Text('Insights'),
                  contentPadding: EdgeInsets.zero,
                ),
              ),
              const PopupMenuItem(
                value: 'feedback',
                child: ListTile(
                  leading: Icon(Icons.support_agent),
                  title: Text('Suporte'),
                  contentPadding: EdgeInsets.zero,
                ),
              ),
              const PopupMenuItem(
                value: 'trust',
                child: ListTile(
                  leading: Icon(Icons.shield_outlined),
                  title: Text('Política e segurança'),
                  contentPadding: EdgeInsets.zero,
                ),
              ),
              const PopupMenuItem(
                value: 'about',
                child: ListTile(
                  leading: Icon(Icons.info_outline),
                  title: Text('Sobre'),
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
        onDestinationSelected: (value) {
          setState(() => _index = value);
          if (value == 3) {
            _markNotificationsRead();
          }
        },
        destinations: [
          const NavigationDestination(
            icon: Icon(Icons.auto_graph),
            label: 'Hoje',
          ),
          const NavigationDestination(
            icon: Icon(Icons.leaderboard_outlined),
            label: 'Ranking',
          ),
          const NavigationDestination(
            icon: Icon(Icons.grid_view),
            label: 'Mercados',
          ),
          NavigationDestination(
            icon: _AlertNavIcon(unreadCount: unreadNotifications),
            selectedIcon: _AlertNavIcon(
              unreadCount: unreadNotifications,
              selected: true,
            ),
            label: 'Alertas',
          ),
          const NavigationDestination(icon: Icon(Icons.search), label: 'Busca'),
        ],
      ),
    );
  }

  void _refreshNotifications() {
    final auth = ref.read(authControllerProvider);
    if (!auth.isAuthenticated) {
      return;
    }
    if (_index == 3) {
      _markNotificationsRead();
    } else {
      ref.invalidate(notificationsProvider);
    }
  }

  void _openMarketDesk(MarketDeskFilter filter) {
    setState(() {
      _marketDeskFilter = filter;
      _index = 2;
    });
  }

  Future<void> _markNotificationsRead() async {
    final auth = ref.read(authControllerProvider);
    if (!auth.isAuthenticated) {
      return;
    }
    try {
      await ref
          .read(apiClientProvider)
          .postMap('/users/me/notifications/read-all');
    } catch (_) {
      // A lista ainda pode ser exibida; o badge tenta sincronizar no proximo refresh.
    } finally {
      ref.invalidate(notificationsProvider);
    }
  }
}

class _AlertNavIcon extends StatelessWidget {
  const _AlertNavIcon({required this.unreadCount, this.selected = false});

  final int unreadCount;
  final bool selected;

  @override
  Widget build(BuildContext context) {
    final icon = Icon(
      unreadCount > 0 || selected
          ? Icons.notifications_active
          : Icons.notifications_none,
    );
    if (unreadCount <= 0) {
      return icon;
    }
    return Badge.count(
      count: unreadCount,
      backgroundColor: GtlColors.accentRed,
      textColor: GtlColors.textPrimary,
      child: icon,
    );
  }
}

int _unreadNotificationCount(List<dynamic> notifications) {
  var unread = 0;
  var unknownReadState = 0;
  for (final notification in notifications) {
    if (notification is! Map) {
      continue;
    }
    final isRead = notification['is_read'];
    if (isRead is bool) {
      if (!isRead) {
        unread += 1;
      }
      continue;
    }
    unknownReadState += 1;
  }
  return unread > 0 ? unread : unknownReadState;
}

class _RoundIconButton extends StatelessWidget {
  const _RoundIconButton({
    required this.tooltip,
    required this.icon,
    required this.onPressed,
  });

  final String tooltip;
  final IconData icon;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(right: 4),
      child: IconButton(
        tooltip: tooltip,
        onPressed: onPressed,
        icon: Icon(icon),
        style: IconButton.styleFrom(
          backgroundColor: GtlColors.surfaceElevated,
          foregroundColor: GtlColors.textPrimary,
          side: const BorderSide(color: GtlColors.border),
        ),
      ),
    );
  }
}

class InsightsScreen extends ConsumerWidget {
  const InsightsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      appBar: AppBar(title: const Text('Insights')),
      body: GtlScreen(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
          children: [
            const GtlEditorialHeader(
              kicker: 'Leitura assistida',
              title: 'Insights',
              body:
                  'Comentários de IA oficial e análises aparecem aqui quando expostos pelo backend.',
            ),
            const SizedBox(height: 16),
            GtlSurface(
              glowColor: GtlColors.accentViolet,
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
            const SizedBox(height: 12),
            const GtlSurface(
              child: GtlEditorialHeader(
                kicker: 'MVP',
                title: 'Sem provedor local',
                body:
                    'O app não chama LLM diretamente; quando houver insight, ele será servido pelo backend.',
                icon: Icons.lock_outline,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
