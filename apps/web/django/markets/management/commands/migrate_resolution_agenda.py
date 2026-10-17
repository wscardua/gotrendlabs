"""Reviewed, all-or-nothing schedule supplements. Dry-run is the default."""
import json
from datetime import datetime
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from apps.api.backend_api.db import get_connection
from apps.api.backend_api import resolution_schedule as schedules


def apply_inventory(cursor, inventory, *, apply=False, actor_id=None):
    if inventory.get('schema') != 'gtl-resolution-agenda/v2' or not isinstance(inventory.get('inventory_id'),str) or not inventory['inventory_id'].strip():
        raise CommandError('Formato de inventário inválido.')
    results = []
    for item in sorted(inventory['markets'], key=lambda x:x['market_id']):
        if item.get('reviewed') is not True or not isinstance(item.get('reviewer'),str) or not item['reviewer'].strip() or not item.get('reviewed_at'):
            raise CommandError(f"Mercado {item['market_id']}: revisão explícita ausente.")
        try:
            reviewed_at = datetime.fromisoformat(item['reviewed_at'].replace('Z','+00:00'))
            if reviewed_at.tzinfo is None:
                raise ValueError('offset required')
        except (ValueError,TypeError,AttributeError) as exc:
            raise CommandError('Revisão exige instante inequívoco com offset.') from exc
        if not isinstance(item.get('reason'),str) or not item['reason'].strip():
            raise CommandError('Motivo obrigatório.')
        for key in schedules.DATES:
            source = item.get('sources',{}).get(key)
            if (not isinstance(source,dict) or source.get('origin') not in {'explicit_text_candidate','reviewed_operational_decision'}
                or not source.get('excerpt') or not source.get('source')):
                raise CommandError('Proveniência revisada obrigatória por data; decisão pendente não autoriza aplicação.')
        cursor.execute('SELECT * FROM gotrendlabs_markets WHERE id=%s FOR UPDATE', (item['market_id'],))
        market = cursor.fetchone()
        if not market:
            raise CommandError('Mercado inexistente.')
        cursor.execute('SELECT payload_hash,definition_version FROM market_integrity_definitions WHERE market_id=%s', (market['id'],))
        definition = cursor.fetchone()
        cursor.execute('SELECT revision FROM gotrendlabs_agent_editorial_drafts WHERE market_id=%s', (market['id'],))
        editorial = cursor.fetchone()
        if (market['slug'] != item['slug'] or market['status'] != item['status'] or not definition
            or definition['payload_hash'] != item['definition_hash']
            or definition['definition_version'] != item['definition_version']
            or (editorial['revision'] if editorial else None) != item['editorial_revision']):
            raise CommandError('Inventário obsoleto: estado/hash/revisão/identidade divergente.')
        if market['status'] not in {'open','locked'}:
            raise CommandError('Somente ativos publicados; draft segue revisão editorial e terminal não recebe data fabricada.')
        proposed = dict(item['proposed'])
        if set(proposed) != set(schedules.FIELDS):
            raise CommandError('Proposta exige somente resolução prevista e fuso.')
        for k in schedules.DATES:
            proposed[k] = datetime.fromisoformat(proposed[k].replace('Z','+00:00')) if proposed.get(k) else None
        schedules.validate_schedule({**market, **proposed}, required=True)
        if market['schedule_version']:
            if all(market[k] == proposed[k] for k in schedules.FIELDS) and not schedules.verify(cursor, market):
                results.append({'market_id':market['id'],'action':'already_applied'})
                continue
            raise CommandError('Agenda existente diferente; use reagendamento autorizado.')
        if item.get('expected_schedule_version') != 0:
            raise CommandError('Versão esperada inválida.')
        results.append({'market_id':market['id'],'action':'apply' if apply else 'would_apply'})
        if apply:
            cursor.execute('UPDATE gotrendlabs_markets SET '+','.join(k+'=%s' for k in schedules.FIELDS)+' WHERE id=%s',
                (*[proposed[k] for k in schedules.FIELDS],market['id']))
            schedules.register(cursor,market['id'],actor_id=actor_id,reason=item['reason'],provenance={
                'inventory_id':inventory['inventory_id'],'reviewer':item['reviewer'],'reviewed_at':item['reviewed_at'],
                'sources':item['sources'],'query_coverage':inventory.get('coverage'),'queried_at':inventory.get('queried_at')})
    return results


class Command(BaseCommand):
    help = 'Validate reviewed inventory; append signed supplements only with --apply and staff actor.'

    def add_arguments(self, parser):
        parser.add_argument('inventory')
        parser.add_argument('--apply', action='store_true')
        parser.add_argument('--actor-id', type=int)
        parser.add_argument('--backup-confirmed', action='store_true')

    def handle(self, *args, **options):
        if options['apply'] and (not options['backup_confirmed'] or not options['actor_id']):
            raise CommandError('--apply exige --backup-confirmed e --actor-id de staff autorizado.')
        inventory = json.loads(Path(options['inventory']).read_text())
        with get_connection() as connection:
            with connection.cursor() as cursor:
                if options['apply']:
                    cursor.execute('SELECT id FROM gotrendlabs_users WHERE id=%s AND is_active AND (is_staff OR is_superuser)', (options['actor_id'],))
                    if not cursor.fetchone():
                        raise CommandError('Ator staff ativo obrigatório.')
                result = apply_inventory(cursor, inventory, apply=options['apply'], actor_id=options['actor_id'])
                if not options['apply']:
                    connection.rollback()
        self.stdout.write(json.dumps({'mode':'apply' if options['apply'] else 'dry-run','markets':result},ensure_ascii=False))
