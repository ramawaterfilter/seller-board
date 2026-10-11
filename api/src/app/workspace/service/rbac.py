from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def permitted(
    session: AsyncSession,
    user_id: UUID,
    workspace_id: UUID,
    function: str,
    product: str,
    market: str,
) -> bool:
    """Require all dimensions on the same unexpired grant, with an active identity."""
    result = await session.execute(
        text("""
        SELECT EXISTS (
          SELECT 1 FROM ws.permission_scope p JOIN ws."user" u ON u.id = p.user_id
          WHERE p.user_id = :user AND p.workspace_id = :workspace AND u.status = 'active'
            AND p.function_code IN ('*', :function)
            AND p.product_scope IN ('*', :product)
            AND p.market_scope IN ('*', :market)
            AND (p.expires_at IS NULL OR p.expires_at > now())
        )
    """),
        {
            "user": user_id,
            "workspace": workspace_id,
            "function": function,
            "product": product,
            "market": market,
        },
    )
    return bool(result.scalar_one())
