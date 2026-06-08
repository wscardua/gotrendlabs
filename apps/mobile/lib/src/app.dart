import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'features/markets/market_detail_screen.dart';
import 'features/profile/badges_screen.dart';
import 'features/shell/shell_screen.dart';
import 'features/wallet/wallet_screen.dart';
import 'theme.dart';

class GoTrendLabsApp extends ConsumerWidget {
  const GoTrendLabsApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = GoRouter(
      routes: [
        GoRoute(
          path: '/',
          builder: (context, state) => const ShellScreen(),
          routes: [
            GoRoute(
              path: 'markets/:slug',
              builder: (context, state) =>
                  MarketDetailScreen(slug: state.pathParameters['slug'] ?? ''),
            ),
            GoRoute(
              path: 'wallet',
              builder: (context, state) => const WalletScreen(),
            ),
            GoRoute(
              path: 'badges',
              builder: (context, state) => const BadgesScreen(),
            ),
          ],
        ),
      ],
    );

    return MaterialApp.router(
      title: 'GoTrendLabs',
      debugShowCheckedModeBanner: false,
      theme: buildGoTrendLabsTheme(),
      routerConfig: router,
    );
  }
}
