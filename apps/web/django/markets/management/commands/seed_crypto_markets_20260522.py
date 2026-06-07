from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.web.django.markets.models import Market, MarketCategory, MarketEvent, MarketOption, MarketSubcategory


CRYPTO_NOTICE = "Mercados de criptoativos envolvem alta volatilidade. Nao caracteriza recomendacao de investimento."
MARKET_CLOSE_AT = datetime(2026, 6, 30, 23, 59, tzinfo=ZoneInfo("America/Sao_Paulo"))
MARKET_CLOSE_LABEL = "Fecha em 30/06/2026 23:59 BRT"


MARKETS = [
    {
        "slug": "ethereum-acima-3000-30-junho-2026",
        "title": "O Ethereum estará acima de US$ 3.000 em 30 de junho de 2026?",
        "summary": "Mercado sobre o preço público do ETH em USD na CoinGecko no fechamento de 30 de junho de 2026.",
        "event": "Ethereum",
        "source": "CoinGecko Ethereum: https://www.coingecko.com/en/coins/ethereum",
        "resolution_criteria": (
            "Vence Sim se o preço em USD exibido pela CoinGecko para Ethereum (ETH) estiver acima de US$ 3.000 "
            "em 30/06/2026 às 23:59 BRT. Caso contrário, vence Nao. Se a CoinGecko ficar indisponível por mais "
            "de 24h, usar CoinMarketCap Ethereum no mesmo horário e critério; se nenhuma fonte verificável estiver "
            "disponível, cancelar o mercado."
        ),
        "thumb": "ETH",
        "thumb_color": "#7f8cff",
        "image_url": "/media/market_thumbnails/generated-ethereum-acima-3000-30-junho-2026.png",
        "probabilities": (Decimal("50.0000"), Decimal("50.0000")),
    },
    {
        "slug": "dogecoin-top10-30-junho-2026",
        "title": "Dogecoin estará no Top 10 geral da CoinGecko por market cap em 30 de junho de 2026?",
        "summary": "Mercado sobre a posição geral de DOGE por capitalização de mercado no ranking público da CoinGecko.",
        "event": "Dogecoin",
        "source": "CoinGecko ranking geral: https://www.coingecko.com",
        "resolution_criteria": (
            "Vence Sim se Dogecoin (DOGE) estiver na posição #10 ou melhor no ranking geral da CoinGecko por market cap "
            "em 30/06/2026 às 23:59 BRT. Caso contrário, vence Nao. Se a CoinGecko ficar indisponível por mais de 24h, "
            "usar o ranking geral da CoinMarketCap para Dogecoin no mesmo horário e critério; se nenhuma fonte "
            "verificável estiver disponível, cancelar o mercado."
        ),
        "thumb": "DOGE",
        "thumb_color": "#c2a633",
        "image_url": "/media/market_thumbnails/generated-dogecoin-top10-30-junho-2026.png",
        "probabilities": (Decimal("50.0000"), Decimal("50.0000")),
    },
    {
        "slug": "solana-acima-xrp-ranking-30-junho-2026",
        "title": "Solana estará acima de XRP no ranking geral da CoinGecko por market cap em 30 de junho de 2026?",
        "summary": "Mercado sobre a disputa de posição entre SOL e XRP no ranking público de capitalização da CoinGecko.",
        "event": "Solana",
        "source": "CoinGecko ranking geral: https://www.coingecko.com",
        "resolution_criteria": (
            "Vence Sim se Solana (SOL) estiver melhor colocada que XRP no ranking geral da CoinGecko por market cap "
            "em 30/06/2026 às 23:59 BRT. Caso contrário, vence Nao. Se a CoinGecko ficar indisponível por mais de 24h, "
            "usar o ranking geral da CoinMarketCap para SOL e XRP no mesmo horário e critério; se nenhuma fonte "
            "verificável estiver disponível, cancelar o mercado."
        ),
        "thumb": "SOL",
        "thumb_color": "#14f195",
        "image_url": "/media/market_thumbnails/generated-solana-acima-xrp-ranking-30-junho-2026.png",
        "probabilities": (Decimal("50.0000"), Decimal("50.0000")),
    },
]


