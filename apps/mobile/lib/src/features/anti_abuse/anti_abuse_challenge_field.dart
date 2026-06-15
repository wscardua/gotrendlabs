import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_client.dart';
import '../../theme.dart';
import '../../ui/gtl_components.dart';
import 'anti_abuse_repository.dart';

class AntiAbuseChallengeField extends ConsumerWidget {
  const AntiAbuseChallengeField({
    super.key,
    required this.controller,
    this.enabled = true,
  });

  final TextEditingController controller;
  final bool enabled;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final challenge = ref.watch(antiAbuseChallengeProvider);
    return GtlSurface(
      color: GtlColors.surfaceInk,
      borderColor: GtlColors.accentYellow.withValues(alpha: 0.42),
      padding: const EdgeInsets.all(14),
      child: challenge.when(
        loading: () => Row(
          children: [
            const SizedBox.square(
              dimension: 16,
              child: CircularProgressIndicator(strokeWidth: 2),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                'Preparando verificação anti-abuso...',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            ),
          ],
        ),
        error: (error, stack) => Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Icon(Icons.error_outline, color: GtlColors.accentYellow),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                ApiFailure.fromObject(error).message,
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            ),
            IconButton(
              onPressed: () => ref.invalidate(antiAbuseChallengeProvider),
              icon: const Icon(Icons.refresh),
              tooltip: 'Recarregar desafio',
            ),
          ],
        ),
        data: (value) => Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Icon(
                  Icons.verified_user_outlined,
                  color: GtlColors.accentYellow,
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Verificação rápida',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        value.prompt,
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: GtlColors.textPrimary,
                        ),
                      ),
                    ],
                  ),
                ),
                IconButton(
                  onPressed: enabled
                      ? () {
                          controller.clear();
                          ref.invalidate(antiAbuseChallengeProvider);
                        }
                      : null,
                  icon: const Icon(Icons.refresh),
                  tooltip: 'Novo desafio',
                ),
              ],
            ),
            const SizedBox(height: 12),
            TextField(
              controller: controller,
              enabled: enabled,
              keyboardType: TextInputType.number,
              textInputAction: TextInputAction.done,
              decoration: const InputDecoration(labelText: 'Resposta'),
            ),
          ],
        ),
      ),
    );
  }
}
