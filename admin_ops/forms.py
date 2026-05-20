from decimal import Decimal, ROUND_DOWN

from django import forms


PROBABILITY_QUANT = Decimal("0.0001")


def _display_probability(value):
    return int(Decimal(str(value or 0)).quantize(PROBABILITY_QUANT).to_integral_value(rounding=ROUND_DOWN))


def _even_probability_exact(total):
    if total <= 0:
        return Decimal("0.0000")
    return (Decimal("100") / Decimal(total)).quantize(PROBABILITY_QUANT)


class AdminMarketForm(forms.Form):
    title = forms.CharField(label="Pergunta PT-BR", max_length=240)
    slug = forms.SlugField(label="Slug", max_length=160, required=False)
    summary = forms.CharField(label="Resumo", widget=forms.Textarea)
    kind = forms.ChoiceField(label="Tipo", choices=(("binary", "Sim/Não"), ("multiple", "Múltipla escolha")))
    category = forms.CharField(label="Categoria", max_length=80)
    subcategory = forms.CharField(label="Subcategoria", max_length=80)
    source = forms.CharField(label="Fonte esperada", max_length=180)
    close_label = forms.CharField(label="Mensagem pública de fechamento", max_length=120, required=False)
    close_at = forms.DateTimeField(
        label="Data/hora de fechamento",
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
    )
    close_timezone = forms.ChoiceField(
        label="Fuso de fechamento",
        choices=(
            ("America/Sao_Paulo", "America/Sao_Paulo"),
            ("UTC", "UTC"),
            ("America/New_York", "America/New_York"),
            ("Europe/London", "Europe/London"),
        ),
    )
    auto_close_enabled = forms.BooleanField(label="Fechamento automático pelo daemon", required=False, initial=True)
    is_featured = forms.BooleanField(label="Usar como destaque do feed", required=False)
    thumb = forms.CharField(label="Sigla do card", max_length=12, required=False)
    thumb_color = forms.CharField(label="Cor do card", max_length=20, widget=forms.TextInput(attrs={"type": "color"}))
    image_url = forms.CharField(widget=forms.HiddenInput, required=False)
    thumbnail_file = forms.FileField(label="Thumbnail do card", required=False)
    resolution_criteria = forms.CharField(label="Critério de resolução", widget=forms.Textarea)
    admin_notes = forms.CharField(label="Notas internas", widget=forms.Textarea, required=False)
    option_1_label = forms.CharField(label="Opção 1", max_length=80, required=False)
    option_1_hint = forms.CharField(label="Hint 1", max_length=160, required=False)
    option_2_label = forms.CharField(label="Opção 2", max_length=80, required=False)
    option_2_hint = forms.CharField(label="Hint 2", max_length=160, required=False)
    option_3_label = forms.CharField(label="Opção 3", max_length=80, required=False)
    option_3_hint = forms.CharField(label="Hint 3", max_length=160, required=False)

    def __init__(self, *args, taxonomy=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.taxonomy = taxonomy or {"categories": []}
        category_choices = [("", "Selecione a categoria")]
        subcategory_choices = [("", "Selecione a subcategoria")]
        for category in self.taxonomy.get("categories", []):
            if category.get("is_blocked"):
                continue
            category_choices.append((category.get("name", ""), category.get("name", "")))
            for subcategory in category.get("subcategories", []):
                if subcategory.get("is_blocked"):
                    continue
                subcategory_choices.append((subcategory.get("name", ""), subcategory.get("name", "")))
        if len(category_choices) > 1:
            self.fields["category"] = forms.ChoiceField(label="Categoria", choices=category_choices)
        if len(subcategory_choices) > 1:
            self.fields["subcategory"] = forms.ChoiceField(label="Subcategoria", choices=subcategory_choices)

    def clean(self):
        cleaned_data = super().clean()
        category_name = cleaned_data.get("category")
        subcategory_name = cleaned_data.get("subcategory")
        categories = self.taxonomy.get("categories", [])
        if not categories or not category_name or not subcategory_name:
            return cleaned_data
        category = next((item for item in categories if item.get("name") == category_name), None)
        if not category:
            self.add_error("category", "Escolha uma categoria cadastrada.")
            return cleaned_data
        if category.get("is_blocked"):
            self.add_error("category", "Categoria bloqueada para novos mercados.")
        subcategory = next(
            (item for item in category.get("subcategories", []) if item.get("name") == subcategory_name),
            None,
        )
        if not subcategory:
            self.add_error("subcategory", "Escolha uma subcategoria da categoria selecionada.")
        elif subcategory.get("is_blocked"):
            self.add_error("subcategory", "Subcategoria bloqueada para novos mercados.")
        return cleaned_data

    def _posted_option_rows(self):
        labels = self.data.getlist("option_label")
        hints = self.data.getlist("option_hint")
        return [
            {"label": label.strip(), "hint": (hints[index] if index < len(hints) else "").strip()}
            for index, label in enumerate(labels)
            if label.strip()
        ]

    def option_rows(self):
        if self.is_bound:
            rows = self._posted_option_rows()
            if rows:
                return rows
            rows = []
            for index in range(1, 4):
                label = self.cleaned_data.get(f"option_{index}_label") if hasattr(self, "cleaned_data") else self.data.get(f"option_{index}_label")
                if label:
                    rows.append({"label": label, "hint": self.data.get(f"option_{index}_hint", "")})
            return rows
        return self.initial.get("options") or [
            {"label": "SIM", "hint": "Opção afirmativa"},
            {"label": "NAO", "hint": "Opção negativa"},
        ]

    def calculated_option_rows(self):
        if self.cleaned_data.get("kind") == "binary":
            initial_options = self.initial.get("options") or []
            if self.initial.get("slug") and len(initial_options) >= 2:
                return [
                    {
                        "label": option.get("label", ""),
                        "probability": option.get("probability", _display_probability(option.get("probability_exact", 0))),
                        "probability_exact": option.get("probability_exact", option.get("probability", 0)),
                        "hint": option.get("hint", ""),
                    }
                    for option in initial_options[:2]
                ]
            return [
                {"label": "SIM", "probability": 50, "probability_exact": 50.0, "hint": "Opção afirmativa"},
                {"label": "NAO", "probability": 50, "probability_exact": 50.0, "hint": "Opção negativa"},
            ]
        rows = self.option_rows()
        if not rows:
            return []
        exact = _even_probability_exact(len(rows))
        return [
            {**row, "probability": _display_probability(exact), "probability_exact": float(exact)}
            for row in rows
        ]

    def to_payload(self):
        options = self.calculated_option_rows()
        primary = options[0] if options else {"label": "", "probability": 0}
        secondary = options[1] if len(options) > 1 else {"probability": 0}
        return {
            "title": self.cleaned_data["title"],
            "slug": self.cleaned_data.get("slug") or None,
            "summary": self.cleaned_data.get("summary") or "",
            "kind": self.cleaned_data["kind"],
            "category": self.cleaned_data["category"],
            "subcategory": self.cleaned_data["subcategory"],
            "status_label": self.initial.get("status_label") or "Rascunho",
            "primary_outcome": self.initial.get("primary_outcome") or primary["label"],
            "primary_probability_exact": self.initial.get("primary_probability_exact", primary.get("probability_exact", primary["probability"])),
            "secondary_probability_exact": self.initial.get("secondary_probability_exact", secondary.get("probability_exact", secondary["probability"])),
            "volume_oc": self.initial.get("volume_oc") or "0 OC",
            "participants": self.initial.get("participants") or "0 usuários",
            "source": self.cleaned_data.get("source") or "",
            "closes_in": "",
            "close_label": self.cleaned_data.get("close_label") or "",
            "thumb": self.cleaned_data.get("thumb") or "",
            "thumb_color": self.cleaned_data.get("thumb_color") or "#d8ece2",
            "image_url": self.cleaned_data.get("image_url") or "",
            "resolution_criteria": self.cleaned_data.get("resolution_criteria") or "",
            "close_at": self.cleaned_data["close_at"].isoformat(),
            "close_timezone": self.cleaned_data["close_timezone"],
            "auto_close_enabled": self.cleaned_data.get("auto_close_enabled", False),
            "is_featured": self.cleaned_data.get("is_featured", False),
            "resolution_type": self.initial.get("resolution_type") or "",
            "resolution_note": self.initial.get("resolution_note") or "",
            "admin_notes": self.cleaned_data.get("admin_notes") or "",
            "options": options,
        }


class AdminCategoryForm(forms.Form):
    name = forms.CharField(label="Categoria", max_length=80)
    slug = forms.SlugField(label="Slug", max_length=100, required=False)


class AdminSubcategoryForm(forms.Form):
    category_slug = forms.SlugField(widget=forms.HiddenInput)
    name = forms.CharField(label="Subcategoria", max_length=80)
    slug = forms.SlugField(label="Slug", max_length=100, required=False)


class QueueReviewForm(forms.Form):
    status = forms.ChoiceField(
        label="Status",
        choices=(
            ("pending", "Pendente"),
            ("reviewed", "Revisado"),
            ("rejected", "Rejeitado"),
        ),
    )
    note = forms.CharField(label="Nota operacional", widget=forms.Textarea, required=False)


class FeedbackRewardForm(forms.Form):
    amount_oc = forms.IntegerField(label="Recompensa OC", min_value=1, max_value=10000, initial=50)
    note = forms.CharField(label="Nota operacional", widget=forms.Textarea, required=False)


class AdminUserNoteForm(forms.Form):
    note = forms.CharField(label="Nota operacional", max_length=2000, widget=forms.Textarea)


class AdminUserWalletAdjustmentForm(forms.Form):
    direction = forms.ChoiceField(label="Direção", choices=(("", "Selecione"), ("credit", "Crédito"), ("debit", "Débito")))
    amount_oc = forms.IntegerField(label="Valor OC", min_value=1, max_value=1000000)
    note = forms.CharField(label="Nota operacional", max_length=2000, widget=forms.Textarea)


class AdminUserRoleForm(forms.Form):
    role = forms.ChoiceField(
        label="Papel administrativo",
        choices=(
            ("user", "Usuário comum"),
            ("staff", "Staff/Admin"),
            ("superuser", "Superuser"),
        ),
    )
    note = forms.CharField(label="Nota operacional", max_length=2000, widget=forms.Textarea)

    def role_flags(self):
        role = self.cleaned_data["role"]
        return {
            "is_staff": role in {"staff", "superuser"},
            "is_superuser": role == "superuser",
        }


RESOLUTION_TIMEZONE_CHOICES = (
    ("America/Sao_Paulo", "America/Sao_Paulo"),
    ("UTC", "UTC"),
    ("America/New_York", "America/New_York"),
    ("America/Los_Angeles", "America/Los_Angeles"),
    ("Europe/London", "Europe/London"),
    ("Europe/Lisbon", "Europe/Lisbon"),
)


BADGE_TYPE_CHOICES = (
    ("global", "Global"),
    ("category", "Categoria"),
    ("performance", "Performance"),
    ("engagement", "Engajamento"),
)

BADGE_RULE_CHOICES = (
    ("founding_member", "Membro fundador"),
    ("resolved_predictions_count", "Previsões resolvidas"),
    ("correct_predictions_count", "Acertos"),
    ("streak_count", "Sequência de acertos"),
    ("ranking_position", "Posição no ranking"),
    ("comments_count", "Comentários visíveis"),
    ("approved_suggestions_count", "Sugestões aprovadas"),
    ("rewarded_feedback_count", "Feedback recompensado"),
)


class AdminBadgeForm(forms.Form):
    code = forms.SlugField(label="Código", max_length=80, required=False)
    name = forms.CharField(label="Nome", max_length=120)
    description = forms.CharField(label="Descrição", max_length=255, widget=forms.Textarea)
    rule_description = forms.CharField(label="Descrição da regra", max_length=255, required=False)
    badge_type = forms.ChoiceField(label="Tipo", choices=BADGE_TYPE_CHOICES)
    image_url = forms.CharField(widget=forms.HiddenInput, required=False)
    image_dark_url = forms.CharField(widget=forms.HiddenInput, required=False)
    badge_image = forms.FileField(label="Imagem para tema claro", required=False)
    badge_dark_image = forms.FileField(label="Imagem para tema escuro", required=False)
    is_active = forms.BooleanField(label="Badge ativa", required=False, initial=True)
    rule_type = forms.ChoiceField(label="Regra automática", choices=BADGE_RULE_CHOICES)
    threshold_value = forms.DecimalField(label="Valor mínimo/posição", min_value=Decimal("0"), max_digits=12, decimal_places=4, initial=1)
    category = forms.CharField(label="Categoria", max_length=80, required=False)
    subcategory = forms.CharField(label="Subcategoria", max_length=80, required=False)

    def __init__(self, *args, taxonomy=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.taxonomy = taxonomy or {"categories": []}
        category_choices = [("", "Todas as categorias")]
        subcategory_choices = [("", "Todas as subcategorias")]
        for category in self.taxonomy.get("categories", []):
            if category.get("is_blocked"):
                continue
            category_name = category.get("name", "")
            category_choices.append((category_name, category_name))
            for subcategory in category.get("subcategories", []):
                if subcategory.get("is_blocked"):
                    continue
                subcategory_choices.append((subcategory.get("name", ""), subcategory.get("name", "")))
        self.fields["category"] = forms.ChoiceField(label="Categoria", choices=category_choices, required=False)
        self.fields["subcategory"] = forms.ChoiceField(label="Subcategoria", choices=subcategory_choices, required=False)

    def clean(self):
        cleaned_data = super().clean()
        category_name = cleaned_data.get("category")
        subcategory_name = cleaned_data.get("subcategory")
        categories = self.taxonomy.get("categories", [])
        if not subcategory_name:
            return cleaned_data
        if not category_name:
            self.add_error("subcategory", "Escolha uma categoria antes da subcategoria.")
            return cleaned_data
        category = next((item for item in categories if item.get("name") == category_name), None)
        if not category:
            self.add_error("category", "Escolha uma categoria cadastrada.")
            return cleaned_data
        subcategory = next((item for item in category.get("subcategories", []) if item.get("name") == subcategory_name), None)
        if not subcategory:
            self.add_error("subcategory", "Escolha uma subcategoria da categoria selecionada.")
        return cleaned_data

    def to_payload(self):
        return {
            "code": self.cleaned_data.get("code") or None,
            "name": self.cleaned_data["name"],
            "description": self.cleaned_data["description"],
            "rule_description": self.cleaned_data.get("rule_description") or self.cleaned_data["description"],
            "badge_type": self.cleaned_data["badge_type"],
            "image_url": self.cleaned_data.get("image_url") or "",
            "image_dark_url": self.cleaned_data.get("image_dark_url") or "",
            "is_active": self.cleaned_data.get("is_active", False),
            "rule_type": self.cleaned_data["rule_type"],
            "threshold_value": float(self.cleaned_data.get("threshold_value") or 0),
            "category": self.cleaned_data.get("category") or "",
            "subcategory": self.cleaned_data.get("subcategory") or "",
        }


class MarketResolutionForm(forms.Form):
    winning_option_id = forms.ChoiceField(label="Resultado")
    resolved_at = forms.DateTimeField(
        label="Data/hora da resolução",
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )
    resolution_timezone = forms.ChoiceField(label="Timezone", choices=RESOLUTION_TIMEZONE_CHOICES)
    source_url = forms.CharField(label="Fonte pública", max_length=500)
    note = forms.CharField(label="Justificativa operacional", widget=forms.Textarea)

    def __init__(self, *args, market=None, **kwargs):
        super().__init__(*args, **kwargs)
        from datetime import datetime
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

        options = (market or {}).get("options", [])
        timezone_name = (market or {}).get("resolution_timezone") or (market or {}).get("close_timezone") or "UTC"
        try:
            target_timezone = ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError:
            timezone_name = "UTC"
            target_timezone = ZoneInfo("UTC")
        if timezone_name not in dict(RESOLUTION_TIMEZONE_CHOICES):
            timezone_name = "UTC"
        if not self.is_bound:
            self.initial.setdefault("resolved_at", datetime.now(target_timezone).strftime("%Y-%m-%dT%H:%M"))
            self.initial.setdefault("resolution_timezone", timezone_name)
        self.fields["winning_option_id"].choices = [("", "Selecione o resultado")] + [
            (str(option.get("id")), "NÃO" if option.get("label") == "NAO" else option.get("label", ""))
            for option in options
            if option.get("id")
        ]

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data
