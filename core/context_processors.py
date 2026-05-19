from core.domain_client import get_domain_client


def session_context(request):
    client = get_domain_client()
    return {"viewer": client.viewer()}
