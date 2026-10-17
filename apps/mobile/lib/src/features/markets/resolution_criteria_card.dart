import 'package:flutter/material.dart';

import '../../theme.dart';
import '../../ui/gtl_components.dart';

class ResolutionCriteriaText extends StatelessWidget {
  const ResolutionCriteriaText({super.key, required this.criteria});

  final String criteria;

  @override
  Widget build(BuildContext context) {
    final text = criteria.isEmpty ? 'Critério não informado.' : criteria;
    final style = DefaultTextStyle.of(context).style;
    return LayoutBuilder(
      builder: (context, constraints) {
        final painter = TextPainter(
          text: TextSpan(text: text, style: style),
          maxLines: 3,
          textDirection: Directionality.of(context),
          textScaler: MediaQuery.textScalerOf(context),
          locale: Localizations.maybeLocaleOf(context),
        )..layout(maxWidth: constraints.maxWidth);
        final truncated = painter.didExceedMaxLines;
        painter.dispose();
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              text,
              style: style,
              maxLines: 3,
              overflow: TextOverflow.ellipsis,
            ),
            if (truncated) ...[
              const SizedBox(height: 8),
              TextButton.icon(
                onPressed: () => showModalBottomSheet<void>(
                  context: context,
                  isScrollControlled: true,
                  showDragHandle: true,
                  backgroundColor: GtlColors.surfaceElevated,
                  builder: (context) => SafeArea(
                    child: SizedBox(
                      height: MediaQuery.sizeOf(context).height * .75,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 20),
                            child: Row(
                              children: [
                                const Expanded(
                                  child: GtlSectionTitle(
                                    title: 'Critério de resolução',
                                  ),
                                ),
                                IconButton(
                                  onPressed: () => Navigator.of(context).pop(),
                                  icon: const Icon(Icons.close),
                                  tooltip: 'Fechar',
                                ),
                              ],
                            ),
                          ),
                          Expanded(
                            child: SingleChildScrollView(
                              padding: const EdgeInsets.fromLTRB(
                                20,
                                12,
                                20,
                                24,
                              ),
                              child: SelectableText(text),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
                icon: const Icon(Icons.read_more),
                label: const Text('Ver critério de resolução completo'),
              ),
            ],
          ],
        );
      },
    );
  }
}
