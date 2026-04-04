from fastapi import APIRouter, HTTPException, status, Depends
from ..database import session_object, Users, Portfolio
from ..oauth2 import get_current_user
from ..models import PortfolioCreate, PortfolioResponse
from ..crypto_service import portfolio_service
from sqlalchemy import select
from ..redis_config import redis_client
import random
from ..crypto_service.market_service import market_service1

router = APIRouter(prefix="/api/v1/portfolio", tags=["Portfolio"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=PortfolioResponse)
async def add_asset(
    coin: PortfolioCreate,
    session: session_object,
    current_user: Users = Depends(get_current_user),
):
    return await portfolio_service.add_coin_to_portfolio(session, current_user.id, coin)


@router.get("/", status_code=status.HTTP_200_OK, response_model=list[PortfolioResponse])
async def list_assest(
    session: session_object, current_user: Users = Depends(get_current_user)
):
    return await portfolio_service.get_user_portfolio(current_user.id, session)


@router.get("/total/", status_code=status.HTTP_200_OK)
async def total_value(
    db: session_object, current_user: Users = Depends(get_current_user)
):

    stmt = (
        select(Portfolio).where(Portfolio.user_id == current_user.id).with_for_update()
    )
    result = await db.execute(stmt)
    user_assets = result.scalars().all()

    if not user_assets:
        return {"message": "Portfolio is empty", "total_usd": 0, "assets": []}

    coin_ids = [asset.coin_id for asset in user_assets]
    cache_keys = [f"price:{cid}" for cid in coin_ids]

    cached_values = await redis_client.mget(*cache_keys)
    live_prices = {cid: float(val) for cid, val in zip(coin_ids, cached_values) if val}

    missing_ids = [cid for cid in coin_ids if cid not in live_prices]

    if missing_ids:
        fresh_prices = await market_service1.get_live_prices(missing_ids)

        for cid, price in fresh_prices.items():
            live_prices[cid] = price
            await redis_client.setex(
                f"price:{cid}", 60 + random.randint(0, 10), str(price)
            )

    total_portfolio_value = 0
    detailed_assets = []

    for asset in user_assets:
        current_price = live_prices.get(asset.coin_id, 0)
        item_value = asset.quantity * current_price

        total_portfolio_value += item_value

        detailed_assets.append(
            {
                "coin_id": asset.coin_id,
                "quantity": asset.quantity,
                "current_price": current_price,
                "value_usd": round(item_value, 2),
            }
        )

    return {
        "user": current_user.name,
        "total_usd": round(total_portfolio_value, 2),
        "assets": detailed_assets,
    }
