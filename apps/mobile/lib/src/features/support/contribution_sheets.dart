import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_client.dart';
import '../../theme.dart';
import '../../ui/gtl_components.dart';
import '../anti_abuse/anti_abuse_challenge_field.dart';
import '../anti_abuse/anti_abuse_repository.dart';
import '../auth/auth_controller.dart';
import 'support_providers.dart';

const _feedbackTypes = [
  'Bug de produto',
  'Mercado ambíguo',
  'Risco de segurança',
  'Ideia de melhoria',
  'Dúvidas',
];

Future<void> showFeedbackSheet(BuildContext context) {
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    backgroundColor: GtlColors.surfaceElevated,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(GtlRadii.large)),
    ),
    builder: (_) => const _FeedbackSheet(),
  );
}

Future<void> showSuggestionSheet(BuildContext context) {
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    backgroundColor: GtlColors.surfaceElevated,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(GtlRadii.large)),
    ),
    builder: (_) => const _SuggestionSheet(),
  );
}

class _FeedbackSheet extends ConsumerStatefulWidget {
  const _FeedbackSheet();

  @override
  ConsumerState<_FeedbackSheet> createState() => _FeedbackSheetState();
}

class _FeedbackSheetState extends ConsumerState<_FeedbackSheet> {
  final _guestName = TextEditingController();
  final _guestEmail = TextEditingController();
  final _antiAbuseAnswer = TextEditingController();
  final _description = TextEditingController();
  String? _feedbackType;
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _guestName.dispose();
    _guestEmail.dispose();
    _antiAbuseAnswer.dispose();
    _description.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);
    return _ContributionScaffold(
      title: 'Suporte e feedback',
      busy: _busy,
      error: _error,
      submitLabel: 'Enviar feedback',
      onSubmit: _send,
      children: [
        if (!auth.isAuthenticated) ...[
          TextField(
            controller: _guestName,
            decoration: const InputDecoration(labelText: 'Nome'),
          ),
          const SizedBox(height: 10),
          TextField(
            controller: _guestEmail,
            keyboardType: TextInputType.emailAddress,
            decoration: const InputDecoration(labelText: 'Email'),
          ),
          const SizedBox(height: 10),
          AntiAbuseChallengeField(
            controller: _antiAbuseAnswer,
            enabled: !_busy,
          ),
          const SizedBox(height: 10),
        ],
        DropdownButtonFormField<String>(
          initialValue: _feedbackType,
          decoration: const InputDecoration(labelText: 'Tipo'),
          items: [
            for (final type in _feedbackTypes)
              DropdownMenuItem(value: type, child: Text(type)),
          ],
          onChanged: (value) => setState(() => _feedbackType = value),
        ),
        const SizedBox(height: 10),
        TextField(
          controller: _description,
          minLines: 4,
          maxLines: 6,
          decoration: const InputDecoration(labelText: 'Descrição'),
        ),
      ],
    );
  }

  Future<void> _send() async {
    final type = _feedbackType ?? '';
    final auth = ref.read(authControllerProvider);
    if (_description.text.trim().isEmpty || type.isEmpty) {
      setState(() => _error = 'Preencha tipo e descrição.');
      return;
    }
    if (!auth.isAuthenticated && !_hasGuestIdentity()) {
      setState(
        () => _error = 'Informe nome e email para enviar como visitante.',
      );
      return;
    }
    final challenge = auth.isAuthenticated
        ? null
        : ref
              .read(antiAbuseChallengeProvider)
              .maybeWhen(data: (value) => value, orElse: () => null);
    if (!auth.isAuthenticated && challenge == null) {
      setState(() => _error = 'Aguarde o desafio anti-abuso carregar.');
      return;
    }
    if (!auth.isAuthenticated && _antiAbuseAnswer.text.trim().isEmpty) {
      setState(() => _error = 'Responda ao desafio anti-abuso.');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref
          .read(supportRepositoryProvider)
          .sendFeedback(
            feedbackType: type,
            description: _description.text.trim(),
            guestName: _guestName.text.trim(),
            guestEmail: _guestEmail.text.trim(),
            antiAbuseToken: challenge?.token ?? '',
            antiAbuseAnswer: _antiAbuseAnswer.text.trim(),
          );
      if (mounted) {
        Navigator.of(context).pop();
        _showMessage('Feedback enviado para revisão.');
      }
    } catch (error) {
      setState(() => _error = ApiFailure.fromObject(error).message);
    } finally {
      if (mounted) {
        setState(() => _busy = false);
      }
    }
  }

  void _showMessage(String message) {
    if (!mounted) {
      return;
    }
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(message)));
  }

  bool _hasGuestIdentity() {
    return _guestName.text.trim().isNotEmpty &&
        _isValidEmail(_guestEmail.text.trim());
  }
}

