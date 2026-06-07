import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:share_plus/share_plus.dart';

import '../../core/api_client.dart';
import '../../core/environment.dart';
import '../../core/formatters.dart';
import '../../theme.dart';
import '../auth/auth_controller.dart';
import '../auth/login_sheet.dart';
import 'badges_screen.dart';
import '../ranking/ranking_screen.dart';
import '../support/contribution_sheets.dart';
import '../wallet/wallet_screen.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authControllerProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Perfil')),
      body: !auth.isAuthenticated
          ? _ProfileAuthRequired(onLogin: () => showLoginSheet(context))
          : ref
                .watch(profileProvider)
                .when(
                  loading: () =>
                      const Center(child: CircularProgressIndicator()),
                  error: (error, stack) =>
                      Center(child: Text(error.toString())),
                  data: (profile) {
                    final user = Map<String, dynamic>.from(
                      (profile['user'] as Map?) ?? const {},
                    );
                    final reputation = Map<String, dynamic>.from(
                      (profile['reputation'] as Map?) ?? const {},
                    );
                    return ListView(
                      padding: const EdgeInsets.all(16),
                      children: [
                        _ProfileHeader(
                          user: user,
                          profile: profile,
                          emailConfirmed: auth.user?.emailConfirmed == true,
                        ),
                        const SizedBox(height: 12),
                        _ReputationPanel(reputation: reputation),
                        const SizedBox(height: 12),
                        ref
                            .watch(badgesProvider)
                            .when(
                              loading: () => const _InfoCard(
                                icon: Icons.workspace_premium_outlined,
                                title: 'Badges conquistadas',
                                body: 'Carregando...',
                              ),
                              error: (error, stack) => _InfoCard(
                                icon: Icons.workspace_premium_outlined,
                                title: 'Badges conquistadas',
                                body: error.toString(),
                              ),
                              data: (badges) => _BadgesPanel(badges: badges),
                            ),
                        const SizedBox(height: 12),
                        OutlinedButton.icon(
                          onPressed: () => Navigator.of(context).push(
                            MaterialPageRoute(
                              builder: (_) => const BadgesScreen(),
                            ),
                          ),
                          icon: const Icon(Icons.workspace_premium_outlined),
                          label: const Text('Ver badges'),
                        ),
                        const SizedBox(height: 8),
                        OutlinedButton.icon(
                          onPressed: () => showInviteSheet(context),
                          icon: const Icon(Icons.person_add_alt_1),
                          label: const Text('Convidar'),
                        ),
                        const SizedBox(height: 8),
                        FilledButton.icon(
                          onPressed: () => Navigator.of(context).push(
                            MaterialPageRoute(
                              builder: (_) => const WalletScreen(),
                            ),
                          ),
                          icon: const Icon(
                            Icons.account_balance_wallet_outlined,
                          ),
                          label: const Text('Ver wallet'),
                        ),
                        const SizedBox(height: 8),
                        OutlinedButton.icon(
                          onPressed: () => Navigator.of(context).push(
                            MaterialPageRoute(
                              builder: (_) => const RankingScreen(),
                            ),
                          ),
                          icon: const Icon(Icons.leaderboard_outlined),
                          label: const Text('Ver ranking'),
                        ),
                        const SizedBox(height: 8),
                        OutlinedButton.icon(
                          onPressed: () => showSuggestionSheet(context),
                          icon: const Icon(Icons.add_chart),
                          label: const Text('Sugerir mercado'),
                        ),
                        const SizedBox(height: 8),
                        OutlinedButton.icon(
                          onPressed: () => showFeedbackSheet(context),
                          icon: const Icon(Icons.support_agent),
                          label: const Text('Suporte/feedback'),
                        ),
                      ],
                    );
                  },
                ),
    );
  }
}

class _ProfileHeader extends StatelessWidget {
  const _ProfileHeader({
    required this.user,
    required this.profile,
    required this.emailConfirmed,
  });

  final Map<String, dynamic> user;
  final Map<String, dynamic> profile;
  final bool emailConfirmed;

  @override
  Widget build(BuildContext context) {
    final displayName = user['display_name']?.toString() ?? 'Usuário';
    final handle = _handleLabel(user['handle']?.toString() ?? '');
    final bio = profile['bio']?.toString() ?? '';
    final category = profile['strong_category']?.toString() ?? '';
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CircleAvatar(
                  backgroundColor: GtlColors.accentBlue.withValues(alpha: 0.18),
                  child: const Icon(Icons.person_outline),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        displayName,
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      Text(handle.isEmpty ? 'handle em formação' : handle),
                    ],
                  ),
                ),
                Icon(
                  emailConfirmed ? Icons.verified : Icons.mark_email_unread,
                  color: emailConfirmed
                      ? GtlColors.accentGreen
                      : GtlColors.accentYellow,
                ),
              ],
            ),
            if (category.isNotEmpty) ...[
              const SizedBox(height: 12),
              _Pill(label: category, icon: Icons.category_outlined),
            ],
            if (bio.isNotEmpty) ...[const SizedBox(height: 12), Text(bio)],
          ],
        ),
      ),
    );
  }
}

String _handleLabel(String value) {
  final handle = value.trim();
  if (handle.isEmpty) {
    return '';
  }
  return handle.startsWith('@') ? handle : '@$handle';
}

class _ReputationPanel extends StatelessWidget {
  const _ReputationPanel({required this.reputation});

