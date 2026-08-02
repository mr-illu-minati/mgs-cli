"""OneDrive/SharePoint +verb helpers (upload, download)."""

from __future__ import annotations

import argparse
import os

from mgs.errors import UsageError
from mgs.executor import Opts
from mgs.helpers import files_build, registry
from mgs.userpath import resolve_user_path

_GRAPH = {"v1.0": "https://graph.microsoft.com/v1.0", "beta": "https://graph.microsoft.com/beta"}


def _base(beta: bool) -> str:
    return _GRAPH["beta"] if beta else _GRAPH["v1.0"]


class UploadHelper:
    name = "+upload"
    service = "driveItem"
    help = "Upload a file (auto small PUT or chunked upload session for >4 MB)"

    def add_arguments(self, p: argparse.ArgumentParser) -> None:
        p.add_argument("local", help="Local file to upload")
        p.add_argument("--to", help="Remote folder or path (default: drive root)")
        p.add_argument("--name", help="Rename on upload")
        p.add_argument("--chunk-mb", type=int, default=10, help="Chunk size for large uploads")
        p.add_argument("--dry-run", action="store_true")
        p.add_argument("--beta", action="store_true")

    def run(self, token: str, ns: argparse.Namespace, opts: Opts) -> object:
        try:
            size = os.path.getsize(ns.local)
        except OSError as e:
            raise UsageError(f"cannot read {ns.local!r}: {e}") from e
        remote = files_build.resolve_remote_path(ns.local, ns.to, ns.name)
        small = files_build.is_small(size)

        if opts.dry_run:
            if small:
                return {
                    "dryRun": True,
                    "mode": "small",
                    "method": "PUT",
                    "url": _base(opts.beta)
                    + resolve_user_path(files_build.upload_content_path(remote)),
                    "size": size,
                }
            chunk = files_build.normalize_chunk_size(ns.chunk_mb)
            return {
                "dryRun": True,
                "mode": "session",
                "method": "POST",
                "url": _base(opts.beta)
                + resolve_user_path(files_build.upload_session_path(remote)),
                "size": size,
                "chunks": len(files_build.compute_chunks(size, chunk)),
            }

        from mgs.helpers import httpio

        with open(ns.local, "rb") as f:
            data = f.read()

        if small:
            url = _base(opts.beta) + resolve_user_path(files_build.upload_content_path(remote))
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/octet-stream",
            }
            return httpio.put_bytes(url, data, headers)

        from mgs.client import GraphClient

        client = GraphClient(token, beta=opts.beta)
        session = client.request(
            "POST",
            client.full_url(files_build.upload_session_path(remote)),
            body=files_build.session_body(),
        )
        upload_url = session.get("uploadUrl") if isinstance(session, dict) else None
        if not upload_url:
            raise UsageError("failed to create upload session")
        chunk_size = files_build.normalize_chunk_size(ns.chunk_mb)
        result = None
        for start, end in files_build.compute_chunks(size, chunk_size):
            piece = data[start : end + 1]
            headers = {
                "Content-Length": str(len(piece)),
                "Content-Range": f"bytes {start}-{end}/{size}",
            }
            result = httpio.put_bytes(upload_url, piece, headers)
        return result


registry.register(UploadHelper())


# Note: `@microsoft.graph.downloadUrl` is a computed instance annotation that Graph OMITS
# when a `$select` is applied, so we resolve the item with a plain GET (no $select).


class DownloadHelper:
    name = "+download"
    service = "driveItem"
    help = "Download a drive item (by id or /path) to a local file"

    def add_arguments(self, p: argparse.ArgumentParser) -> None:
        p.add_argument("ref", help="Drive item id or /path")
        p.add_argument("--out", help="Local destination (default: the item's name)")
        p.add_argument("--dry-run", action="store_true")
        p.add_argument("--beta", action="store_true")

    def run(self, token: str, ns: argparse.Namespace, opts: Opts) -> object:
        from mgs.drivepath import drive_item_base

        base = resolve_user_path(drive_item_base(ns.ref))
        resolve_url = _base(opts.beta) + base
        if opts.dry_run:
            return {
                "dryRun": True,
                "method": "GET",
                "url": resolve_url,
                "out": ns.out or "(item name)",
            }

        from mgs.client import GraphClient
        from mgs.helpers import httpio

        client = GraphClient(token, beta=opts.beta)
        meta = client.request("GET", client.full_url(base))
        if not isinstance(meta, dict):
            raise UsageError("could not resolve drive item")
        name = meta.get("name")
        download_url = meta.get("@microsoft.graph.downloadUrl")
        if not download_url:
            raise UsageError("item has no download URL (is it a folder?)")
        dest = ns.out or name
        httpio.get_to_file(download_url, dest)
        return {"downloaded": dest, "name": name, "size": meta.get("size")}


registry.register(DownloadHelper())