class _SuggestionSheet extends ConsumerStatefulWidget {
  const _SuggestionSheet();

  @override
  ConsumerState<_SuggestionSheet> createState() => _SuggestionSheetState();
}

class _SuggestionSheetState extends ConsumerState<_SuggestionSheet> {
  final _guestName = TextEditingController();
  final _guestEmail = TextEditingController();
  final _antiAbuseAnswer = TextEditingController();
  final _question = TextEditingController();
  final _source = TextEditingController();
  final _rationale = TextEditingController();
  String? _category;
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _guestName.dispose();
    _guestEmail.dispose();
    _antiAbuseAnswer.dispose();
    _question.dispose();
    _source.dispose();
    _rationale.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);
    final taxonomy = ref.watch(taxonomyProvider);
    return _ContributionScaffold(
      title: 'Sugerir mercado',
      busy: _busy,
      error: _error,
      submitLabel: 'Enviar sugestão',
      onSubmit: _send,
      children: [
        if (!auth.isAuthenticated) ...[
          TextField(
            controller: _guestName,
            decoration: const InputDecoration(labelText: 'Nome'),
          ),
          const SizedBox(height: 10),
          TextField(
            controller: _guestEmail,
            keyboardType: TextInputType.emailAddress,
            decoration: const InputDecoration(labelText: 'Email'),
          ),
          const SizedBox(height: 10),
          AntiAbuseChallengeField(
            controller: _antiAbuseAnswer,
            enabled: !_busy,
          ),
          const SizedBox(height: 10),
        ],
        TextField(
          controller: _question,
          maxLength: 240,
          decoration: const InputDecoration(labelText: 'Pergunta do mercado'),
        ),
        const SizedBox(height: 10),
        taxonomy.when(
          loading: () => const _SelectPlaceholder(
            label: 'Categoria',
            text: 'Carregando categorias...',
            loading: true,
          ),
          error: (error, stack) => _SelectPlaceholder(
            label: 'Categoria',
            text: ApiFailure.fromObject(error).message,
          ),
          data: (categories) {
            final options = categories
                .map((item) => item['name']?.toString() ?? '')
                .where((name) => name.isNotEmpty)
                .toList();
            final selected = options.contains(_category) ? _category : null;
            return DropdownButtonFormField<String>(
              initialValue: selected,
              decoration: const InputDecoration(labelText: 'Categoria'),
              hint: Text(
                options.isEmpty
                    ? 'Nenhuma categoria ativa cadastrada'
                    : 'Selecione',
              ),
              items: [
                for (final category in options)
                  DropdownMenuItem(value: category, child: Text(category)),
              ],
              onChanged: options.isEmpty
                  ? null
                  : (value) => setState(() => _category = value),
            );
          },
        ),
        const SizedBox(height: 10),
        TextField(
          controller: _source,
          decoration: const InputDecoration(labelText: 'Fonte sugerida'),
        ),
        const SizedBox(height: 10),
        TextField(
          controller: _rationale,
          minLines: 3,
          maxLines: 5,
          decoration: const InputDecoration(labelText: 'Contexto'),
        ),
      ],
    );
  }

  Future<void> _send() async {
    final category = _category ?? '';
    final auth = ref.read(authControllerProvider);
    if (_question.text.trim().isEmpty ||
        category.isEmpty ||
        _source.text.trim().isEmpty) {
      setState(() => _error = 'Preencha pergunta, categoria e fonte.');
      return;
    }
    if (!auth.isAuthenticated && !_hasGuestIdentity()) {
      setState(
        () => _error = 'Informe nome e email para enviar como visitante.',
      );
      return;
    }
    final challenge = auth.isAuthenticated
        ? null
        : ref
              .read(antiAbuseChallengeProvider)
              .maybeWhen(data: (value) => value, orElse: () => null);
    if (!auth.isAuthenticated && challenge == null) {
      setState(() => _error = 'Aguarde o desafio anti-abuso carregar.');
      return;
    }
    if (!auth.isAuthenticated && _antiAbuseAnswer.text.trim().isEmpty) {
      setState(() => _error = 'Responda ao desafio anti-abuso.');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref
          .read(supportRepositoryProvider)
          .suggestMarket(
            question: _question.text.trim(),
            category: category,
            subcategory: '',
            suggestedSource: _source.text.trim(),
            rationale: _rationale.text.trim(),
            guestName: _guestName.text.trim(),
            guestEmail: _guestEmail.text.trim(),
            antiAbuseToken: challenge?.token ?? '',
            antiAbuseAnswer: _antiAbuseAnswer.text.trim(),
          );
      if (mounted) {
        Navigator.of(context).pop();
        _showMessage('Sugestão enviada para revisão.');
      }
    } catch (error) {
      setState(() => _error = ApiFailure.fromObject(error).message);
    } finally {
      if (mounted) {
        setState(() => _busy = false);
      }
    }
  }

  void _showMessage(String message) {
    if (!mounted) {
      return;
    }
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(message)));
  }

  bool _hasGuestIdentity() {
    return _guestName.text.trim().isNotEmpty &&
        _isValidEmail(_guestEmail.text.trim());
  }
}

