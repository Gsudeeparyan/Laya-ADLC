"""Where PII vaults live on the server, so real values never travel to Copilot.

A vault is kept per person and per file. In Azure it is stored in Table Storage (encrypted
at rest, reachable only by the Function's managed identity); in tests it lives in memory.
"""

from __future__ import annotations

import json
import os
import time

from adlc_pii import Vault

TTL_SECONDS = int(os.environ.get("VAULT_TTL_SECONDS", str(14 * 24 * 3600)))


class InMemoryVaultStore:
    def __init__(self):
        self._data: dict[tuple[str, str], tuple[float, str]] = {}

    def get(self, user: str, file_key: str) -> Vault:
        hit = self._data.get((user, file_key))
        if not hit or time.time() - hit[0] > TTL_SECONDS:
            return Vault(file_key)
        return Vault.from_dict(json.loads(hit[1]))

    def put(self, user: str, file_key: str, vault: Vault) -> None:
        self._data[(user, file_key)] = (time.time(), json.dumps(vault.to_dict(), ensure_ascii=False))


class TableVaultStore:
    """Azure Table Storage. Needs azure-data-tables and the VAULT_TABLE_URL setting."""

    def __init__(self, table_url: str | None = None):
        from azure.data.tables import TableClient
        from azure.identity import DefaultAzureCredential

        self.client = TableClient.from_table_url(table_url or os.environ["VAULT_TABLE_URL"], credential=DefaultAzureCredential())

    @staticmethod
    def _keys(user: str, file_key: str):
        safe = lambda s: "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in s)[:500]  # noqa: E731
        return safe(user), safe(file_key)

    def get(self, user: str, file_key: str) -> Vault:
        pk, rk = self._keys(user, file_key)
        try:
            entity = self.client.get_entity(pk, rk)
        except Exception:
            return Vault(file_key)
        if time.time() - float(entity.get("saved", 0)) > TTL_SECONDS:
            return Vault(file_key)
        chunks = [entity[k] for k in sorted(k for k in entity if k.startswith("part"))]
        return Vault.from_dict(json.loads("".join(chunks)))

    def put(self, user: str, file_key: str, vault: Vault) -> None:
        pk, rk = self._keys(user, file_key)
        text = json.dumps(vault.to_dict(), ensure_ascii=False)
        parts = {f"part{i:03d}": text[i * 30000:(i + 1) * 30000] for i in range((len(text) // 30000) + 1)}
        self.client.upsert_entity({"PartitionKey": pk, "RowKey": rk, "saved": str(time.time()), **parts})
