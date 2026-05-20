from django import forms
from django.contrib.auth.password_validation import validate_password


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(label="Senha", widget=forms.PasswordInput)
    remember_me = forms.BooleanField(label="Lembrar meu acesso neste dispositivo", required=False)


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(label="Email")


class PasswordResetConfirmForm(forms.Form):
    password = forms.CharField(label="Nova senha", widget=forms.PasswordInput)
    password_confirm = forms.CharField(label="Confirmar nova senha", widget=forms.PasswordInput)

    def clean_password(self):
        password = self.cleaned_data["password"]
        validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")
        if password and password_confirm and password != password_confirm:
            self.add_error("password_confirm", "As senhas não conferem.")
        return cleaned_data


class RegisterForm(forms.Form):
    display_name = forms.CharField(label="Nome público", max_length=150)
    email = forms.EmailField(label="Email")
    language = forms.ChoiceField(label="Idioma", choices=(("pt-br", "PT-BR"), ("en", "EN")))
    password = forms.CharField(label="Senha", widget=forms.PasswordInput)
    terms_accepted = forms.BooleanField(label="Aceito a política de uso", required=True)

    def clean_email(self):
        return self.cleaned_data["email"]

    def clean_password(self):
        password = self.cleaned_data["password"]
        validate_password(password)
        return password


class ProfileForm(forms.Form):
    SEX_CHOICES = (
        ("", "Não informado"),
        ("male", "Masculino"),
        ("female", "Feminino"),
        ("other", "Outro"),
        ("prefer_not_to_say", "Prefiro não informar"),
    )

    display_name = forms.CharField(label="Nome", max_length=150)
    handle = forms.CharField(label="Identificador", max_length=150)
    email = forms.EmailField(label="Email")
    preferred_language = forms.ChoiceField(label="Idioma", choices=(("pt-br", "PT-BR"), ("en", "EN")))
    birth_date = forms.DateField(label="Data de nascimento", required=False, widget=forms.DateInput(attrs={"type": "date"}))
    sex = forms.ChoiceField(label="Sexo", choices=SEX_CHOICES, required=False)
    bio = forms.CharField(label="Bio", max_length=1000, required=False, widget=forms.Textarea)

    def clean_handle(self):
        value = self.cleaned_data["handle"].strip().lstrip("@")
        return f"@{value}" if value else value

    def clean_birth_date(self):
        value = self.cleaned_data["birth_date"]
        return value.isoformat() if value else ""
