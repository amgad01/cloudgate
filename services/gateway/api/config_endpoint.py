from fastapi import APIRouter, Depends

from shared.config import GatewayConfig, get_gateway_config

router = APIRouter()


@router.get("/api/frontend-config")
async def get_frontend_config(
    config: GatewayConfig = Depends(get_gateway_config),
) -> dict[str, str | None]:
    return {
        "apiBaseUrl": config.api_base_url if hasattr(config, "api_base_url") else None,
        "environment": config.app_env,
    }
