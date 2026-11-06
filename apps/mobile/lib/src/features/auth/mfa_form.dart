import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'auth_controller.dart';

class MfaForm extends ConsumerStatefulWidget {
  const MfaForm({super.key});

  @override
  ConsumerState<MfaForm> createState() => _MfaFormState();
}

class _MfaFormState extends ConsumerState<MfaForm> {
  final _code = TextEditingController();
  bool _recovery = false;
  String? _codeError;

  @override
  void dispose() {
    _code.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);
    final controller = ref.read(authControllerProvider.notifier);
    final enrollment = auth.challenge?.enrollmentRequired == true;
    return Padding(
      padding: EdgeInsets.fromLTRB(
        20,
        20,
        20,
        MediaQuery.viewInsetsOf(context).bottom + 20,
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              auth.recoveryCodes.isNotEmpty
                  ? 'Guarde seus códigos de recuperação'
                  : 'Verificação em duas etapas',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 16),
            if (auth.recoveryCodes.isNotEmpty) ...[
              const Text(
                'Estes códigos aparecem apenas uma vez. Guarde-os em um local seguro. Cada código pode ser usado uma única vez se você perder acesso ao autenticador.',
              ),
              const SizedBox(height: 12),
              SelectableText(auth.recoveryCodes.join('\n')),
              const SizedBox(height: 16),
              FilledButton(
                onPressed: controller.acknowledgeRecoveryCodes,
                child: const Text('Guardei os códigos'),
              ),
            ] else ...[
              if (enrollment) ...[
                const Text(
                  'Adicione esta chave manualmente ao seu aplicativo autenticador e informe o código gerado.',
                ),
                if (auth.manualKey != null) SelectableText(auth.manualKey!),
                if (auth.manualKey == null)
                  TextButton(
                    onPressed: auth.busy ? null : controller.enrollMfa,
                    child: const Text('Carregar chave do autenticador'),
                  ),
              ] else
                Text(
                  _recovery
                      ? 'Informe um dos seus códigos de recuperação.'
                      : 'Informe o código de seis dígitos do seu aplicativo autenticador.',
                ),
              const SizedBox(height: 12),
              TextField(
                controller: _code,
                enabled: !auth.busy,
                autocorrect: false,
                enableSuggestions: false,
                keyboardType: _recovery
                    ? TextInputType.text
                    : TextInputType.number,
                decoration: InputDecoration(
                  errorText: _codeError,
                  labelText: _recovery
                      ? 'Código de recuperação'
                      : 'Código do autenticador',
                ),
              ),
              if (!enrollment)
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Usar código de recuperação'),
                  value: _recovery,
                  onChanged: auth.busy
                      ? null
                      : (value) => setState(() {
                          _recovery = value;
                          if (mounted) _code.clear();
                        }),
                ),
              if (auth.error != null)
                Text(
                  auth.error!,
                  style: TextStyle(color: Theme.of(context).colorScheme.error),
                ),
              const SizedBox(height: 16),
              FilledButton(
                onPressed: auth.busy || (enrollment && auth.manualKey == null)
                    ? null
                    : () async {
                        final code = _code.text.trim();
                        if (code.isEmpty) {
                          setState(
                            () =>
                                _codeError = 'Informe o código para continuar.',
                          );
                          return;
                        }
                        setState(() => _codeError = null);
                        await controller.verifyMfa(code, recovery: _recovery);
                        if (mounted) _code.clear();
                      },
                child: Text(auth.busy ? 'Verificando…' : 'Confirmar e entrar'),
              ),
              TextButton(
                onPressed: auth.busy ? null : controller.cancelMfa,
                child: const Text('Voltar ao login'),
              ),
              const Text(
                'Se o desafio expirar, volte ao login e entre novamente.',
              ),
            ],
          ],
        ),
      ),
    );
  }
}
