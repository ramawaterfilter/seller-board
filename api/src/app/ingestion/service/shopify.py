import asyncio
import hashlib
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from uuid import uuid4

from app.errors import AppError
from app.ingestion.connectors.shopify import queries
from app.ingestion.connectors.shopify.client import ShopifyClient
from app.ingestion.service.credentials import load_credentials
from app.platform.audit import append_audit
from app.workspace.service.rbac import permitted
from sqlalchemy import bindparam, text
from sqlalchemy.dialects.postgresql import JSONB

FIELDS = {
    "product": ("id", "title", "status", "updatedAt"),
    "variant": ("id", "sku", "title", "updatedAt"),
    "inventory_item": ("id", "sku", "tracked", "updatedAt"),
    "inventory_level": ("id",),
    "order": (
        "id",
        "createdAt",
        "updatedAt",
        "cancelledAt",
        "displayFinancialStatus",
        "displayFulfillmentStatus",
    ),
    "order_line": ("id", "sku", "quantity"),
}


def safe_record(kind: str, node: dict, parent_id: str | None = None) -> dict:
    """Explicit allow-list at raw-write; never persist an unexpected provider field."""
    result = {key: node.get(key) for key in FIELDS[kind]}
    if not isinstance(result["id"], str):
        raise AppError(502, "SHOPIFY_RESPONSE_INVALID", "A Shopify record has no identifier.")
    for field in ("product", "inventoryItem", "variant"):
        if field in node and node[field] is not None:
            result[field] = {"id": node[field]["id"]}
    for field in (
        "currentTotalPriceSet",
        "totalRefundedSet",
        "originalUnitPriceSet",
        "discountedTotalSet",
    ):
        if field in node:
            money = node[field]["shopMoney"]
            try:
                amount = Decimal(money["amount"])
                if (
                    not amount.is_finite()
                    or amount.as_tuple().exponent < -4
                    or abs(amount) >= Decimal("1e14")
                ):
                    raise ValueError("unsupported precision")
                currency = money["currencyCode"]
                if not isinstance(currency, str) or len(currency) != 3 or not currency.isalpha():
                    raise ValueError("invalid currency")
                result[field] = {
                    "shopMoney": {"amount": format(amount, ".4f"), "currencyCode": currency}
                }
            except (InvalidOperation, ValueError, TypeError, KeyError):
                raise AppError(
                    502, "SHOPIFY_MONEY_INVALID", "Shopify returned an invalid amount or currency."
                ) from None
    if kind == "inventory_level":
        result["location"] = {"id": node["location"]["id"], "name": node["location"]["name"]}
        result["quantities"] = [
            {"name": q["name"], "quantity": q["quantity"]} for q in node["quantities"]
        ]
    if parent_id:
        result["parent_id"] = parent_id
    return result


async def authorize(session, workspace, user, country, *, write=False):
    if not await permitted(
        session, user, workspace, "connectors.manage", "*", f"country:{country}"
    ):
        raise AppError(404, "NOT_FOUND", "Connection was not found.")
    if write:
        demo = (
            await session.execute(
                text("SELECT demo_mode FROM ws.workspace WHERE id=:ws"), {"ws": workspace}
            )
        ).scalar_one()
        if demo:
            raise AppError(
                403,
                "DEMO_READ_ONLY",
                "Demo workspaces are read only. Use a local integration workspace.",
            )


