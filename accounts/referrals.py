from django.urls import reverse

from accounts.api_client import AuthAPIError, get_referral


def referral_card_context(request, token):
    try:
        referral = get_referral(token)
    except AuthAPIError:
        return {"enabled": False, "code": "", "bonus_gtl": 0, "url": "", "reason": "Link de indicação indisponível no momento."}
    code = referral.get("code", "")
    url = request.build_absolute_uri(f"{reverse('register')}?ref={code}") if code else ""
    return {**referral, "url": url}
