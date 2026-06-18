import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter/services.dart';
import 'package:share_plus/share_plus.dart';

import '../../core/api_client.dart';
import '../../core/environment.dart';
import '../../core/formatters.dart';
import '../../core/providers.dart';
import '../../theme.dart';
import '../../ui/gtl_components.dart';
import '../auth/auth_controller.dart';
import '../auth/login_sheet.dart';
import '../info/about_screen.dart';
import '../info/trust_screen.dart';
import '../performance/performance_screen.dart';
import 'badges_screen.dart';
import '../ranking/ranking_screen.dart';
import '../support/contribution_sheets.dart';
import '../wallet/wallet_screen.dart';

final profileRepositoryProvider = Provider<ProfileRepository>(
  (ref) => ProfileRepository(ref.watch(apiClientProvider)),
);

class ProfileRepository {
  const ProfileRepository(this._api);

  final ApiClient _api;

  Future<Map<String, dynamic>> updatePrivateProfile({
    required String email,
    required String birthDate,
    required String bio,
  }) {
    return _api.patchMap(
      '/users/me',
      data: {'email': email, 'birth_date': birthDate, 'bio': bio},
    );
  }

  Future<Map<String, dynamic>> updateEmail({required String email}) {
    return _api.patchMap('/users/me', data: {'email': email});
  }
}

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authControllerProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Perfil')),
      body: GtlScreen(
        child: !auth.isAuthenticated
            ? _ProfileAuthRequired(onLogin: () => showLoginSheet(context))
            : ref
                  .watch(profileProvider)
                  .when(
                    loading: () =>
                        const Center(child: CircularProgressIndicator()),
                    error: (error, stack) => GtlStatePanel(
                      icon: Icons.cloud_off,
                      title: 'Perfil indisponível',
                      body: error.toString(),
                      color: GtlColors.accentYellow,
                    ),
                    data: (profile) {
                      final user = Map<String, dynamic>.from(
                        (profile['user'] as Map?) ?? const {},
                      );
                      final reputation = Map<String, dynamic>.from(
                        (profile['reputation'] as Map?) ?? const {},
                      );
                      return ListView(
                        padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
                        children: [
                          _ProfileHeader(
                            user: user,
                            profile: profile,
                            emailConfirmed: auth.user?.emailConfirmed == true,
                          ),
                          const SizedBox(height: 12),
                          _PrivateProfilePanel(
                            user: user,
                            profile: profile,
                            onEdit: () => showProfileEditSheet(
                              context,
                              initialProfile: profile,
                            ),
                          ),
                          const SizedBox(height: 12),
                          const _BiometricSettingsPanel(),
                          const SizedBox(height: 12),
                          _ReputationPanel(reputation: reputation),
                          const SizedBox(height: 12),
                          FilledButton.icon(
                            onPressed: () => Navigator.of(context).push(
                              MaterialPageRoute(
                                builder: (_) => const PerformanceScreen(),
                              ),
                            ),
                            icon: const Icon(Icons.query_stats),
                            label: const Text('Ver desempenho'),
                          ),
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
                          const SizedBox(height: 8),
                          OutlinedButton.icon(
                            onPressed: () => Navigator.of(context).push(
                              MaterialPageRoute(
                                builder: (_) => const TrustScreen(),
                              ),
                            ),
                            icon: const Icon(Icons.shield_outlined),
                            label: const Text(
                              'Política, conceitos e segurança',
                            ),
                          ),
                          const SizedBox(height: 8),
                          OutlinedButton.icon(
                            onPressed: () => Navigator.of(context).push(
                              MaterialPageRoute(
                                builder: (_) => const AboutScreen(),
                              ),
                            ),
                            icon: const Icon(Icons.info_outline),
                            label: const Text('Sobre'),
                          ),
                        ],
                      );
                    },
                  ),
      ),
    );
  }
}

Future<void> showProfileEditSheet(
  BuildContext context, {
  required Map<String, dynamic> initialProfile,
}) {
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    backgroundColor: GtlColors.surfaceElevated,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(GtlRadii.large)),
    ),
    builder: (_) => _ProfileEditSheet(initialProfile: initialProfile),
  );
}

