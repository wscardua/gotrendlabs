import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:package_info_plus/package_info_plus.dart';

import '../../core/api_client.dart';
import '../../core/providers.dart';
import '../../theme.dart';
import '../../ui/gtl_components.dart';
import '../auth/auth_controller.dart';
import '../auth/auth_models.dart';
import '../push/push_controller.dart';
import '../push/push_models.dart';
import 'trust_screen.dart';

final aboutAppInfoProvider = FutureProvider<AboutAppInfo>((ref) async {
  try {
    final package = await PackageInfo.fromPlatform();
    return AboutAppInfo(
      appName: package.appName.isEmpty ? 'GoTrendLabs' : package.appName,
      packageName: package.packageName,
      version: package.version,
      buildNumber: package.buildNumber,
      platform: _platformLabel(),
    );
  } catch (_) {
    return AboutAppInfo(
      appName: 'GoTrendLabs',
      packageName: 'br.com.gotrendlabs.gotrendlabs_mobile',
      version: '1.0.0',
      buildNumber: '1',
      platform: _platformLabel(),
    );
  }
});

final aboutApiHealthProvider = FutureProvider<Map<String, dynamic>>((ref) {
  return ref.read(apiClientProvider).getMap('/health');
});

final aboutPushStatusProvider = FutureProvider<PushTokenSnapshot>((ref) {
  final auth = ref.watch(authControllerProvider);
  if (!auth.isAuthenticated) {
    return const PushTokenSnapshot.unavailable('authentication_required');
  }
  return ref.read(pushTokenProvider).currentToken();
});

class AboutAppInfo {
  const AboutAppInfo({
    required this.appName,
    required this.packageName,
    required this.version,
    required this.buildNumber,
    required this.platform,
  });

  final String appName;
  final String packageName;
  final String version;
  final String buildNumber;
  final String platform;

  String get versionLabel => '$version+$buildNumber';
}