  final Map<String, dynamic> reputation;

  @override
  Widget build(BuildContext context) {
    final metrics = [
      ('Reputação', safeInt(reputation['reputation_score']).toString()),
      ('Ranking', '#${safeInt(reputation['ranking_position'])}'),
      (
        'Resolvidas',
        safeInt(reputation['resolved_predictions_count']).toString(),
      ),
      ('Precisão', reputation['accuracy_indicator']?.toString() ?? '0%'),
      ('Sequência', safeInt(reputation['streak']).toString()),
      (
        'Força',
        reputation['strong_category']?.toString().isNotEmpty == true
            ? reputation['strong_category'].toString()
            : 'Geral',
      ),
    ];
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Reputação', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 12),
            Wrap(
              spacing: 10,
              runSpacing: 10,
              children: [
                for (final metric in metrics)
                  SizedBox(
                    width: 142,
                    child: DecoratedBox(
                      decoration: BoxDecoration(
                        color: GtlColors.surfaceElevated,
                        border: Border.all(color: GtlColors.border),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Padding(
                        padding: const EdgeInsets.all(10),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              metric.$1.toUpperCase(),
                              style: Theme.of(context).textTheme.labelMedium,
                            ),
                            const SizedBox(height: 6),
                            FittedBox(
                              fit: BoxFit.scaleDown,
                              alignment: Alignment.centerLeft,
                              child: Text(
                                metric.$2,
                                style: Theme.of(context).textTheme.titleLarge,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _BadgesPanel extends StatelessWidget {
  const _BadgesPanel({required this.badges});

  final List<dynamic> badges;

  @override
  Widget build(BuildContext context) {
    final api = ApiClient();
    final earned = badges
        .whereType<Map>()
        .map((item) => Map<String, dynamic>.from(item))
        .where(
          (badge) =>
              badge['status']?.toString() == 'earned' ||
              (badge['earned_at']?.toString().isNotEmpty ?? false),
        )
        .toList();
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.workspace_premium_outlined),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Badges conquistadas',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
                Text(earned.length.toString()),
              ],
            ),
            const SizedBox(height: 12),
            if (earned.isEmpty)
              const Text('Nenhuma badge conquistada ainda.')
            else
              Column(
                children: [
                  for (final badge in earned.take(3))
                    Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: Row(
                        children: [
                          BadgeArt(badge: badge, api: api, size: 44),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  badge['name']?.toString() ?? 'Badge',
                                  style: Theme.of(
                                    context,
                                  ).textTheme.titleMedium,
                                ),
                                Text(
                                  badge['description']?.toString() ?? '',
                                  maxLines: 2,
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                ],
              ),
          ],
        ),
      ),
    );
  }
}

Future<void> showInviteSheet(BuildContext context) {
  return showModalBottomSheet<void>(
    context: context,
    builder: (_) => const _InviteSheet(),
  );
}

class _InviteSheet extends ConsumerWidget {
  const _InviteSheet();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final referral = ref.watch(referralProvider);
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: referral.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (error, stack) => Text(ApiFailure.fromObject(error).message),
          data: (data) {
            final enabled = data['enabled'] == true;
            final code = data['code']?.toString() ?? '';
            final bonus = safeInt(data['bonus_gtl']);
            final reason = data['reason']?.toString() ?? '';
            final url =
                '${AppEnvironment.publicWebBaseUrl}/register/?ref=$code';
            return Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        'Convidar',
                        style: Theme.of(context).textTheme.headlineSmall,
                      ),
                    ),
                    IconButton(
                      onPressed: () => Navigator.of(context).pop(),
                      icon: const Icon(Icons.close),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  enabled
                      ? 'Compartilhe seu link e receba $bonus GT₵ quando a pessoa criar conta.'
                      : reason,
                ),
                if (enabled) ...[
                  const SizedBox(height: 12),
                  SelectableText(url),
                  const SizedBox(height: 12),
                  FilledButton.icon(
                    onPressed: () => SharePlus.instance.share(
                      ShareParams(
                        title: 'GoTrendLabs',
                        subject: 'Convite GoTrendLabs',
                        text: 'Entre na GoTrendLabs pelo meu convite: $url',
                      ),
                    ),
                    icon: const Icon(Icons.ios_share),
                    label: const Text('Compartilhar convite'),
                  ),
                ],
              ],
            );
          },
        ),
      ),
    );
  }
}

class _InfoCard extends StatelessWidget {
  const _InfoCard({
    required this.icon,
    required this.title,
    required this.body,
  });

  final IconData icon;
  final String title;
  final String body;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        leading: Icon(icon),
        title: Text(title),
        subtitle: Text(body),
      ),
    );
  }
}

class _Pill extends StatelessWidget {
  const _Pill({required this.label, required this.icon});

  final String label;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: GtlColors.surfaceElevated,
        border: Border.all(color: GtlColors.border),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 16),
            const SizedBox(width: 6),
            Text(label, style: Theme.of(context).textTheme.labelMedium),
          ],
        ),
      ),
    );
  }
}

class _ProfileAuthRequired extends StatelessWidget {
  const _ProfileAuthRequired({required this.onLogin});

  final VoidCallback onLogin;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.lock_outline),
            const SizedBox(height: 12),
            const Text('Entre para ver perfil, reputação e badges.'),
            const SizedBox(height: 12),
            FilledButton(onPressed: onLogin, child: const Text('Entrar')),
          ],
        ),
      ),
    );
  }
}