class _SelectPlaceholder extends StatelessWidget {
  const _SelectPlaceholder({
    required this.label,
    required this.text,
    this.loading = false,
  });

  final String label;
  final String text;
  final bool loading;

  @override
  Widget build(BuildContext context) {
    return InputDecorator(
      decoration: InputDecoration(labelText: label),
      child: Row(
        children: [
          if (loading)
            const SizedBox.square(
              dimension: 14,
              child: CircularProgressIndicator(strokeWidth: 2),
            )
          else
            const Icon(Icons.error_outline, size: 18),
          const SizedBox(width: 10),
          Expanded(child: Text(text)),
        ],
      ),
    );
  }
}

class _ContributionScaffold extends StatelessWidget {
  const _ContributionScaffold({
    required this.title,
    required this.children,
    required this.busy,
    required this.submitLabel,
    required this.onSubmit,
    this.error,
  });

  final String title;
  final List<Widget> children;
  final bool busy;
  final String submitLabel;
  final VoidCallback onSubmit;
  final String? error;

  @override
  Widget build(BuildContext context) {
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
                kicker: 'Contribuição',
                title: title,
                body: 'Envie para a fila FastAPI/Admin Ops, sem lógica local.',
                trailing: IconButton(
                  onPressed: () => Navigator.of(context).pop(),
                  icon: const Icon(Icons.close),
                ),
                icon: Icons.outgoing_mail,
              ),
              const SizedBox(height: 10),
              ...children,
              if (error?.trim().isNotEmpty == true) ...[
                const SizedBox(height: 12),
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
                      Expanded(
                        child: Text(
                          error!,
                          style: Theme.of(context).textTheme.bodyMedium
                              ?.copyWith(color: GtlColors.textPrimary),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
              const SizedBox(height: 14),
              FilledButton.icon(
                onPressed: busy ? null : onSubmit,
                icon: busy
                    ? const SizedBox.square(
                        dimension: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.send),
                label: Text(submitLabel),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

bool _isValidEmail(String email) {
  return RegExp(r'^[^\s@]+@[^\s@]+\.[^\s@]+$').hasMatch(email);
}
