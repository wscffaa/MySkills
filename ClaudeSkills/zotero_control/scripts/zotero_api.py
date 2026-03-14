#!/usr/bin/env python3
"""
Zotero Web API v3 client - standalone replacement for zotero-mcp-server.
Calls Zotero REST API directly via urllib (no dependencies).

Usage:
  python3 zotero_api.py <command> [options]

Configuration:
  Reads from config.json in the skill root directory (~/.claude/skills/zotero_control/config.json).
  Environment variables override config.json values.

Commands:
  search    Search items (--query, --item-type, --tag, --collection, --sort, --direction, --limit)
  get       Get single item (--key or --doi)
  cite      Generate citation (--keys, --style, --format)
  fulltext  Get PDF full-text (--key, --start-page, --end-page)
  create    Create item (--json with item data)
  update    Update item (--key, --version, --json with field updates)
  delete    Delete items (--keys comma-separated)
  collections  Manage collections (--action list|get|create|delete, --key, --name, --parent)
  tags      Manage tags (--action list|add|remove, --key, --tags)
  keyinfo   Show API key info and permissions
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from typing import Any


def _load_config() -> dict:
    """Load config from config.json, env vars take precedence."""
    config_path = Path(__file__).resolve().parent.parent / "config.json"
    file_cfg = {}
    if config_path.exists():
        with open(config_path) as f:
            file_cfg = json.load(f)
    return {
        "base_url": os.environ.get("ZOTERO_BASE_URL", file_cfg.get("ZOTERO_BASE_URL", "https://api.zotero.org")),
        "api_key": os.environ.get("ZOTERO_API_KEY", file_cfg.get("ZOTERO_API_KEY", "")),
        "user_id": os.environ.get("ZOTERO_USER_ID", file_cfg.get("ZOTERO_USER_ID", "")),
        "group_id": os.environ.get("ZOTERO_GROUP_ID", file_cfg.get("ZOTERO_GROUP_ID", "")),
    }


_CFG = _load_config()
BASE_URL = _CFG["base_url"]
API_KEY = _CFG["api_key"]
USER_ID = _CFG["user_id"]
GROUP_ID = _CFG["group_id"]
MAX_RETRIES = 3


def library_prefix() -> str:
    if USER_ID:
        return f"/users/{USER_ID}"
    if GROUP_ID:
        return f"/groups/{GROUP_ID}"
    die("Set ZOTERO_USER_ID or ZOTERO_GROUP_ID")


def die(msg: str):
    print(json.dumps({"error": msg}), file=sys.stderr)
    sys.exit(1)


def api_request(method: str, path: str, data: Any = None,
                params: dict = None, headers: dict = None,
                raw_response: bool = False) -> Any:
    """Make an authenticated Zotero API request with retry logic."""
    if not API_KEY:
        die("ZOTERO_API_KEY not set")

    url = BASE_URL + path
    if params:
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            url += "?" + urllib.parse.urlencode(filtered, doseq=True)

    hdrs = {
        "Zotero-API-Key": API_KEY,
        "Content-Type": "application/json",
    }
    if headers:
        hdrs.update(headers)

    body = json.dumps(data).encode() if data is not None else None

    for attempt in range(MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
            with urllib.request.urlopen(req, timeout=30) as resp:
                text = resp.read().decode("utf-8")
                if raw_response:
                    return text
                if not text.strip():
                    return {"status": resp.status}
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return {"raw": text}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace") if e.fp else ""
            if e.code == 429 and attempt < MAX_RETRIES:
                retry_after = e.headers.get("Retry-After", str(5 * (2 ** attempt)))
                time.sleep(int(retry_after))
                continue
            if e.code >= 500 and attempt < MAX_RETRIES:
                time.sleep(1 * (attempt + 1))
                continue
            return {"error": f"HTTP {e.code}: {e.reason}", "detail": err_body}
        except Exception as e:
            if attempt < MAX_RETRIES:
                time.sleep(1)
                continue
            return {"error": str(e)}


def cmd_search(args):
    params = {
        "format": "json",
        "q": args.get("query"),
        "qmode": args.get("qmode"),
        "itemType": args.get("item_type"),
        "collection": args.get("collection"),
        "limit": args.get("limit", 25),
        "sort": args.get("sort", "dateModified"),
        "direction": args.get("direction", "desc"),
        "start": args.get("start"),
    }
    tags = args.get("tag")
    if tags:
        params["tag"] = tags if isinstance(tags, list) else [tags]

    result = api_request("GET", library_prefix() + "/items", params=params)
    if isinstance(result, list):
        items = [{
            "key": it.get("key"),
            "version": it.get("version"),
            "itemType": it.get("data", {}).get("itemType"),
            "title": it.get("data", {}).get("title"),
            "creators": it.get("data", {}).get("creators"),
            "date": it.get("data", {}).get("date"),
            "DOI": it.get("data", {}).get("DOI"),
            "url": it.get("data", {}).get("url"),
            "tags": it.get("data", {}).get("tags"),
            "abstractNote": it.get("data", {}).get("abstractNote"),
            "collections": it.get("data", {}).get("collections"),
        } for it in result]
        return {"count": len(items), "items": items}
    return result


def cmd_get(args):
    key = args.get("key")
    doi = args.get("doi")
    if key:
        return api_request("GET", library_prefix() + f"/items/{key}", params={"format": "json"})
    if doi:
        result = api_request("GET", library_prefix() + "/items", params={"format": "json", "q": doi})
        if isinstance(result, list):
            for item in result:
                if item.get("data", {}).get("DOI") == doi:
                    return item
            return {"error": f"No item found with DOI: {doi}"}
        return result
    return {"error": "Provide --key or --doi"}


def cmd_cite(args):
    keys = args.get("keys", "")
    style = args.get("style", "apa")
    fmt = args.get("format", "text")
    params = {
        "itemKey": keys,
        "format": "bib",
        "style": style,
        "linkwrap": "1" if fmt == "html" else "0",
    }
    return api_request("GET", library_prefix() + "/items", params=params, raw_response=True)


def cmd_fulltext(args):
    key = args.get("key")
    if not key:
        return {"error": "Provide --key"}
    result = api_request("GET", library_prefix() + f"/items/{key}/fulltext")
    if isinstance(result, dict) and "error" not in result:
        start = args.get("start_page")
        end = args.get("end_page")
        if start or end:
            content = result.get("content", "")
            lines = content.split("\n")
            total = result.get("totalPages", 1)
            if total > 0:
                lpp = max(1, len(lines) // total)
                s = ((int(start) - 1) * lpp) if start else 0
                e = (int(end) * lpp) if end else len(lines)
                result["content"] = "\n".join(lines[s:e])
                result["extractedPages"] = f"{start or 1}-{end or total}"
    return result


def cmd_create(args):
    data = args.get("json")
    if not data:
        return {"error": "Provide --json with item data"}
    if isinstance(data, str):
        data = json.loads(data)
    # Get template first
    item_type = data.get("itemType", "journalArticle")
    template = api_request("GET", f"/items/new", params={"itemType": item_type})
    if isinstance(template, dict) and "error" not in template:
        # Handle tags format
        tags = data.pop("tags", [])
        if tags and isinstance(tags[0], str):
            tags = [{"tag": t, "type": 1} for t in tags]
        merged = {**template, **data, "tags": tags}
        return api_request("POST", library_prefix() + "/items", data=[merged])
    return template


def cmd_update(args):
    key = args.get("key")
    version = args.get("version")
    data = args.get("json")
    if not all([key, version, data]):
        return {"error": "Provide --key, --version, --json"}
    if isinstance(data, str):
        data = json.loads(data)
    return api_request("PATCH", library_prefix() + f"/items/{key}",
                       data=data, headers={"If-Unmodified-Since-Version": str(version)})


def cmd_delete(args):
    keys = args.get("keys", "")
    key_list = [k.strip() for k in keys.split(",") if k.strip()]
    if not key_list:
        return {"error": "Provide --keys (comma-separated)"}
    if len(key_list) > 50:
        return {"error": "Max 50 items per delete request"}
    # Get version from first item to use for delete
    first = api_request("GET", library_prefix() + f"/items/{key_list[0]}", params={"format": "json"})
    ver = str(first.get("version", 0)) if isinstance(first, dict) and "version" in first else "0"
    return api_request("DELETE", library_prefix() + "/items",
                       params={"itemKey": ",".join(key_list)},
                       headers={"If-Unmodified-Since-Version": ver})


def cmd_collections(args):
    action = args.get("action", "list")
    if action == "list":
        return api_request("GET", library_prefix() + "/collections", params={"format": "json"})
    elif action == "get":
        key = args.get("key")
        return api_request("GET", library_prefix() + f"/collections/{key}", params={"format": "json"})
    elif action == "create":
        name = args.get("name")
        parent = args.get("parent")
        data = [{"name": name}]
        if parent:
            data[0]["parentCollection"] = parent
        return api_request("POST", library_prefix() + "/collections", data=data)
    elif action == "delete":
        key = args.get("key")
        # Get collection version first
        col = api_request("GET", library_prefix() + f"/collections/{key}", params={"format": "json"})
        ver = str(col.get("version", 0)) if isinstance(col, dict) and "version" in col else "0"
        return api_request("DELETE", library_prefix() + f"/collections/{key}",
                          headers={"If-Unmodified-Since-Version": ver})
    return {"error": f"Unknown action: {action}"}


def cmd_tags(args):
    action = args.get("action", "list")
    if action == "list":
        return api_request("GET", library_prefix() + "/tags", params={"format": "json"})
    elif action in ("add", "remove"):
        key = args.get("key")
        tags_input = args.get("tags", [])
        if isinstance(tags_input, str):
            tags_input = [t.strip() for t in tags_input.split(",")]
        # Retry on version conflict (412) since item may have just been updated
        for attempt in range(3):
            item = api_request("GET", library_prefix() + f"/items/{key}", params={"format": "json"})
            if isinstance(item, dict) and "error" in item:
                return item
            current_tags = item.get("data", {}).get("tags", [])
            version = item.get("version")
            if action == "add":
                new_tags = current_tags + [{"tag": t, "type": 1} for t in tags_input]
            else:
                new_tags = [t for t in current_tags if t.get("tag") not in tags_input]
            result = api_request("PATCH", library_prefix() + f"/items/{key}",
                                data={"tags": new_tags},
                                headers={"If-Unmodified-Since-Version": str(version)})
            if isinstance(result, dict) and "error" in result and "412" in str(result.get("error", "")):
                time.sleep(0.5)
                continue
            return result
        return {"error": "Version conflict after 3 retries"}
    return {"error": f"Unknown action: {action}"}


def cmd_keyinfo(args):
    return api_request("GET", f"/keys/{API_KEY}")


def parse_args(argv):
    """Minimal argument parser - no external deps needed."""
    if len(argv) < 2:
        print(__doc__)
        sys.exit(0)
    cmd = argv[1]
    args = {}
    i = 2
    while i < len(argv):
        if argv[i].startswith("--"):
            key = argv[i][2:].replace("-", "_")
            if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                args[key] = argv[i + 1]
                i += 2
            else:
                args[key] = True
                i += 1
        else:
            i += 1
    return cmd, args


def main():
    cmd, args = parse_args(sys.argv)
    commands = {
        "search": cmd_search,
        "get": cmd_get,
        "cite": cmd_cite,
        "fulltext": cmd_fulltext,
        "create": cmd_create,
        "update": cmd_update,
        "delete": cmd_delete,
        "collections": cmd_collections,
        "tags": cmd_tags,
        "keyinfo": cmd_keyinfo,
    }
    fn = commands.get(cmd)
    if not fn:
        die(f"Unknown command: {cmd}. Available: {', '.join(commands)}")
    result = fn(args)
    if isinstance(result, str):
        print(result)
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
