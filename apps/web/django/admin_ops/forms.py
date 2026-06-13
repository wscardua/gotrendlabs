from decimal import Decimal, ROUND_DOWN

from django import forms

from apps.web.django.admin_ops.models import MobileAppRelease, SiteConfig


PROBABILITY_QUANT = Decimal("0.0001")


class MaintenanceConfigForm(forms.Form):
    maintenance_enabled = forms.BooleanField(label="Modo manutenção ativo", required=False)
    maintenance_message = forms.CharField(
        label="Mensagem pública",
        max_length=280,
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def clean_maintenance_message(self):
        message = (self.cleaned_data.get("maintenance_message") or "").strip()
        if self.cleaned_data.get("maintenance_enabled") and not message:
            raise forms.ValidationError("Informe a mensagem exibida na página de manutenção.")
        return message


class MobileMaintenanceConfigForm(forms.Form):
    mobile_maintenance_enabled = forms.BooleanField(label="Modo manutenção mobile ativo", required=False)
    mobile_maintenance_message = forms.CharField(
        label="Mensagem mobile",
        max_length=280,
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def clean_mobile_maintenance_message(self):
        message = (self.cleaned_data.get("mobile_maintenance_message") or "").strip()
        if self.cleaned_data.get("mobile_maintenance_enabled") and not message:
            raise forms.ValidationError("Informe a mensagem exibida no app mobile.")
        return message


class SiteEmailConfigForm(forms.Form):
    email_enabled = forms.BooleanField(label="Envio de email ativo", required=False)
    email_provider = forms.ChoiceField(label="Provedor", choices=SiteConfig.EMAIL_PROVIDER_CHOICES, initial=SiteConfig.EMAIL_PROVIDER_SMTP)
    smtp_host = forms.CharField(label="Servidor SMTP", max_length=255, required=False)
    smtp_port = forms.IntegerField(label="Porta", min_value=1, max_value=65535, initial=587)
    smtp_username = forms.CharField(label="Usuário SMTP", max_length=255, required=False)
    smtp_use_tls = forms.BooleanField(label="Usar TLS", required=False, initial=True)
    smtp_use_ssl = forms.BooleanField(label="Usar SSL", required=False)
    smtp_timeout_seconds = forms.IntegerField(label="Timeout em segundos", min_value=1, max_value=120, initial=10)
    default_from_email = forms.EmailField(label="Email remetente padrão", required=False)
    default_reply_to_email = forms.EmailField(label="Reply-to padrão", required=False)

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("smtp_use_tls") and cleaned_data.get("smtp_use_ssl"):
            raise forms.ValidationError("TLS e SSL não podem ficar ativos ao mesmo tempo.")
        if cleaned_data.get("email_enabled"):
            email_provider = cleaned_data.get("email_provider") or SiteConfig.EMAIL_PROVIDER_SMTP
            required_fields = {
                "default_from_email": "Informe o email remetente padrão.",
            }
            if email_provider == SiteConfig.EMAIL_PROVIDER_SMTP:
                required_fields["smtp_host"] = "Informe o servidor SMTP."
            for field, error in required_fields.items():
                if not cleaned_data.get(field):
                    self.add_error(field, error)
        return cleaned_data


class EmailTemplateForm(forms.Form):
    subject = forms.CharField(label="Assunto", max_length=255)
    body_text = forms.CharField(label="Corpo texto", widget=forms.Textarea(attrs={"rows": 10}))
    body_html = forms.CharField(label="Corpo HTML", required=False, widget=forms.Textarea(attrs={"rows": 8}))
    is_active = forms.BooleanField(label="Ativo", required=False, initial=True)


class PushTemplateForm(forms.Form):
    mode = forms.ChoiceField(label="Envio deste evento", choices=(("off", "Não enviar push"), ("immediate", "Enviar imediatamente"), ("digest", "Digest (futuro)")))
    policy_active = forms.BooleanField(label="Evento habilitado para push", required=False, initial=True)
    default_user_enabled = forms.BooleanField(label="Usuários recebem por padrão", required=False, initial=True)
    title = forms.CharField(label="Título", max_length=120)
    body = forms.CharField(label="Corpo", widget=forms.Textarea(attrs={"rows": 5}))
    is_active = forms.BooleanField(label="Template ativo", required=False, initial=True)


class PushTestDeliveryForm(forms.Form):
    device_id = forms.ChoiceField(label="Dispositivo")
    event_type = forms.ChoiceField(label="Tipo de teste")
    title = forms.CharField(label="Título", max_length=120, initial="Teste de push")
    body = forms.CharField(
        label="Corpo",
        max_length=240,
        initial="Mensagem de teste do GoTrendLabs.",
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def __init__(self, *args, devices=None, event_types=None, **kwargs):
        super().__init__(*args, **kwargs)
        device_choices = []
        for device in devices or []:
            username = getattr(device.user, "username", "") or getattr(device.user, "email", "") or f"user={device.user_id}"
            label = device.device_label or f"{device.platform} #{device.id}"
            version = f" · app {device.app_version}" if device.app_version else ""
            device_choices.append((str(device.id), f"#{device.id} · {username} · {label}{version}"))
        self.fields["device_id"].choices = device_choices
        self.fields["event_type"].choices = [("admin_push_test", "Teste administrativo")] + [
            (event_type, f"Teste como {event_type}") for event_type in event_types or []
        ]


class MobileAppReleaseForm(forms.ModelForm):
    class Meta:
        model = MobileAppRelease
        fields = ["version_name", "version_code", "apk", "release_notes", "is_active"]
        labels = {
            "version_name": "Versão",
            "version_code": "Código da versão",
            "apk": "APK Android",
            "release_notes": "Notas da versão",
            "is_active": "Publicar como versão ativa",
        }
        widgets = {
            "release_notes": forms.Textarea(attrs={"rows": 5}),
        }

    def clean_apk(self):
        apk = self.cleaned_data.get("apk")
        if not apk:
            return apk
        if not apk.name.lower().endswith(".apk"):
            raise forms.ValidationError("Envie um arquivo .apk.")
        if apk.size <= 0:
            raise forms.ValidationError("O APK enviado está vazio.")
        return apk


class EconomyConfigForm(forms.Form):
    wallet_recharge_min_balance_gtl = forms.IntegerField(
        label="Saldo máximo para solicitar recarga",
        min_value=0,
        max_value=1000000,
        initial=100,
    )
    referral_bonus_gtl = forms.IntegerField(
        label="Bônus por indicação validada",
        min_value=0,
        max_value=1000000,
        initial=200,
    )


class DaemonConfigForm(forms.Form):
    daemon_stale_after_minutes = forms.IntegerField(
        label="Minutos até status atrasado",
        min_value=1,
        max_value=1440,
        initial=7,
    )
    daemon_missing_after_minutes = forms.IntegerField(
        label="Minutos até status sem sinal",
        min_value=2,
        max_value=10080,
        initial=21,
    )

    def clean(self):
        cleaned_data = super().clean()
        stale_after = cleaned_data.get("daemon_stale_after_minutes")
        missing_after = cleaned_data.get("daemon_missing_after_minutes")
        if stale_after is not None and missing_after is not None and missing_after <= stale_after:
            self.add_error("daemon_missing_after_minutes", "O limite de sem sinal deve ser maior que o limite de atraso.")
        return cleaned_data


class RetentionConfigForm(forms.Form):
    system_log_retention_days = forms.IntegerField(
        label="Retenção de logs técnicos",
        min_value=1,
        max_value=3650,
        initial=90,
    )
    ai_audit_retention_days = forms.IntegerField(
        label="Retenção da auditoria IA",
        min_value=1,
        max_value=3650,
        initial=90,
    )


class AiConfigForm(forms.Form):
    ai_agents_enabled = forms.BooleanField(label="Agentes IA ativos", required=False)
    ai_commenting_enabled = forms.BooleanField(label="Comentários IA ativos", required=False)
    ai_predictions_enabled = forms.BooleanField(label="Previsões bot ativas", required=False)
    ai_llm_provider = forms.CharField(label="Provedor LLM", max_length=40, initial="openai")
    ai_llm_base_url = forms.URLField(label="Base URL LLM", max_length=255, initial="https://api.openai.com/v1")
    ai_model = forms.CharField(label="Modelo comentário", max_length=120, initial="gpt-5.4-mini")
    ai_high_reasoning_model = forms.CharField(label="Modelo alto raciocínio", max_length=120, initial="gpt-5.5")
    ai_market_cooldown_hours = forms.IntegerField(label="Cooldown por mercado (h)", min_value=1, max_value=720, initial=24)
    ai_max_comments_per_market_per_day = forms.IntegerField(label="Comentários por mercado/dia", min_value=1, max_value=10, initial=1)
    ai_max_comments_per_cycle = forms.IntegerField(label="Comentários por ciclo", min_value=0, max_value=100, initial=1)
    ai_max_comment_attempts_per_cycle = forms.IntegerField(label="Tentativas LLM por ciclo", min_value=1, max_value=100, initial=3)
    ai_comment_candidate_limit = forms.IntegerField(label="Mercados candidatos por ciclo", min_value=1, max_value=10000, initial=200)
    ai_max_comments_per_day = forms.IntegerField(label="Comentários por dia", min_value=0, max_value=10000, initial=20)
    ai_comment_max_chars = forms.IntegerField(label="Máximo de caracteres", min_value=120, max_value=1000, initial=700)
    ai_min_humans_for_prediction = forms.IntegerField(label="Mínimo de humanos para previsão", min_value=0, max_value=10000, initial=1)
    ai_max_stake_gtl = forms.IntegerField(label="Stake máximo bot", min_value=1, max_value=1000000, initial=25)
    ai_max_predictions_per_cycle = forms.IntegerField(label="Previsões por ciclo", min_value=0, max_value=100, initial=1)
    ai_max_predictions_per_day = forms.IntegerField(label="Previsões por dia", min_value=0, max_value=10000, initial=10)
    ai_skip_if_human_comments_recent = forms.BooleanField(label="Pular se houver comentário humano recente", required=False)
    ai_recent_human_comment_window_hours = forms.IntegerField(label="Janela comentário humano (h)", min_value=1, max_value=720, initial=6)
    ai_openai_timeout_seconds = forms.IntegerField(label="Timeout OpenAI", min_value=1, max_value=120, initial=20)
    ai_openai_max_retries = forms.IntegerField(label="Retries OpenAI", min_value=0, max_value=5, initial=1)
    ai_paused_until = forms.DateTimeField(
        label="Pausado até",
        required=False,
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
    )
    ai_pause_reason = forms.CharField(label="Motivo da pausa", required=False, widget=forms.Textarea(attrs={"rows": 2}), max_length=2000)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        control_style = (
            "display:block!important;visibility:visible!important;opacity:1!important;"
            "width:100%;min-height:44px;border:1px solid #ded7c8;border-radius:14px;"
            "padding:11px 12px;background:#fffaf0;color:#111315;"
        )
        checkbox_style = (
            "display:inline-block!important;visibility:visible!important;opacity:1!important;"
            "width:18px;height:18px;margin-top:2px;accent-color:#136f4a;"
        )
        for field in self.fields.values():
            if isinstance(field, forms.BooleanField):
                field.widget.attrs["style"] = checkbox_style
            else:
                existing_style = field.widget.attrs.get("style", "")
                field.widget.attrs["style"] = f"{existing_style}{control_style}"


class AiAgentForm(forms.Form):
    AGENT_TYPE_CHOICES = (("analyst", "Analyst"), ("liquidity", "Liquidity"), ("contrarian", "Contrarian"))

    name = forms.CharField(label="Nome", max_length=120)
    agent_type = forms.ChoiceField(label="Tipo", choices=AGENT_TYPE_CHOICES)
    user_id = forms.ChoiceField(label="Usuário bot oficial")
    is_active = forms.BooleanField(label="Ativo", required=False)
    personality_prompt = forms.CharField(label="Persona editável", required=False, widget=forms.Textarea(attrs={"rows": 5}), max_length=5000)
    comment_style = forms.CharField(label="Estilo de comentário", required=False, max_length=120)
    max_comments_per_day = forms.IntegerField(label="Comentários/dia do agente", required=False, min_value=0, max_value=10000)
    max_predictions_per_day = forms.IntegerField(label="Previsões/dia do agente", required=False, min_value=0, max_value=10000)
    max_stake_gtl = forms.IntegerField(label="Stake máximo do agente", required=False, min_value=0, max_value=1000000)
    cooldown_hours = forms.IntegerField(label="Cooldown do agente (h)", required=False, min_value=0, max_value=10000)
    min_humans_for_prediction = forms.IntegerField(label="Mínimo de humanos do agente", required=False, min_value=0, max_value=10000)

    def __init__(self, *args, bot_user_choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [("", "Selecione um usuário bot ativo")]
        choices.extend(bot_user_choices or [])
        self.fields["user_id"].choices = choices
        if not bot_user_choices:
            self.fields["user_id"].help_text = "Nenhum usuário ativo com is_bot=true foi encontrado."

    def clean_user_id(self):
        value = self.cleaned_data.get("user_id")
        if not value:
            raise forms.ValidationError("Escolha um usuário bot ativo.")
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise forms.ValidationError("Usuário bot inválido.") from exc

    def clean(self):
        cleaned_data = super().clean()
        agent_type = cleaned_data.get("agent_type")
        if agent_type == "analyst":
            cleaned_data["max_predictions_per_day"] = None
            cleaned_data["max_stake_gtl"] = None
            cleaned_data["min_humans_for_prediction"] = None
        elif agent_type == "liquidity":
            cleaned_data["personality_prompt"] = ""
            cleaned_data["comment_style"] = ""
            cleaned_data["max_comments_per_day"] = None
            cleaned_data["cooldown_hours"] = None
        elif agent_type == "contrarian":
            cleaned_data["personality_prompt"] = ""
            cleaned_data["comment_style"] = ""
            cleaned_data["max_comments_per_day"] = None
            cleaned_data["max_predictions_per_day"] = None
            cleaned_data["max_stake_gtl"] = None
            cleaned_data["cooldown_hours"] = None
            cleaned_data["min_humans_for_prediction"] = None
        return cleaned_data

    def to_payload(self):
        data = {}
        for field, value in self.cleaned_data.items():
            data[field] = "" if value is None and field in {"personality_prompt", "comment_style"} else value
        return data


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
    event = forms.CharField(label="Evento", max_length=80)
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
        event_choices = [("", "Selecione o evento")]
        for category in self.taxonomy.get("categories", []):
            if category.get("is_blocked"):
                continue
            category_choices.append((category.get("name", ""), category.get("name", "")))
            for subcategory in category.get("subcategories", []):
                if subcategory.get("is_blocked"):
                    continue
                subcategory_choices.append((subcategory.get("name", ""), subcategory.get("name", "")))
                for event in subcategory.get("events", []):
                    if event.get("is_blocked"):
                        continue
                    event_choices.append((event.get("name", ""), event.get("name", "")))
        if len(category_choices) > 1:
            self.fields["category"] = forms.ChoiceField(label="Categoria", choices=category_choices)
        if len(subcategory_choices) > 1:
            self.fields["subcategory"] = forms.ChoiceField(label="Subcategoria", choices=subcategory_choices)
        if len(event_choices) > 1:
            self.fields["event"] = forms.ChoiceField(label="Evento", choices=event_choices)

    def clean(self):
        cleaned_data = super().clean()
        category_name = cleaned_data.get("category")
        subcategory_name = cleaned_data.get("subcategory")
        event_name = cleaned_data.get("event")
        categories = self.taxonomy.get("categories", [])
        if not categories or not category_name or not subcategory_name or not event_name:
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
            return cleaned_data
        if subcategory.get("is_blocked"):
            self.add_error("subcategory", "Subcategoria bloqueada para novos mercados.")
        if "events" not in subcategory:
            return cleaned_data
        event = next((item for item in subcategory.get("events", []) if item.get("name") == event_name), None)
        if not event:
            self.add_error("event", "Escolha um evento da subcategoria selecionada.")
        elif event.get("is_blocked"):
            self.add_error("event", "Evento bloqueado para novos mercados.")
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
            "event": self.cleaned_data["event"],
            "status_label": self.initial.get("status_label") or "Rascunho",
            "primary_outcome": self.initial.get("primary_outcome") or primary["label"],
            "primary_probability_exact": self.initial.get("primary_probability_exact", primary.get("probability_exact", primary["probability"])),
            "secondary_probability_exact": self.initial.get("secondary_probability_exact", secondary.get("probability_exact", secondary["probability"])),
            "volume_gtl": self.initial.get("volume_gtl") or "0 GT₵",
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
    notice = forms.CharField(label="Aviso da categoria", max_length=500, required=False, widget=forms.Textarea(attrs={"rows": 3}))


class AdminSubcategoryForm(forms.Form):
    category_slug = forms.SlugField(widget=forms.HiddenInput)
    name = forms.CharField(label="Subcategoria", max_length=80)
    slug = forms.SlugField(label="Slug", max_length=100, required=False)
    notice = forms.CharField(label="Aviso da subcategoria", max_length=500, required=False, widget=forms.Textarea(attrs={"rows": 3}))


class AdminEventForm(forms.Form):
    category_slug = forms.SlugField(widget=forms.HiddenInput)
    subcategory_slug = forms.SlugField(widget=forms.HiddenInput)
    name = forms.CharField(label="Evento", max_length=80)
    slug = forms.SlugField(label="Slug", max_length=100, required=False)
    notice = forms.CharField(label="Aviso do evento", max_length=500, required=False, widget=forms.Textarea(attrs={"rows": 3}))


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
    amount_gtl = forms.IntegerField(label="Recompensa GT₵", min_value=1, max_value=10000, initial=50)
    note = forms.CharField(label="Nota operacional", widget=forms.Textarea, required=False)


class WalletRechargeApprovalForm(forms.Form):
    amount_gtl = forms.IntegerField(label="Recarga GT₵", min_value=1, max_value=10000, initial=250)
    note = forms.CharField(label="Nota operacional", widget=forms.Textarea, required=False)


class WalletRechargeRejectForm(forms.Form):
    note = forms.CharField(label="Nota operacional", max_length=2000, widget=forms.Textarea)


class AdminUserNoteForm(forms.Form):
    note = forms.CharField(label="Nota operacional", max_length=2000, widget=forms.Textarea)


class AdminUserWalletAdjustmentForm(forms.Form):
    direction = forms.ChoiceField(label="Direção", choices=(("", "Selecione"), ("credit", "Crédito"), ("debit", "Débito")))
    amount_gtl = forms.IntegerField(label="Valor GT₵", min_value=1, max_value=1000000)
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


class AdminUserBotForm(forms.Form):
    is_bot = forms.BooleanField(label="Conta controlada por robôs", required=False)
    note = forms.CharField(label="Nota operacional", max_length=2000, widget=forms.Textarea)


class AdminUserPasswordResetForm(forms.Form):
    note = forms.CharField(label="Nota operacional", max_length=2000, widget=forms.Textarea)


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
    is_active = forms.BooleanField(label="Exibir badge e conquistas históricas", required=False, initial=True)
    rule_active = forms.BooleanField(label="Conceder para novas conquistas", required=False, initial=True)
    rule_type = forms.ChoiceField(label="Regra automática", choices=BADGE_RULE_CHOICES)
    threshold_value = forms.DecimalField(label="Valor mínimo/posição", min_value=Decimal("0"), max_digits=12, decimal_places=4, initial=1)
    category = forms.CharField(label="Categoria", max_length=80, required=False)
    subcategory = forms.CharField(label="Subcategoria", max_length=80, required=False)
    event = forms.CharField(label="Evento", max_length=80, required=False)

    def __init__(self, *args, taxonomy=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.taxonomy = taxonomy or {"categories": []}
        category_choices = [("", "Todas as categorias")]
        subcategory_choices = [("", "Todas as subcategorias")]
        event_choices = [("", "Todos os eventos")]
        for category in self.taxonomy.get("categories", []):
            if category.get("is_blocked"):
                continue
            category_name = category.get("name", "")
            category_choices.append((category_name, category_name))
            for subcategory in category.get("subcategories", []):
                if subcategory.get("is_blocked"):
                    continue
                subcategory_choices.append((subcategory.get("name", ""), subcategory.get("name", "")))
                for event in subcategory.get("events", []):
                    if event.get("is_blocked"):
                        continue
                    event_choices.append((event.get("name", ""), event.get("name", "")))
        self.fields["category"] = forms.ChoiceField(label="Categoria", choices=category_choices, required=False)
        self.fields["subcategory"] = forms.ChoiceField(label="Subcategoria", choices=subcategory_choices, required=False)
        self.fields["event"] = forms.ChoiceField(label="Evento", choices=event_choices, required=False)

    def clean(self):
        cleaned_data = super().clean()
        category_name = cleaned_data.get("category")
        subcategory_name = cleaned_data.get("subcategory")
        event_name = cleaned_data.get("event")
        categories = self.taxonomy.get("categories", [])
        if event_name and not subcategory_name:
            self.add_error("event", "Escolha uma subcategoria antes do evento.")
            return cleaned_data
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
        if event_name:
            event = next((item for item in subcategory.get("events", []) if item.get("name") == event_name), None)
            if not event:
                self.add_error("event", "Escolha um evento da subcategoria selecionada.")
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
            "rule_active": self.cleaned_data.get("rule_active", False),
            "rule_type": self.cleaned_data["rule_type"],
            "threshold_value": float(self.cleaned_data.get("threshold_value") or 0),
            "category": self.cleaned_data.get("category") or "",
            "subcategory": self.cleaned_data.get("subcategory") or "",
            "event": self.cleaned_data.get("event") or "",
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
