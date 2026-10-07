"""Authlib protocol engine with PostgreSQL persistence owned by FastAPI."""

from collections import defaultdict
from datetime import timedelta
import uuid
from authlib.oauth2 import AuthorizationServer
from authlib.oauth2.rfc6749 import OAuth2Request, InvalidRequestError
from authlib.oauth2.rfc6749.requests import OAuth2Payload
from authlib.oauth2.rfc6749.grants import AuthorizationCodeGrant, RefreshTokenGrant
from authlib.oauth2.rfc7636 import CodeChallenge
from authlib.common.urls import add_params_to_uri
from fastapi import HTTPException
from apps.api.backend_api import editorial_auth as a
from apps.api.backend_api.editorial_schemas import SCOPES
from psycopg.types.json import Jsonb


class Payload(OAuth2Payload):
    def __init__(self, data):
        self._data = data

    @property
    def data(self):
        return self._data

    @property
    def datalist(self):
        return defaultdict(list, {k: [v] for k, v in self._data.items()})


class Request(OAuth2Request):
    def __init__(self, method, uri, data):
        super().__init__(method, uri)
        self.payload = Payload(data)

    @property
    def form(self):
        return self.payload.data

    @property
    def args(self):
        return self.payload.data


class Client:
    def __init__(self, row):
        self.row = row

    def get_client_id(self):
        return str(self.row["id"])

    def get_default_redirect_uri(self):
        return self.row["redirect_uris"][0]

    def check_redirect_uri(self, uri):
        return uri in self.row["redirect_uris"]

    def check_response_type(self, value):
        return value == "code"

    def check_grant_type(self, value):
        return value in ("authorization_code", "refresh_token")

    def check_endpoint_auth_method(self, method, endpoint):
        return method == "none"

    def get_allowed_scope(self, scope):
        return " ".join(s for s in (scope or "").split() if s in SCOPES)


class Artifact:
    def __init__(self, row):
        self.row = row
        self.code_challenge = row["metadata"].get("code_challenge")
        self.code_challenge_method = "S256"

    def get_redirect_uri(self):
        return self.row["metadata"].get("redirect_uri")

    def get_scope(self):
        return " ".join(self.row["scopes"])

    def check_client(self, client):
        return str(self.row["origin"]["client_id"]) == client.get_client_id()


class S256(CodeChallenge):
    SUPPORTED_CODE_CHALLENGE_METHOD = ["S256"]

    def validate_code_challenge(self, grant, redirect_uri):
        super().validate_code_challenge(grant, redirect_uri)
        d = grant.request.payload.data
        if not d.get("code_challenge") or d.get("code_challenge_method") != "S256":
            raise InvalidRequestError("PKCE S256 required")


class Code(AuthorizationCodeGrant):
    TOKEN_ENDPOINT_AUTH_METHODS = ["none"]

    def save_authorization_code(self, code, request):
        grant = request.user
        a.insert_token(
            self.server.cursor,
            grant,
            "code",
            a.resource(),
            min(a.now() + timedelta(minutes=5), grant["expires_at"]),
            metadata={
                k: request.payload.data[k]
                for k in ("redirect_uri", "code_challenge", "code_challenge_method")
            },
            value=code,
        )

    def query_authorization_code(self, value, client):
        return self.server.artifact(value, "code", client)

    def delete_authorization_code(self, code):
        self.server.consume(code)

    def authenticate_user(self, code):
        return code.row

    def create_authorization_response(self, redirect_uri, grant_user):
        code, body, headers = super().create_authorization_response(
            redirect_uri, grant_user
        )
        return (
            code,
            body,
            [
                (
                    k,
                    add_params_to_uri(v, [("iss", a.issuer())])
                    if k == "Location"
                    else v,
                )
                for k, v in headers
            ],
        )


class Refresh(RefreshTokenGrant):
    TOKEN_ENDPOINT_AUTH_METHODS = ["none"]
    INCLUDE_NEW_REFRESH_TOKEN = True

    def authenticate_refresh_token(self, value):
        return self.server.artifact(value, "refresh", self.request.client)

    def authenticate_user(self, token):
        return token.row

    def revoke_old_credential(self, token):
        self.server.consume(token)


