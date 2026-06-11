import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../theme.dart';
import '../../ui/gtl_components.dart';
import 'auth_controller.dart';

Future<void> showLoginSheet(BuildContext context) {
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    backgroundColor: GtlColors.surfaceElevated,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(GtlRadii.large)),
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
  bool _rememberLogin = true;
  String? _localError;

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
            GtlEditorialHeader(
              kicker: 'Conta GoTrendLabs',
              title: _register ? 'Criar conta' : 'Entrar',
              body:
                  'Sessão para prever, comentar, acompanhar wallet e construir reputação.',
              trailing: IconButton(
                onPressed: () => Navigator.of(context).pop(),
                icon: const Icon(Icons.close),
                tooltip: 'Fechar',
              ),
              icon: Icons.account_circle_outlined,
            ),
            const SizedBox(height: 12),
            SegmentedButton<bool>(
              segments: const [
                ButtonSegment(value: false, label: Text('Login')),
                ButtonSegment(value: true, label: Text('Cadastro')),
              ],
              selected: {_register},
              onSelectionChanged: (value) => setState(() {
                _register = value.first;
                _localError = null;
              }),
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
            ] else ...[
              const SizedBox(height: 8),
              SwitchListTile(
                value: _rememberLogin,
                contentPadding: EdgeInsets.zero,
                onChanged: (value) => setState(() => _rememberLogin = value),
                title: const Text('Lembrar login'),
                subtitle: const Text('Mantém a sessão neste dispositivo.'),
              ),
            ],
            if (_localError != null || auth.error != null) ...[
              const SizedBox(height: 12),
              Text(
                _localError ?? auth.error!,
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
    final localError = _validateForm(email, password);
    if (localError != null) {
      setState(() => _localError = localError);
      return;
    }
    setState(() => _localError = null);
    if (_register) {
      await ref
          .read(authControllerProvider.notifier)
          .register(_name.text.trim(), email, password, _acceptedTerms);
      return;
    }
    await ref
        .read(authControllerProvider.notifier)
        .login(email, password, rememberSession: _rememberLogin);
  }

  Future<void> _recoverPassword() async {
    final email = _email.text.trim();
    if (!_isValidEmail(email)) {
      setState(() => _localError = 'Informe um email válido.');
      return;
    }
    setState(() => _localError = null);
    await ref.read(authControllerProvider.notifier).requestPasswordReset(email);
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

  String? _validateForm(String email, String password) {
    if (!_isValidEmail(email)) {
      return 'Informe um email válido.';
    }
    if (password.isEmpty) {
      return 'Informe sua senha.';
    }
    if (_register && _name.text.trim().isEmpty) {
      return 'Informe um nome público.';
    }
    if (_register && !_acceptedTerms) {
      return 'Aceite a política de uso para criar sua conta.';
    }
    return null;
  }

  bool _isValidEmail(String email) {
    return RegExp(r'^[^\s@]+@[^\s@]+\.[^\s@]+$').hasMatch(email);
  }
}
