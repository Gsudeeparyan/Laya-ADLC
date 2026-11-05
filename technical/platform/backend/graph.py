"""Minimal Microsoft Graph client for files in SharePoint / OneDrive (standard library only).

Acts on behalf of the signed-in person (on-behalf-of token), so it can only open files
that person can already open.
"""

from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

GRAPH = "https://graph.microsoft.com/v1.0"


class GraphError(RuntimeError):
    def __init__(self, status: int, message: str):
        self.status = status
        super().__init__(message)


class ConflictError(GraphError):
    pass


@dataclass
class DriveFile:
    drive_id: str
    item_id: str
    name: str
    etag: str
    parent_id: str
    web_url: str


def share_id(url: str) -> str:
    """Graph 'shares' id for a SharePoint/OneDrive link (sharing link or normal file URL)."""
    encoded = base64.urlsafe_b64encode(url.strip().encode("utf-8")).decode("ascii").rstrip("=")
    return "u!" + encoded


class GraphClient:
    def __init__(self, token: str):
        self.token = token

    def _request(self, method: str, path: str, data: bytes | None = None, headers: dict | None = None,
                 raw: bool = False):
        url = path if path.startswith("http") else GRAPH + path
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", f"Bearer {self.token}")
        for k, v in (headers or {}).items():
            req.add_header(k, v)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = resp.read()
                return body if raw else (json.loads(body) if body else {})
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:300]
            if exc.code == 412:
                raise ConflictError(412, "The file was changed by someone else since I read it. Nothing was saved - please ask again.") from None
            if exc.code in (401, 403):
                raise GraphError(exc.code, "You don't have permission to that file, or your sign-in has expired.") from None
            if exc.code == 404:
                raise GraphError(404, "I can't find that file. Check the link, or that it hasn't been moved or renamed.") from None
            if exc.code == 423:
                raise GraphError(423, "The file is locked (checked out or open exclusively). Close it or check it in, then try again.") from None
            raise GraphError(exc.code, f"SharePoint returned an error ({exc.code}): {detail}") from None

    def resolve(self, file_url: str) -> DriveFile:
        item = self._request("GET", f"/shares/{share_id(file_url)}/driveItem?$select=id,name,eTag,parentReference,webUrl")
        return DriveFile(
            drive_id=item["parentReference"]["driveId"], item_id=item["id"], name=item["name"],
            etag=item.get("eTag", ""), parent_id=item["parentReference"].get("id", ""), web_url=item.get("webUrl", file_url),
        )

    def download(self, f: DriveFile) -> bytes:
        return self._request("GET", f"/drives/{f.drive_id}/items/{f.item_id}/content", raw=True)

    def upload(self, f: DriveFile, content: bytes) -> DriveFile:
        """Replace the file's content only if nobody changed it since we read it (If-Match)."""
        item = self._request("PUT", f"/drives/{f.drive_id}/items/{f.item_id}/content", data=content,
                             headers={"If-Match": f.etag, "Content-Type": "application/octet-stream"})
        return DriveFile(f.drive_id, item["id"], item["name"], item.get("eTag", ""), f.parent_id, item.get("webUrl", f.web_url))

    def create_sibling(self, f: DriveFile, name: str, content: bytes) -> DriveFile:
        """Save a new file next to ``f`` (renamed automatically if the name is taken)."""
        path = f"/drives/{f.drive_id}/items/{f.parent_id}:/{urllib.parse.quote(name)}:/content?@microsoft.graph.conflictBehavior=rename"
        item = self._request("PUT", path, data=content, headers={"Content-Type": "application/octet-stream"})
        return DriveFile(f.drive_id, item["id"], item["name"], item.get("eTag", ""), f.parent_id, item.get("webUrl", ""))
