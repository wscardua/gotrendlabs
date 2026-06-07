import 'package:flutter/material.dart';

import '../../theme.dart';

class TrustScreen extends StatelessWidget {
  const TrustScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 3,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Confiança'),
          bottom: const TabBar(
            tabs: [
              Tab(text: 'Política'),
              Tab(text: 'Conceitos'),
              Tab(text: 'Segurança'),
            ],
          ),
        ),
        body: const TabBarView(
          children: [_PolicyTab(), _ConceptsTab(), _SecurityTab()],
        ),
      ),
    );
  }
}

class _PolicyTab extends StatelessWidget {
  const _PolicyTab();

  @override
  Widget build(BuildContext context) {
    return const _InfoList(
      title: 'Regras para previsão educativa.',
      subtitle:
          'Ao criar conta, você participa de uma rede social de previsões com GT₵ educativas, reputação pública e resolução auditável.',
      items: [
        _InfoItem(
          icon: Icons.savings_outlined,
          title: 'GT₵ não é dinheiro real',
          body:
              'GTL Credits são uma unidade interna de participação. Não são sacáveis, transferíveis ou promessa financeira.',
        ),
        _InfoItem(
          icon: Icons.person_outline,
          title: 'Conta e histórico',
          body:
              'Handle, reputação, badges e previsões resolvidas podem aparecer publicamente. Dados privados ficam separados.',
        ),
        _InfoItem(
          icon: Icons.front_hand_outlined,
          title: 'Conduta',
          body:
              'Spam, abuso, manipulação coordenada, exploração de bugs, assédio e conteúdo ilegal podem passar por moderação.',
        ),
        _InfoItem(
          icon: Icons.smart_toy_outlined,
          title: 'IA oficial identificada',
          body:
              'Agentes oficiais não fingem ser humanos e não entram em ranking, badges, reputação ou recompensas públicas.',
        ),
      ],
    );
  }
}

class _ConceptsTab extends StatelessWidget {
  const _ConceptsTab();

  @override
  Widget build(BuildContext context) {
    return const _InfoList(
      title: 'Como a GoTrendLabs funciona.',
      subtitle:
          'Mercados objetivos, consenso da comunidade, carteira educativa e reputação pública caminham juntos.',
      items: [
        _InfoItem(
          icon: Icons.help_outline,
          title: 'Mercados',
          body:
              'Cada mercado é uma pergunta objetiva, com opções finitas, prazo e critério de resolução verificável.',
        ),
        _InfoItem(
          icon: Icons.account_balance_wallet_outlined,
          title: 'Carteira educativa',
          body:
              'Ao prever, parte das GT₵ fica reservada. Cancelamentos devolvem a reserva; resoluções aplicam o resultado.',
        ),
        _InfoItem(
          icon: Icons.auto_graph,
          title: 'Consenso',
          body:
              'A probabilidade exibida é consenso agregado, não promessa de resultado. Ela pode mudar até o fechamento.',
        ),
        _InfoItem(
          icon: Icons.workspace_premium_outlined,
          title: 'Reputação e badges',
          body:
              'Acertos em mercados resolvidos constroem reputação, ranking e sinais públicos de contribuição.',
        ),
      ],
    );
  }
}

class _SecurityTab extends StatelessWidget {
  const _SecurityTab();

  @override
  Widget build(BuildContext context) {
    return const _InfoList(
      title: 'Confiança para prever com tranquilidade.',
      subtitle:
          'Ações importantes exigem sessão válida e resultados seguem critérios verificáveis.',
      items: [
        _InfoItem(
          icon: Icons.verified_user_outlined,
          title: 'Ações autenticadas',
          body:
              'Prever, comentar, reagir, acessar carteira e editar perfil exigem conta autenticada.',
        ),
        _InfoItem(
          icon: Icons.fact_check_outlined,
          title: 'Resolução auditável',
          body:
              'Resultado exige opção vencedora, fonte ou justificativa, data e registro operacional.',
        ),
        _InfoItem(
          icon: Icons.history,
          title: 'Extrato conciliável',
          body:
              'Carteira educativa e histórico seguem a trilha da API. Se houver divergência, vale o registro auditável.',
        ),
        _InfoItem(
          icon: Icons.shield_outlined,
          title: 'Dados protegidos',
          body:
              'Pesos sensíveis, heurísticas antifraude e dados privados de perfil não viram conteúdo público.',
        ),
      ],
    );
  }
}

class _InfoList extends StatelessWidget {
  const _InfoList({
    required this.title,
    required this.subtitle,
    required this.items,
  });

  final String title;
  final String subtitle;
  final List<_InfoItem> items;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text(title, style: Theme.of(context).textTheme.headlineSmall),
        const SizedBox(height: 8),
        Text(subtitle),
        const SizedBox(height: 14),
        for (final item in items) _InfoCard(item: item),
      ],
    );
  }
}

class _InfoItem {
  const _InfoItem({
    required this.icon,
    required this.title,
    required this.body,
  });

  final IconData icon;
  final String title;
  final String body;
}

class _InfoCard extends StatelessWidget {
  const _InfoCard({required this.item});

  final _InfoItem item;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            DecoratedBox(
              decoration: BoxDecoration(
                color: GtlColors.accentBlue.withValues(alpha: 0.12),
                border: Border.all(color: GtlColors.border),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Padding(
                padding: const EdgeInsets.all(10),
                child: Icon(item.icon, color: GtlColors.accentBlue),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    item.title,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 5),
                  Text(item.body),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