class _BiometricSettingsPanel extends ConsumerWidget {
  const _BiometricSettingsPanel();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authControllerProvider);
    final supported = ref
        .watch(biometricCapabilityProvider)
        .maybeWhen(data: (value) => value, orElse: () => false);
    final enabled = ref
        .watch(biometricPreferenceProvider)
        .maybeWhen(data: (value) => value, orElse: () => false);
    final hasRememberedSession = ref
        .watch(rememberedSessionProvider)
        .maybeWhen(data: (value) => value, orElse: () => false);
    final canToggle = supported && hasRememberedSession && !auth.busy;
    final subtitle = !supported
        ? 'Este aparelho não informou biometria ou senha local compatível.'
        : !hasRememberedSession
        ? 'Entre com Lembrar login para proteger a próxima abertura.'
        : 'Na próxima abertura, use biometria ou senha do aparelho.';

    return GtlSurface(
      color: GtlColors.surfaceGlass,
      padding: EdgeInsets.zero,
      child: Material(
        type: MaterialType.transparency,
        child: SwitchListTile(
          value: enabled && supported,
          contentPadding: const EdgeInsets.symmetric(
            horizontal: 16,
            vertical: 8,
          ),
          secondary: const Icon(Icons.fingerprint),
          onChanged: canToggle
              ? (value) async {
                  await ref
                      .read(authControllerProvider.notifier)
                      .setBiometricProtection(value);
                  final error = ref.read(authControllerProvider).error;
                  if (context.mounted && error != null) {
                    ScaffoldMessenger.of(
                      context,
                    ).showSnackBar(SnackBar(content: Text(error)));
                  }
                }
              : null,
          title: const Text('Proteção local'),
          subtitle: Text(subtitle),
        ),
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
    final category = profile['strong_category']?.toString() ?? '';
    return GtlSurface(
      glowColor: GtlColors.accentBlue,
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
        ],
      ),
    );
  }
}

class _PrivateProfilePanel extends StatelessWidget {
  const _PrivateProfilePanel({
    required this.user,
    required this.profile,
    required this.onEdit,
  });

  final Map<String, dynamic> user;
  final Map<String, dynamic> profile;
  final VoidCallback onEdit;

  @override
  Widget build(BuildContext context) {
    final email = user['email']?.toString() ?? '';
    final birthDate = profile['birth_date']?.toString() ?? '';
    final bio = profile['bio']?.toString() ?? '';

    return GtlSurface(
      color: GtlColors.surfaceGlass,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          GtlSectionTitle(
            title: 'Dados pessoais',
            subtitle: 'Informações privadas para conferência e edição',
            trailing: TextButton.icon(
              onPressed: onEdit,
              icon: const Icon(Icons.edit_outlined, size: 18),
              label: const Text('Editar'),
            ),
          ),
          const SizedBox(height: 12),
          _PrivateDataRow(
            icon: Icons.alternate_email,
            label: 'Email',
            value: email.isEmpty ? 'Não informado' : email,
          ),
          const SizedBox(height: 10),
          _PrivateDataRow(
            icon: Icons.cake_outlined,
            label: 'Nascimento',
            value: _formatBirthDate(birthDate),
          ),
          const SizedBox(height: 10),
          _PrivateDataRow(
            icon: Icons.notes_outlined,
            label: 'Bio',
            value: bio.trim().isEmpty ? 'Ainda sem bio' : bio.trim(),
            maxLines: 4,
          ),
        ],
      ),
    );
  }
}

class _PrivateDataRow extends StatelessWidget {
  const _PrivateDataRow({
    required this.icon,
    required this.label,
    required this.value,
    this.maxLines = 2,
  });

  final IconData icon;
  final String label;
  final String value;
  final int maxLines;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: GtlColors.surfaceInk,
        borderRadius: BorderRadius.circular(GtlRadii.medium),
        border: Border.all(color: GtlColors.border),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, size: 20, color: GtlColors.accentCyan),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    label.toUpperCase(),
                    style: Theme.of(context).textTheme.labelMedium,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    value,
                    maxLines: maxLines,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: GtlColors.textPrimary,
                    ),
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

class _ProfileEditSheet extends ConsumerStatefulWidget {
  const _ProfileEditSheet({required this.initialProfile});

  final Map<String, dynamic> initialProfile;

  @override
  ConsumerState<_ProfileEditSheet> createState() => _ProfileEditSheetState();
}