class Command(BaseCommand):
    help = "Seed the approved 2026-05-22 mainstream crypto market lote."

    def add_arguments(self, parser):
        parser.add_argument(
            "--status",
            choices=("open", "draft"),
            default="open",
            help="Initial status for the seeded markets. Defaults to open for the approved production lote.",
        )
        parser.add_argument("--dry-run", action="store_true", help="Show what would be created or updated without writing.")

    def handle(self, *args, **options):
        status = options["status"]
        dry_run = options["dry_run"]
        status_label = "Aberto" if status == "open" else "Rascunho"

        if dry_run:
            self.stdout.write("DRY-RUN taxonomy: Mercado / Cripto with notice")
            for payload in MARKETS:
                exists = Market.objects.filter(slug=payload["slug"]).exists()
                action = "update" if exists else "create"
                self.stdout.write(f"DRY-RUN {action}: {payload['slug']} ({status})")
            return

        category, _ = MarketCategory.objects.update_or_create(
            slug="mercado",
            defaults={"name": "Mercado", "is_blocked": False, "blocked_reason": ""},
        )
        subcategory, _ = MarketSubcategory.objects.update_or_create(
            category=category,
            slug="cripto",
            defaults={"name": "Cripto", "notice": CRYPTO_NOTICE, "is_blocked": False, "blocked_reason": ""},
        )
        if subcategory.notice != CRYPTO_NOTICE:
            subcategory.notice = CRYPTO_NOTICE
            subcategory.save(update_fields=["notice"])

        seeded = []
        for index, payload in enumerate(MARKETS, start=1):
            event, _ = MarketEvent.objects.update_or_create(
                subcategory=subcategory,
                slug=payload["event"].lower(),
                defaults={"name": payload["event"], "is_blocked": False, "blocked_reason": ""},
            )
            primary_probability, secondary_probability = payload["probabilities"]
            existing_market = Market.objects.filter(slug=payload["slug"]).first()
            market_defaults = {
                "category": category,
                "subcategory": subcategory,
                "event": event,
                "title": payload["title"],
                "summary": payload["summary"],
                "kind": "binary",
                "status": status,
                "status_label": status_label,
                "primary_outcome": "Sim",
                "primary_probability_exact": primary_probability,
                "secondary_probability_exact": secondary_probability,
                "volume_gtl": "0 GT₵",
                "participants": "0 usuários",
                "source": payload["source"],
                "closes_in": "39d",
                "close_label": MARKET_CLOSE_LABEL,
                "thumb": payload["thumb"],
                "thumb_color": payload["thumb_color"],
                "image_url": payload["image_url"],
                "resolution_criteria": payload["resolution_criteria"],
                "close_at": MARKET_CLOSE_AT,
                "close_timezone": "America/Sao_Paulo",
                "auto_close_enabled": True,
                "is_featured": False,
                "display_order": 1000 + index,
                "updated_at": timezone.now(),
            }
            if existing_market and existing_market.status not in {"draft", "scheduled", "open"}:
                market_defaults["status"] = existing_market.status
                market_defaults["status_label"] = existing_market.status_label
            market, created = Market.objects.update_or_create(slug=payload["slug"], defaults=market_defaults)
            for option_index, (label, probability) in enumerate(
                (("Sim", primary_probability), ("Nao", secondary_probability)),
                start=1,
            ):
                MarketOption.objects.update_or_create(
                    market=market,
                    label=label,
                    defaults={"probability_exact": probability, "display_order": option_index},
                )
            seeded.append((market.slug, "created" if created else "updated"))

        for slug, action in seeded:
            self.stdout.write(f"{action}: {slug}")
        self.stdout.write(f"Done: Mercado / Cripto seeded with {len(seeded)} markets ({status}).")
