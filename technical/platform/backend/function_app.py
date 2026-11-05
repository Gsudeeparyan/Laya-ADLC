"""Azure Functions entry points for the Laya Excel Expert (SharePoint) Copilot agent.

Sign-in: App Service Authentication (Easy Auth) validates the caller's Entra ID token
before any code runs. Each call then exchanges that token for a Microsoft Graph token
(on-behalf-of), so the service can only open files the signed-in person can open.
All business logic is in service.py.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for p in (HERE / "packages", HERE.parent / "src"):  # deployed copy, or the repo when run locally
    if p.exists():
        sys.path.insert(0, str(p))

import azure.functions as func  # noqa: E402

from adlc_excel import OpError  # noqa: E402
from adlc_excel.regions import TargetError  # noqa: E402
from graph import ConflictError, GraphClient, GraphError  # noqa: E402
from service import ServiceError, WorkbookService  # noqa: E402
from vault_store import InMemoryVaultStore, TableVaultStore  # noqa: E402

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)  # Easy Auth sits in front
_store = TableVaultStore() if os.environ.get("VAULT_TABLE_URL") else InMemoryVaultStore()


def _claims(token: str) -> dict:
    """Read claims from a token Easy Auth has already validated."""
    try:
        payload = token.split(".")[1]
        return json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    except Exception:
        return {}


def _graph_token(user_token: str) -> str:
    if os.environ.get("ADLC_DEV_GRAPH_TOKEN"):  # local testing only
        return os.environ["ADLC_DEV_GRAPH_TOKEN"]
    import msal

    cca = msal.ConfidentialClientApplication(
        os.environ["AAD_CLIENT_ID"],
        authority=f"https://login.microsoftonline.com/{os.environ['AAD_TENANT_ID']}",
        client_credential=os.environ["AAD_CLIENT_SECRET"],
    )
    result = cca.acquire_token_on_behalf_of(user_token, scopes=["https://graph.microsoft.com/.default"])
    if "access_token" not in result:
        raise GraphError(401, "I couldn't sign in to SharePoint on your behalf. Try signing in again.")
    return result["access_token"]


def _handle(req: func.HttpRequest, action) -> func.HttpResponse:
    try:
        body = req.get_json()
    except ValueError:
        body = {}
    auth = req.headers.get("Authorization", "")
    if not auth.lower().startswith("bearer "):
        return _json({"error": "Please sign in."}, 401)
    user_token = auth.split(" ", 1)[1]
    claims = _claims(user_token)
    svc = WorkbookService(GraphClient(_graph_token(user_token)), _store,
                          user_id=claims.get("oid", "unknown"), user_name=claims.get("name", ""))
    try:
        return _json(action(svc, body))
    except ConflictError as exc:
        return _json({"error": str(exc)}, 409)
    except (OpError, TargetError, ServiceError, ValueError, KeyError) as exc:
        return _json({"error": str(exc).strip("'\"")}, 400)
    except GraphError as exc:
        return _json({"error": str(exc)}, exc.status if 400 <= exc.status < 500 else 502)
    except Exception:  # never leak data in errors
        logging.exception("Unexpected error")
        return _json({"error": "Something went wrong on my side. Nothing was saved."}, 500)


def _json(obj, status: int = 200) -> func.HttpResponse:
    return func.HttpResponse(json.dumps(obj, ensure_ascii=False, default=str), status_code=status,
                             mimetype="application/json")


@app.route(route="workbook/inspect", methods=["POST"])
def inspect_workbook(req: func.HttpRequest) -> func.HttpResponse:
    return _handle(req, lambda s, b: s.inspect(b["fileUrl"], int(b.get("sampleRows", 3))))


@app.route(route="workbook/query", methods=["POST"])
def query_workbook(req: func.HttpRequest) -> func.HttpResponse:
    return _handle(req, lambda s, b: s.query(b["fileUrl"], b.get("sheet"), b.get("table"), b.get("columns"),
                                             b.get("where"), int(b.get("limit", 100)), int(b.get("offset", 0))))


@app.route(route="workbook/preview", methods=["POST"])
def preview_changes(req: func.HttpRequest) -> func.HttpResponse:
    return _handle(req, lambda s, b: s.preview(b["fileUrl"], b["ops"]))


@app.route(route="workbook/apply", methods=["POST"])
def apply_changes(req: func.HttpRequest) -> func.HttpResponse:
    return _handle(req, lambda s, b: s.apply(b["fileUrl"], b["ops"], b.get("summary")))


@app.route(route="pii/scan", methods=["POST"])
def scan_for_pii(req: func.HttpRequest) -> func.HttpResponse:
    return _handle(req, lambda s, b: s.pii_scan(b["fileUrl"]))


@app.route(route="pii/clean-copy", methods=["POST"])
def create_pii_free_copy(req: func.HttpRequest) -> func.HttpResponse:
    return _handle(req, lambda s, b: s.pii_clean_copy(b["fileUrl"], b.get("profile", "restore")))


@app.route(route="pii/restore-copy", methods=["POST"])
def restore_pii_copy(req: func.HttpRequest) -> func.HttpResponse:
    return _handle(req, lambda s, b: s.pii_restore_copy(b["fileUrl"]))
