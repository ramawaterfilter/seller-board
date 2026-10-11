import asyncio

from fastapi import APIRouter, Request

from app.errors import error_response

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz", response_model=None)
async def readiness(request: Request):
    database = request.app.state.database
    redis = request.app.state.redis

    async def check(resource, probe):
        if resource is None:
            return "not_configured"
        try:
            async with asyncio.timeout(3):
                await probe()
            return "ok"
        except Exception:
            return "unavailable"

    postgres_status, redis_status = await asyncio.gather(
        check(database, database.ready if database else None),
        check(redis, redis.ping if redis else None),
    )
    dependencies = {"postgres": postgres_status, "redis": redis_status}
    if all(status == "ok" for status in dependencies.values()):
        return {"status": "ok", "dependencies": dependencies}
    code = "DEPENDENCIES_NOT_CONFIGURED" if "not_configured" in dependencies.values() \
        else "DEPENDENCIES_UNAVAILABLE"
    return error_response(request, 503, code, "Required dependencies are not ready.", dependencies)