class _ProfileEditSheetState extends ConsumerState<_ProfileEditSheet> {
  late final TextEditingController _email;
  late final TextEditingController _birthDate;
  late final TextEditingController _bio;
  bool _busy = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    final user = Map<String, dynamic>.from(
      (widget.initialProfile['user'] as Map?) ?? const {},
    );
    _email = TextEditingController(text: user['email']?.toString() ?? '');
    _birthDate = TextEditingController(
      text: _editableBirthDate(widget.initialProfile['birth_date']),
    );
    _bio = TextEditingController(
      text: widget.initialProfile['bio']?.toString() ?? '',
    );
  }

  @override
  void dispose() {
    _email.dispose();
    _birthDate.dispose();
    _bio.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final emailConfirmed =
        ref.watch(authControllerProvider).user?.emailConfirmed == true;
    return SafeArea(
      child: Padding(
        padding: EdgeInsets.only(
          left: 16,
          right: 16,
          top: 16,
          bottom: MediaQuery.viewInsetsOf(context).bottom + 16,
        ),
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            mainAxisSize: MainAxisSize.min,
            children: [
              GtlEditorialHeader(
                kicker: 'Perfil privado',
                title: 'Editar dados',
                body: emailConfirmed
                    ? 'Atualize seus dados pessoais. Alterar email exige nova confirmação.'
                    : 'Corrija seu email para receber o link de confirmação.',
                icon: Icons.manage_accounts_outlined,
                trailing: IconButton(
                  onPressed: _busy ? null : () => Navigator.of(context).pop(),
                  icon: const Icon(Icons.close),
                ),
              ),
              const SizedBox(height: 14),
              TextField(
                controller: _email,
                enabled: !_busy,
                keyboardType: TextInputType.emailAddress,
                textInputAction: TextInputAction.next,
                decoration: const InputDecoration(labelText: 'Email'),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: _birthDate,
                enabled: !_busy && emailConfirmed,
                keyboardType: TextInputType.number,
                textInputAction: TextInputAction.next,
                inputFormatters: const [_BirthDateInputFormatter()],
                decoration: InputDecoration(
                  labelText: 'Data de nascimento',
                  hintText: 'DD/MM/AAAA',
                  helperText: 'Digite só números ou use o calendário.',
                  suffixIcon: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      if (_birthDate.text.isNotEmpty)
                        IconButton(
                          tooltip: 'Limpar data',
                          onPressed: _busy || !emailConfirmed
                              ? null
                              : () => setState(() => _birthDate.clear()),
                          icon: const Icon(Icons.close),
                        ),
                      IconButton(
                        tooltip: 'Escolher data',
                        onPressed: _busy || !emailConfirmed
                            ? null
                            : _pickBirthDate,
                        icon: const Icon(Icons.calendar_month_outlined),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: _bio,
                enabled: !_busy && emailConfirmed,
                minLines: 4,
                maxLines: 6,
                maxLength: 1000,
                decoration: const InputDecoration(labelText: 'Bio'),
              ),
              if (!emailConfirmed) ...[
                const SizedBox(height: 10),
                const Text(
                  'Depois de confirmar o email, você poderá alterar nascimento e bio.',
                ),
              ],
              if (_error?.trim().isNotEmpty == true) ...[
                const SizedBox(height: 10),
                GtlSurface(
                  color: GtlColors.surfaceInk,
                  borderColor: GtlColors.accentRed.withValues(alpha: 0.42),
                  padding: const EdgeInsets.all(12),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(
                        Icons.error_outline,
                        color: GtlColors.accentRed,
                      ),
                      const SizedBox(width: 10),
                      Expanded(child: Text(_error!)),
                    ],
                  ),
                ),
              ],
              const SizedBox(height: 14),
              FilledButton.icon(
                onPressed: _busy ? null : _save,
                icon: _busy
                    ? const SizedBox.square(
                        dimension: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.check),
                label: const Text('Salvar dados'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _pickBirthDate() async {
    final initial = _parseBirthDateInput(_birthDate.text) ?? DateTime(1995);
    final selected = await showDatePicker(
      context: context,
      initialDate: initial,
      firstDate: DateTime(1900),
      lastDate: DateTime.now(),
    );
    if (selected == null) {
      return;
    }
    setState(() => _birthDate.text = _toDisplayDate(selected));
  }

  Future<void> _save() async {
    final email = _email.text.trim();
    if (email.isEmpty || !email.contains('@')) {
      setState(() => _error = 'Informe um email válido.');
      return;
    }
    final emailConfirmed =
        ref.read(authControllerProvider).user?.emailConfirmed == true;
    final birthDate = _normalizeBirthDateInput(_birthDate.text);
    if (emailConfirmed &&
        _birthDate.text.trim().isNotEmpty &&
        birthDate == null) {
      setState(() => _error = 'Use uma data válida no formato DD/MM/AAAA.');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final repository = ref.read(profileRepositoryProvider);
      final updated = emailConfirmed
          ? await repository.updatePrivateProfile(
              email: email,
              birthDate: birthDate ?? '',
              bio: _bio.text.trim(),
            )
          : await repository.updateEmail(email: email);
      ref.read(authControllerProvider.notifier).syncProfileUser(updated);
      ref.invalidate(profileProvider);
      if (mounted) {
        Navigator.of(context).pop();
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              emailConfirmed
                  ? 'Dados do perfil atualizados.'
                  : 'Enviamos a confirmação para o email informado.',
            ),
          ),
        );
      }
    } catch (error) {
      setState(() => _error = ApiFailure.fromObject(error).message);
    } finally {
      if (mounted) {
        setState(() => _busy = false);
      }
    }
  }
}

String _handleLabel(String value) {
  final handle = value.trim();
  if (handle.isEmpty) {
    return '';
  }
  return handle.startsWith('@') ? handle : '@$handle';
}

String _editableBirthDate(Object? value) {
  final date = _parseIsoDate(value?.toString() ?? '');
  return date == null ? '' : _toDisplayDate(date);
}

String _formatBirthDate(String value) {
  final date = _parseIsoDate(value);
  if (date == null) {
    return 'Não informada';
  }
  final day = date.day.toString().padLeft(2, '0');
  final month = date.month.toString().padLeft(2, '0');
  return '$day/$month/${date.year}';
}

DateTime? _parseBirthDateInput(String value) {
  final normalized = value.trim();
  if (normalized.isEmpty) {
    return null;
  }
  final displayMatch = RegExp(
    r'^(\d{1,2})/(\d{1,2})/(\d{4})$',
  ).firstMatch(normalized);
  if (displayMatch != null) {
    final day = int.tryParse(displayMatch.group(1)!);
    final month = int.tryParse(displayMatch.group(2)!);
    final year = int.tryParse(displayMatch.group(3)!);
    if (day == null || month == null || year == null) {
      return null;
    }
    final date = DateTime(year, month, day);
    if (date.year != year || date.month != month || date.day != day) {
      return null;
    }
    return date;
  }
  return _parseIsoDate(normalized);
}

String? _normalizeBirthDateInput(String value) {
  final normalized = value.trim();
  if (normalized.isEmpty) {
    return '';
  }
  final date = _parseBirthDateInput(normalized);
  if (date == null) {
    return null;
  }
  return _toIsoDate(date);
}

DateTime? _parseIsoDate(String value) {
  final normalized = value.trim();
  if (normalized.isEmpty) {
    return null;
  }
  return DateTime.tryParse(normalized);
}

String _toDisplayDate(DateTime date) {
  final month = date.month.toString().padLeft(2, '0');
  final day = date.day.toString().padLeft(2, '0');
  return '$day/$month/${date.year}';
}

String _toIsoDate(DateTime date) {
  final month = date.month.toString().padLeft(2, '0');
  final day = date.day.toString().padLeft(2, '0');
  return '${date.year}-$month-$day';
}

class _BirthDateInputFormatter extends TextInputFormatter {
  const _BirthDateInputFormatter();

  @override
  TextEditingValue formatEditUpdate(
    TextEditingValue oldValue,
    TextEditingValue newValue,
  ) {
    final digits = newValue.text.replaceAll(RegExp(r'\D'), '');
    final limited = digits.length > 8 ? digits.substring(0, 8) : digits;
    final buffer = StringBuffer();
    for (var index = 0; index < limited.length; index += 1) {
      if (index == 2 || index == 4) {
        buffer.write('/');
      }
      buffer.write(limited[index]);
    }
    final formatted = buffer.toString();
    return TextEditingValue(
      text: formatted,
      selection: TextSelection.collapsed(offset: formatted.length),
    );
  }
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
    return GtlSurface(
      color: GtlColors.surfaceGlass,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const GtlSectionTitle(
            title: 'Reputação',
            subtitle: 'Sinais públicos calculados pelo backend',
          ),
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
                      color: GtlColors.surfaceInk,
                      border: Border.all(color: GtlColors.border),
                      borderRadius: BorderRadius.circular(GtlRadii.medium),
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
    return GtlSurface(
      color: GtlColors.surfaceGlass,
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
                                style: Theme.of(context).textTheme.titleMedium,
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
    return GtlSurface(
      padding: EdgeInsets.zero,
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
        color: GtlColors.surfaceInk,
        border: Border.all(color: GtlColors.border),
        borderRadius: BorderRadius.circular(GtlRadii.pill),
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
    return GtlStatePanel(
      icon: Icons.lock_outline,
      title: 'Perfil protegido',
      body: 'Entre para ver perfil, reputação e badges.',
      action: FilledButton(onPressed: onLogin, child: const Text('Entrar')),
    );
  }
}
