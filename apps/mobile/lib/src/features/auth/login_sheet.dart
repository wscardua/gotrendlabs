import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../theme.dart';
import 'auth_controller.dart';

Future<void> showLoginSheet(BuildContext context) {
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    backgroundColor: GtlColors.surfaceElevated,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
    ),
    builder: (context) => const LoginSheet(),
  );
}

class LoginSheet extends ConsumerStatefulWidget {
  const LoginSheet({super.key});

  @override
  ConsumerState<LoginSheet> createState() => _LoginSheetState();
}

class _LoginSheetState extends ConsumerState<LoginSheet> {
  final _name = TextEditingController();
  final _email = TextEditingController();
  final _password = TextEditingController();
  bool _register = false;
  bool _acceptedTerms = false;

  @override
  void dispose() {
    _name.dispose();
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);
    ref.listen(authControllerProvider, (previous, next) {
      if (next.isAuthenticated && ModalRoute.of(context)?.isCurrent == true) {
        Navigator.of(context).pop();
      }
    });

    return Padding(
      padding: EdgeInsets.only(
        left: 20,
        right: 20,
        top: 18,
        bottom: MediaQuery.viewInsetsOf(context).bottom + 20,
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    _register ? 'Criar conta' : 'Entrar',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                ),
                IconButton(
                  onPressed: () => Navigator.of(context).pop(),
                  icon: const Icon(Icons.close),
                  tooltip: 'Fechar',
                ),
              ],
            ),
            const SizedBox(height: 12),
            SegmentedButton<bool>(
              segments: const [
                ButtonSegment(value: false, label: Text('Login')),
                ButtonSegment(value: true, label: Text('Cadastro')),
              ],
              selected: {_register},
              onSelectionChanged: (value) =>
                  setState(() => _register = value.first),
            ),
            const SizedBox(height: 16),
            if (_register) ...[
              TextField(
                controller: _name,
                textInputAction: TextInputAction.next,
                decoration: const InputDecoration(labelText: 'Nome público'),
              ),
              const SizedBox(height: 12),
            ],
            TextField(
              controller: _email,
              keyboardType: TextInputType.emailAddress,
              textInputAction: TextInputAction.next,
              decoration: const InputDecoration(labelText: 'Email'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _password,
              obscureText: true,
              decoration: const InputDecoration(labelText: 'Senha'),
            ),
            if (_register) ...[
              const SizedBox(height: 8),
              CheckboxListTile(
                value: _acceptedTerms,
                contentPadding: EdgeInsets.zero,
                onChanged: (value) =>
                    setState(() => _acceptedTerms = value ?? false),
                title: const Text('Aceito a política de uso da GoTrendLabs'),
              ),
            ],
            if (auth.error != null) ...[
              const SizedBox(height: 12),
              Text(
                auth.error!,
                style: const TextStyle(color: GtlColors.accentRed),
              ),
            ],
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: auth.busy ? null : _submit,
              icon: auth.busy
                  ? const SizedBox.square(
                      dimension: 16,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : Icon(_register ? Icons.person_add_alt_1 : Icons.login),
              label: Text(_register ? 'Criar e entrar' : 'Entrar'),
            ),
            TextButton(
              onPressed: auth.busy ? null : _recoverPassword,
              child: const Text('Enviar recuperação de senha'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _submit() async {
    final email = _email.text.trim();
    final password = _password.text;
    if (_register) {
      await ref
          .read(authControllerProvider.notifier)
          .register(_name.text.trim(), email, password, _acceptedTerms);
      return;
    }
    await ref.read(authControllerProvider.notifier).login(email, password);
  }

  Future<void> _recoverPassword() async {
    await ref
        .read(authControllerProvider.notifier)
        .requestPasswordReset(_email.text.trim());
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Se o email existir, enviaremos instruções de recuperação.',
          ),
        ),
      );
    }
  }
}
