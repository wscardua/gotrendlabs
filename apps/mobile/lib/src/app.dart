import 'dart:async';

import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'features/markets/market_detail_screen.dart';
import 'features/maintenance/maintenance_gate.dart';
import 'features/profile/badges_screen.dart';
import 'features/shell/shell_screen.dart';
import 'features/wallet/wallet_screen.dart';
import 'theme.dart';

class GoTrendLabsApp extends ConsumerStatefulWidget {
  const GoTrendLabsApp({super.key});

  @override
  ConsumerState<GoTrendLabsApp> createState() => _GoTrendLabsAppState();
}

class _GoTrendLabsAppState extends ConsumerState<GoTrendLabsApp> {
  late final GoRouter _router;
  StreamSubscription<RemoteMessage>? _openedSubscription;

  @override
  void initState() {
    super.initState();
    _router = GoRouter(
      routes: [
        GoRoute(
          path: '/',
          builder: (context, state) => const ShellScreen(),
          routes: [
            GoRoute(
              path: 'markets/:slug',
              builder: (context, state) => MarketDetailScreen(
                slug: state.pathParameters['slug'] ?? '',
                initialTab: state.uri.queryParameters['tab'] == 'community'
                    ? MarketDetailTab.community
                    : MarketDetailTab.overview,
              ),
            ),
            GoRoute(
              path: 'wallet',
              builder: (context, state) => const WalletScreen(),
            ),
            GoRoute(
              path: 'badges',
              builder: (context, state) => const BadgesScreen(),
            ),
            GoRoute(
              path: 'alerts',
              builder: (context, state) => const ShellScreen(initialIndex: 3),
            ),
          ],
        ),
      ],
    );
    _listenForPushRoutes();
  }

  @override
  void dispose() {
    _openedSubscription?.cancel();
    _router.dispose();
    super.dispose();
  }

  Future<void> _listenForPushRoutes() async {
    if (Firebase.apps.isEmpty) {
      return;
    }
    _openedSubscription = FirebaseMessaging.onMessageOpenedApp.listen(
      _openPushRoute,
    );
    final initialMessage = await FirebaseMessaging.instance.getInitialMessage();
    if (initialMessage != null) {
      _openPushRoute(initialMessage);
    }
  }

  void _openPushRoute(RemoteMessage message) {
    final route = _safePushRoute(message.data['route']?.toString() ?? '');
    if (route == null) {
      return;
    }
    _router.go(route);
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'GoTrendLabs',
      debugShowCheckedModeBanner: false,
      theme: buildGoTrendLabsTheme(),
      routerConfig: _router,
      builder: (context, child) =>
          MaintenanceGate(child: child ?? const SizedBox.shrink()),
    );
  }
}

String? _safePushRoute(String rawRoute) {
  final route = rawRoute.trim();
  if (route == '/wallet' || route == '/badges' || route == '/alerts') {
    return route;
  }
  if (route.startsWith('/markets/')) {
    final uri = Uri.tryParse(route);
    if (uri == null || uri.pathSegments.length != 2) {
      return null;
    }
    final slug = uri.pathSegments[1];
    if (RegExp(r'^[a-z0-9][a-z0-9-]{0,119}$').hasMatch(slug)) {
      if (uri.queryParameters.isEmpty ||
          (uri.queryParameters.length == 1 &&
              uri.queryParameters['tab'] == 'community')) {
        return uri.toString();
      }
    }
  }
  return null;
}