async def connection(session, workspace, user, connector_id, *, write=False, lock=False):
    row = (
        (
            await session.execute(
                text(
                    "SELECT * FROM ing.connector WHERE id=:id AND workspace_id=:ws"
                    + (" FOR UPDATE" if lock else "")
                ),
                {"id": connector_id, "ws": workspace},
            )
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        raise AppError(404, "NOT_FOUND", "Connection was not found.")
    await authorize(session, workspace, user, row["config"]["country"], write=write)
    return dict(row)


def public_connection(row):
    config = row["config"]
    return {
        "id": row["id"],
        "shop_domain": config["shop_domain"],
        "country": config["country"],
        "auth_mode": config["auth_mode"],
        "status": row["status"],
        "api_version": row["api_version"],
        "shop_name": config.get("shop_name"),
        "currency": config.get("currency"),
        "timezone": config.get("timezone"),
        "scopes": config.get("scopes", []),
        "last_success_at": row["last_success_at"],
        "last_error": row["last_error"],
        "revision": row["revision"],
    }


async def probe(settings, connector):
    client = ShopifyClient(
        connector["config"]["shop_domain"],
        load_credentials(settings, connector),
        connector["api_version"],
    )
    shop, scopes = await client.probe()
    # Store identity/region is verified before any records are imported.
    if shop["billingAddress"]["countryCodeV2"] != connector["config"]["country"]:
        raise AppError(
            403,
            "SHOPIFY_COUNTRY_MISMATCH",
            "Store country does not match this connection's permission scope.",
        )
    return client, {
        "shop_name": shop["name"],
        "currency": shop["currencyCode"],
        "timezone": shop["ianaTimezone"],
        "scopes": scopes,
    }


async def update_config(session, workspace, connector_id, config):
    await session.execute(
        text("""
        UPDATE ing.connector SET config=:config,status='connected',last_error=NULL,
          revoked_at=NULL,updated_at=now(),revision=revision+1 WHERE id=:id AND workspace_id=:ws
    """).bindparams(bindparam("config", type_=JSONB)),
        {"config": config, "id": connector_id, "ws": workspace},
    )


async def record_page(
    database,
    workspace,
    user,
    connector_id,
    kind,
    nodes,
    job_id,
    parent_id=None,
    source_version=None,
):
    async with database.transaction(workspace) as session:
        row = await connection(session, workspace, user, connector_id, write=True)
        if row["status"] != "connected" or row["kill_switch"]:
            raise AppError(409, "CONNECTOR_PAUSED", "Connection is not active.")
        inserted = 0
        for node in nodes:
            body = safe_record(kind, node, parent_id)
            content = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            digest = hashlib.sha256(content.encode()).hexdigest()
            version = source_version or body.get("updatedAt") or body.get("createdAt")
            idem = hashlib.sha256(
                f"{connector_id}:{kind}:{body['id']}:{version}:{digest}".encode()
            ).hexdigest()
            raw_id, now = uuid4(), datetime.now(UTC)
            claimed = (
                await session.execute(
                    text("""
                INSERT INTO ing.raw_receipt(workspace_id,connector_id,idempotency_key,
                  raw_id,received_at)
                VALUES (:ws,:connector,:idem,:raw,:now) ON CONFLICT DO NOTHING RETURNING raw_id
            """),
                    {
                        "ws": workspace,
                        "connector": connector_id,
                        "idem": idem,
                        "raw": raw_id,
                        "now": now,
                    },
                )
            ).scalar_one_or_none()
            if claimed is None:
                continue
            stamp = body.get("updatedAt") or body.get("createdAt")
            source_ts = datetime.fromisoformat(stamp.replace("Z", "+00:00")) if stamp else None
            if source_ts and source_ts.utcoffset() is None:
                raise AppError(
                    502, "SHOPIFY_RESPONSE_INVALID", "Shopify timestamp has no timezone."
                )
            await session.execute(
                text("""
                INSERT INTO ing.raw_payload(id,workspace_id,connector_id,object_type,external_id,
                  external_version,idempotency_key,received_at,source_ts,content_hash,body)
                VALUES (:raw,:ws,:connector,:kind,:external,:version,:idem,:now,:stamp,:hash,:body)
            """).bindparams(bindparam("body", type_=JSONB)),
                {
                    "raw": raw_id,
                    "ws": workspace,
                    "connector": connector_id,
                    "kind": kind,
                    "external": body["id"],
                    "version": version,
                    "idem": idem,
                    "now": now,
                    "stamp": source_ts,
                    "hash": digest,
                    "body": body,
                },
            )
            inserted += 1
        await session.execute(
            text("""UPDATE ing.sync_job SET produced_raw_count=produced_raw_count+:n,
          params=jsonb_build_object('stream',CAST(:stream AS text))
          WHERE id=:id AND workspace_id=:ws"""),
            {"n": inserted, "stream": kind, "id": job_id, "ws": workspace},
        )


async def pages(client, operation, root, variables=None, parent=None):
    after = None
    for _ in range(2000):
        result = await client.query(operation, {**(variables or {}), "after": after})
        page = result[parent][root] if parent else result[root]
        yield page["nodes"]
        info = page["pageInfo"]
        if not info["hasNextPage"]:
            return
        if not info["endCursor"] or info["endCursor"] == after:
            raise AppError(502, "SHOPIFY_CURSOR_INVALID", "Shopify pagination did not advance.")
        after = info["endCursor"]
    raise AppError(
        409,
        "SHOPIFY_SYNC_LIMIT",
        "Store exceeded the manual sync limit. Use the future bulk worker.",
    )


async def run_sync(database, settings, workspace, user, connector_id, job_id, trace):
    error = None
    try:
        async with asyncio.timeout(600):
            async with database.transaction(workspace) as session:
                row = await connection(session, workspace, user, connector_id, write=True)
                await session.execute(
                    text("UPDATE ing.sync_job SET state='running',started_at=now() WHERE id=:id"),
                    {"id": job_id},
                )
            client, metadata = await probe(settings, row)
            async with database.transaction(workspace) as session:
                current = await connection(
                    session, workspace, user, connector_id, write=True, lock=True
                )
                if current["status"] in {"paused", "disconnected", "killed"}:
                    raise AppError(409, "CONNECTOR_PAUSED", "Connection is not active.")
                await update_config(
                    session, workspace, connector_id, {**current["config"], **metadata}
                )
            for kind, operation, root in [
                ("product", queries.PRODUCTS, "products"),
                ("variant", queries.VARIANTS, "productVariants"),
                ("inventory_item", queries.INVENTORY, "inventoryItems"),
            ]:
                async for nodes in pages(client, operation, root):
                    await record_page(database, workspace, user, connector_id, kind, nodes, job_id)
                    if kind == "inventory_item":
                        for node in nodes:
                            async for levels in pages(
                                client,
                                queries.LEVELS,
                                "inventoryLevels",
                                {"id": node["id"]},
                                "inventoryItem",
                            ):
                                await record_page(
                                    database,
                                    workspace,
                                    user,
                                    connector_id,
                                    "inventory_level",
                                    levels,
                                    job_id,
                                    node["id"],
                                    source_version=str(job_id),
                                )
            since = (datetime.now(UTC) - timedelta(days=60)).date().isoformat()
            async for nodes in pages(
                client, queries.ORDERS, "orders", {"query": f"created_at:>={since}"}
            ):
                await record_page(database, workspace, user, connector_id, "order", nodes, job_id)
                for node in nodes:
                    async for lines in pages(
                        client, queries.LINES, "lineItems", {"id": node["id"]}, "order"
                    ):
                        await record_page(
                            database,
                            workspace,
                            user,
                            connector_id,
                            "order_line",
                            lines,
                            job_id,
                            node["id"],
                            source_version=node["updatedAt"],
                        )
    except AppError as exc:
        error = exc.code
    except (TimeoutError, asyncio.CancelledError):
        error = "SYNC_INTERRUPTED"
    except Exception:
        # Provider bodies/errors may contain sensitive values; never persist or log them.
        error = "SHOPIFY_SYNC_FAILED"
    async with database.transaction(workspace) as session:
        await session.execute(
            text("""UPDATE ing.sync_job SET state=:state,finished_at=now(),error_code=:err
          WHERE id=:id AND workspace_id=:ws"""),
            {
                "state": "failed" if error else "succeeded",
                "err": error,
                "id": job_id,
                "ws": workspace,
            },
        )
        if error:
            await session.execute(
                text("""UPDATE ing.connector SET last_error_at=now(),last_error=:err,
              status=CASE WHEN :err='CONNECTOR_REVOKED' THEN 'revoked' ELSE status END,
              revoked_at=CASE WHEN :err='CONNECTOR_REVOKED' THEN now() ELSE revoked_at END,
              updated_at=now() WHERE id=:id AND workspace_id=:ws"""),
                {"err": error, "id": connector_id, "ws": workspace},
            )
        else:
            await session.execute(
                text("""UPDATE ing.connector SET last_success_at=now(),last_error=NULL,
              updated_at=now() WHERE id=:id AND workspace_id=:ws AND status='connected'"""),
                {"id": connector_id, "ws": workspace},
            )
        await append_audit(
            session,
            workspace_id=workspace,
            actor_user_id=user,
            action="shopify.sync_failed" if error else "shopify.sync_succeeded",
            trace_id=trace,
            entity_type="connector",
            entity_id=str(connector_id),
            after={"job_id": str(job_id), "error_code": error},
        )