class AboutScreen extends ConsumerWidget {
  const AboutScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final appInfo = ref.watch(aboutAppInfoProvider);
    final health = ref.watch(aboutApiHealthProvider);
    final pushStatus = ref.watch(aboutPushStatusProvider);
    final auth = ref.watch(authControllerProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Sobre')),
      body: GtlScreen(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
          children: [
            GtlSurface(
              glowColor: GtlColors.accentBlue,
              child: Row(
                children: [
                  const GtlBrandMark(size: 58),
                  const SizedBox(width: 14),
                  Expanded(
                    child: GtlEditorialHeader(
                      kicker: 'GoTrendLabs',
                      title: 'Sobre',
                      body: 'Preveja antes do consenso.',
                      trailing: appInfo.when(
                        data: (info) => GtlPill(
                          label: 'v${info.versionLabel}',
                          color: GtlColors.accentGreen,
                          filled: true,
                        ),
                        loading: () => const SizedBox.shrink(),
                        error: (_, _) => const SizedBox.shrink(),
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),
            _AppSection(appInfo: appInfo),
            const SizedBox(height: 12),
            _ApiSection(health: health),
            const SizedBox(height: 12),
            _PushHealthSection(pushStatus: pushStatus),
            const SizedBox(height: 12),
            _AccountSection(user: auth.user),
            const SizedBox(height: 12),
            _LinksSection(
              onTrust: () => Navigator.of(
                context,
              ).push(MaterialPageRoute(builder: (_) => const TrustScreen())),
            ),
            const SizedBox(height: 12),
            _DiagnosticsSection(
              appInfo: appInfo,
              health: health,
              pushStatus: pushStatus,
              user: auth.user,
            ),
          ],
        ),
      ),
    );
  }
}

class _AppSection extends StatelessWidget {
  const _AppSection({required this.appInfo});

  final AsyncValue<AboutAppInfo> appInfo;

  @override
  Widget build(BuildContext context) {
    return _InfoSurface(
      title: 'Aplicativo',
      icon: Icons.app_settings_alt_outlined,
      children: appInfo.when(
        data: (info) => [
          _InfoRow(label: 'Versão', value: info.version),
          _InfoRow(label: 'Build', value: info.buildNumber),
          _InfoRow(label: 'Pacote', value: info.packageName),
          _InfoRow(label: 'Plataforma', value: info.platform),
        ],
        loading: () => const [_LoadingRow()],
        error: (error, stack) => [
          _InfoRow(label: 'Versão', value: 'Indisponível'),
          _InfoRow(label: 'Erro', value: ApiFailure.fromObject(error).message),
        ],
      ),
    );
  }
}

class _ApiSection extends StatelessWidget {
  const _ApiSection({required this.health});

  final AsyncValue<Map<String, dynamic>> health;

  @override
  Widget build(BuildContext context) {
    final healthLabel = health.maybeWhen(
      data: (payload) => payload['status']?.toString() == 'ok'
          ? 'Operando normalmente'
          : 'Instável',
      error: (error, stack) => ApiFailure.fromObject(error).message,
      orElse: () => 'Consultando...',
    );
    final online = health.hasValue;
    return _InfoSurface(
      title: 'Saúde da API',
      icon: online ? Icons.check_circle_outline : Icons.sync_problem,
      trailing: GtlPill(
        label: online ? 'ativa' : 'verificando',
        color: online ? GtlColors.accentGreen : GtlColors.accentYellow,
        filled: true,
      ),
      children: [_InfoRow(label: 'Condição', value: healthLabel)],
    );
  }
}

class _PushHealthSection extends StatelessWidget {
  const _PushHealthSection({required this.pushStatus});

  final AsyncValue<PushTokenSnapshot> pushStatus;

  @override
  Widget build(BuildContext context) {
    final snapshot = pushStatus.maybeWhen(
      data: (value) => value,
      orElse: () => null,
    );
    final isAvailable = snapshot?.isAvailable == true;
    final isLoading = pushStatus.isLoading && !pushStatus.hasValue;
    final reason = snapshot?.reason ?? 'unknown';
    final label = isLoading
        ? 'Verificando'
        : isAvailable
        ? 'Token local'
        : _pushUnavailableLabel(reason);
    final detail = isLoading
        ? 'Consultando o estado local de push.'
        : isAvailable
        ? 'Token local disponível para QA em ${snapshot!.platform}.'
        : _pushUnavailableMessage(reason);
    return _InfoSurface(
      title: 'Push mobile',
      icon: Icons.notifications_none_outlined,
      trailing: GtlPill(
        label: label.toLowerCase(),
        color: isAvailable ? GtlColors.accentGreen : GtlColors.accentYellow,
        filled: true,
      ),
      children: [
        _InfoRow(label: 'Estado', value: label),
        _InfoRow(label: 'Detalhe', value: detail),
      ],
    );
  }
}

class _AccountSection extends StatelessWidget {
  const _AccountSection({required this.user});

  final GtlUser? user;

  @override
  Widget build(BuildContext context) {
    final currentUser = user;
    return _InfoSurface(
      title: 'Conta',
      icon: Icons.account_circle_outlined,
      children: currentUser == null
          ? const [
              _InfoRow(label: 'Sessão', value: 'Visitante'),
              _InfoRow(label: 'Diagnóstico', value: 'Sem dados privados'),
            ]
          : [
              _InfoRow(label: 'Usuário', value: currentUser.displayName),
              _InfoRow(
                label: 'Identificador',
                value: _handleLabel(currentUser.handle),
              ),
              _InfoRow(
                label: 'Email confirmado',
                value: currentUser.emailConfirmed ? 'Sim' : 'Não',
              ),
            ],
    );
  }
}

class _LinksSection extends StatelessWidget {
  const _LinksSection({required this.onTrust});

  final VoidCallback onTrust;

  @override
  Widget build(BuildContext context) {
    return _InfoSurface(
      title: 'Confiança',
      icon: Icons.shield_outlined,
      children: [
        Text(
          'Política de uso, conceitos do produto e segurança ficam reunidos na área de confiança.',
          style: Theme.of(context).textTheme.bodyMedium,
        ),
        const SizedBox(height: 12),
        OutlinedButton.icon(
          onPressed: onTrust,
          icon: const Icon(Icons.shield_outlined),
          label: const Text('Abrir confiança'),
        ),
      ],
    );
  }
}

class _DiagnosticsSection extends ConsumerWidget {
  const _DiagnosticsSection({
    required this.appInfo,
    required this.health,
    required this.pushStatus,
    required this.user,
  });

  final AsyncValue<AboutAppInfo> appInfo;
  final AsyncValue<Map<String, dynamic>> health;
  final AsyncValue<PushTokenSnapshot> pushStatus;
  final GtlUser? user;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return _InfoSurface(
      title: 'Diagnóstico',
      icon: Icons.content_paste_search_outlined,
      children: [
        Text(
          'Copia dados seguros para suporte. Token, senha e segredos nunca entram neste resumo.',
          style: Theme.of(context).textTheme.bodyMedium,
        ),
        const SizedBox(height: 12),
        FilledButton.icon(
          onPressed: () => _copyDiagnostics(context),
          icon: const Icon(Icons.copy),
          label: const Text('Copiar diagnóstico'),
        ),
      ],
    );
  }

  Future<void> _copyDiagnostics(BuildContext context) async {
    final info = appInfo.maybeWhen(data: (value) => value, orElse: () => null);
    final healthPayload = health.maybeWhen(
      data: (value) => value,
      orElse: () => null,
    );
    final pushSnapshot = pushStatus.maybeWhen(
      data: (value) => value,
      orElse: () => null,
    );
    final lines = [
      'GoTrendLabs mobile diagnostics',
      'app_version=${info?.version ?? 'unknown'}',
      'app_build=${info?.buildNumber ?? 'unknown'}',
      'package=${info?.packageName ?? 'unknown'}',
      'platform=${info?.platform ?? _platformLabel()}',
      'api_status=${healthPayload?['status']?.toString() ?? 'unavailable'}',
      'push_status=${_pushDiagnosticsLabel(pushSnapshot)}',
      'user_handle=${user == null ? 'guest' : _handleLabel(user!.handle)}',
      'email_confirmed=${user?.emailConfirmed.toString() ?? 'false'}',
    ];
    await Clipboard.setData(ClipboardData(text: lines.join('\n')));
    if (context.mounted) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Diagnóstico copiado.')));
    }
  }
}

class _InfoSurface extends StatelessWidget {
  const _InfoSurface({
    required this.title,
    required this.icon,
    required this.children,
    this.trailing,
  });