class Server(AuthorizationServer):
    def __init__(self, cursor):
        super().__init__(scopes_supported=list(SCOPES))
        self.cursor = cursor
        self.register_grant(Code, [S256(required=True)])
        self.register_grant(Refresh)
        self.register_token_generator("default", self.generate)

    def query_client(self, identifier):
        try:
            identifier = uuid.UUID(identifier)
        except (ValueError, TypeError, AttributeError):
            return None
        self.cursor.execute(
            "SELECT * FROM gotrendlabs_agent_oauth_clients WHERE id=%s", (identifier,)
        )
        row = self.cursor.fetchone()
        return Client(row) if row else None

    def create_oauth2_request(self, request):
        return request

    def handle_response(self, status, body, headers):
        return status, body, headers

    def send_signal(self, *args, **kwargs):
        pass

    def artifact(self, value, kind, client):
        try:
            t = a.validate(self.cursor, value, a.resource(), kind, allow_consumed=True)
        except HTTPException:
            return None
        if str(t["origin"]["client_id"]) != client.get_client_id():
            return None
        if t["consumed_at"]:
            self.cursor.execute(
                "UPDATE gotrendlabs_agent_grants SET revoked_at=%s WHERE id=%s",
                (a.now(), t["grant_id"]),
            )
            return None
        if self.current_request.payload.data.get("resource") != t["audience"]:
            return None
        return Artifact(t)

    def consume(self, artifact):
        self.cursor.execute(
            "UPDATE gotrendlabs_agent_tokens SET consumed_at=%s WHERE id=%s",
            (a.now(), artifact.row["id"]),
        )

    def generate(
        self, grant_type, client, user, scope, expires_in, include_refresh_token
    ):
        expiry = min(
            a.now() + timedelta(minutes=10),
            user["expires_at"],
            user.get("origin", user)["expires_at"],
        )
        return {
            "access_token": __import__("secrets").token_urlsafe(48),
            "refresh_token": __import__("secrets").token_urlsafe(48),
            "token_type": "Bearer",
            "expires_in": max(1, int((expiry - a.now()).total_seconds())),
            "scope": scope,
        }

    def save_token(self, token, request):
        origin = request.user
        for key, kind, ttl in [
            ("access_token", "access", timedelta(minutes=10)),
            ("refresh_token", "refresh", timedelta(days=90)),
        ]:
            if key in token:
                a.insert_token(
                    self.cursor,
                    origin,
                    kind,
                    a.resource(),
                    min(
                        a.now() + ttl,
                        origin.get("origin", origin)["expires_at"],
                        origin["integration"]["expires_at"]
                        if "integration" in origin
                        else origin["expires_at"],
                    ),
                    scopes=token["scope"].split(),
                    value=token[key],
                )

    def token_response(self, data):
        req = Request("POST", a.issuer() + "/oauth/token", data)
        self.current_request = req
        if data.get("resource") != a.resource():
            return 400, {"error": "invalid_target"}, []
        return self.create_token_response(req)

    def consent_info(self, data):
        req = Request("GET", a.issuer() + "/oauth/authorize", data)
        self.current_request = req
        if (
            data.get("resource") != a.resource()
            or not data.get("state")
            or not data.get("redirect_uri")
        ):
            raise InvalidRequestError("resource, state and redirect_uri required")
        grant = self.get_authorization_grant(req)
        grant.validate_authorization_request()
        if not data.get("scope") or not set(data["scope"].split()).issubset(SCOPES):
            raise InvalidRequestError("explicit supported scopes required")
        return req

    def authorize(self, data, user, integration_id):
        req = self.consent_info(data)
        i = a.integration(self.cursor, integration_id)
        scopes = data["scope"].split()
        if not set(scopes).issubset(i["scopes"]):
            a.fail("forbidden_scope")
        identifier = uuid.uuid4()
        expiry = min(a.now() + timedelta(days=90), i["expires_at"])
        self.cursor.execute(
            "INSERT INTO gotrendlabs_agent_grants(id,integration_id,client_id,user_id,scopes,expires_at,revoked_at,created_at) VALUES(%s,%s,%s,%s,%s,%s,NULL,%s)",
            (
                identifier,
                i["id"],
                req.client.row["id"],
                user["id"],
                Jsonb(scopes),
                expiry,
                a.now(),
            ),
        )
        origin = {
            "integration_id": i["id"],
            "grant_id": identifier,
            "credential_id": None,
            "scopes": scopes,
            "expires_at": expiry,
        }
        return self.create_authorization_response(req, grant_user=origin), identifier
