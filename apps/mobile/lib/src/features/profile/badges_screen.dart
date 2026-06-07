import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:share_plus/share_plus.dart';

import '../../core/api_client.dart';
import '../../core/environment.dart';
import '../../core/providers.dart';
import '../../theme.dart';
import '../auth/auth_controller.dart';

class BadgesScreen extends ConsumerWidget {
  const BadgesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final badges = ref.watch(badgeCatalogProvider);
    final api = ref.watch(apiClientProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Badges')),
      body: badges.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) =>
            Center(child: Text(ApiFailure.fromObject(error).message)),
        data: (items) {
          if (items.isEmpty) {
            return const Center(child: Text('Nenhuma badge cadastrada ainda.'));
          }
          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: items.length,
            itemBuilder: (context, index) {
              final badge = Map<String, dynamic>.from(items[index] as Map);
              return _BadgeCard(badge: badge, api: api);
            },
          );
        },
      ),
    );
  }
}

class _BadgeCard extends StatelessWidget {
  const _BadgeCard({required this.badge, required this.api});

  final Map<String, dynamic> badge;
  final ApiClient api;

  @override
  Widget build(BuildContext context) {
    final earned = badge['status']?.toString() == 'earned';
    final name = badge['name']?.toString() ?? 'Badge';
    final description = badge['description']?.toString() ?? '';
    final rule = badge['rule_description']?.toString() ?? '';
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            BadgeArt(badge: badge, api: api, size: 72),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          name,
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                      ),
                      _BadgeStatus(earned: earned),
                    ],
                  ),
                  if (description.isNotEmpty) ...[
                    const SizedBox(height: 6),
                    Text(description),
                  ],
                  if (rule.isNotEmpty) ...[
                    const SizedBox(height: 6),
                    Text(rule, style: Theme.of(context).textTheme.bodySmall),
                  ],
                  if (earned) ...[
                    const SizedBox(height: 10),
                    Align(
                      alignment: Alignment.centerLeft,
                      child: TextButton.icon(
                        onPressed: () => SharePlus.instance.share(
                          ShareParams(
                            title: name,
                            subject: 'GoTrendLabs',
                            text:
                                'Conquistei a badge $name na GoTrendLabs.\n\n${AppEnvironment.publicWebBaseUrl}/share/badge/${badge['code']}/',
                          ),
                        ),
                        icon: const Icon(Icons.ios_share, size: 18),
                        label: const Text('Compartilhar'),
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class BadgeArt extends StatelessWidget {
  const BadgeArt({
    super.key,
    required this.badge,
    required this.api,
    this.size = 42,
  });

  final Map<String, dynamic> badge;
  final ApiClient api;
  final double size;

  @override
  Widget build(BuildContext context) {
    final status = badge['status']?.toString();
    final imageUrl = api.resolveUrl(
      (badge['image_dark_url']?.toString().isNotEmpty ?? false)
          ? badge['image_dark_url'].toString()
          : badge['image_url']?.toString() ?? '',
    );
    final earned = status == 'earned';
    if (imageUrl.isNotEmpty) {
      return ClipRRect(
        borderRadius: BorderRadius.circular(8),
        child: CachedNetworkImage(
          imageUrl: imageUrl,
          width: size,
          height: size,
          fit: BoxFit.cover,
          errorWidget: (context, url, error) =>
              _BadgeFallback(size: size, earned: earned),
        ),
      );
    }
    return _BadgeFallback(size: size, earned: earned);
  }
}

class _BadgeFallback extends StatelessWidget {
  const _BadgeFallback({required this.size, required this.earned});

  final double size;
  final bool earned;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: earned
            ? GtlColors.accentGreen.withValues(alpha: 0.16)
            : GtlColors.surfaceElevated,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: GtlColors.border),
      ),
      child: SizedBox.square(
        dimension: size,
        child: Icon(
          earned ? Icons.workspace_premium : Icons.lock_outline,
          color: earned ? GtlColors.accentGreen : GtlColors.muted,
        ),
      ),
    );
  }
}

class _BadgeStatus extends StatelessWidget {
  const _BadgeStatus({required this.earned});

  final bool earned;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: (earned ? GtlColors.accentGreen : GtlColors.surfaceElevated)
            .withValues(alpha: 0.18),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(
          color: earned
              ? GtlColors.accentGreen.withValues(alpha: 0.6)
              : GtlColors.border,
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
        child: Text(earned ? 'Conquistada' : 'Bloqueada'),
      ),
    );
  }
}