  final String title;
  final IconData icon;
  final List<Widget> children;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    return GtlSurface(
      color: GtlColors.surfaceGlass,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: GtlColors.accentBlue),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  title,
                  style: Theme.of(context).textTheme.titleLarge,
                ),
              ),
              ?trailing,
            ],
          ),
          const SizedBox(height: 12),
          ...children,
        ],
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 114,
            child: Text(
              label.toUpperCase(),
              style: Theme.of(context).textTheme.labelSmall,
            ),
          ),
          Expanded(
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: SelectableText(
                value,
                maxLines: 1,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: GtlColors.textPrimary,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _LoadingRow extends StatelessWidget {
  const _LoadingRow();

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.only(bottom: 10),
      child: GtlSkeletonBlock(height: 22),
    );
  }
}

String _platformLabel() {
  return switch (defaultTargetPlatform) {
    TargetPlatform.android => 'Android',
    TargetPlatform.iOS => 'iOS',
    TargetPlatform.macOS => 'macOS',
    TargetPlatform.windows => 'Windows',
    TargetPlatform.linux => 'Linux',
    TargetPlatform.fuchsia => 'Fuchsia',
  };
}

String _handleLabel(String value) {
  final handle = value.trim();
  if (handle.isEmpty) {
    return 'sem handle';
  }
  return handle.startsWith('@') ? handle : '@$handle';
}

String _pushUnavailableMessage(String reason) {
  return switch (reason) {
    'firebase_not_configured' =>
      'Firebase/FCM ainda não foi ativado neste build.',
    'fake_token_invalid' => 'Token local de QA inválido.',
    'authentication_required' =>
      'Entre na sua conta para ativar notificações neste dispositivo.',
    'unknown' => 'Estado local de push indisponível.',
    _ => reason,
  };
}

String _pushUnavailableLabel(String reason) {
  return switch (reason) {
    'authentication_required' => 'Login necessário',
    'permission_denied' => 'Permissão negada',
    _ => 'Não configurado',
  };
}

String _pushDiagnosticsLabel(PushTokenSnapshot? snapshot) {
  if (snapshot == null) {
    return 'unknown';
  }
  if (snapshot.isAvailable) {
    return 'available:${snapshot.platform}';
  }
  return snapshot.reason.isEmpty ? 'unavailable' : snapshot.reason;
}
