from fastapi import APIRouter, HTTPException, status, Depends
from ..database import session_object, Users, Portfolio
from ..oauth2 import get_current_user
from ..models import PortfolioCreate, PortfolioResponse
from ..crypto_service import portfolio_service
from sqlalchemy import select
from ..redis_config import redis_client
import random
from ..crypto_service.market_service import market_service1
from ..crypto_service.analysis_service import calculate_rsi, get_signal

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
    total_cost_basis = 0
    detailed_assets = []

    for asset in user_assets:
        current_price = live_prices.get(asset.coin_id, 0)
        item_value = asset.quantity * current_price

        cost_basis = asset.quantity * asset.buy_price
        pnl_usd = item_value - cost_basis
        pnl_percent = (pnl_usd / cost_basis * 100) if cost_basis > 0 else 0

        # RSI Logic (Check Redis first to avoid heavy API calls)
        rsi_cache_key = f"rsi:{asset.coin_id}"
        cached_rsi = await redis_client.get(rsi_cache_key)

        if cached_rsi:
            rsi_value = float(cached_rsi)
        else:
            historical_prices = await market_service1.get_historical_prices(
                asset.coin_id
            )
            rsi_value = await calculate_rsi(historical_prices)
            if rsi_value is not None:
                # Cache RSI for 1 hour
                await redis_client.setex(rsi_cache_key, 3600, str(rsi_value))

        total_portfolio_value += item_value
        total_cost_basis += cost_basis

        detailed_assets.append(
            {
                "coin_id": asset.coin_id,
                "symbol": asset.symbol,
                "quantity": asset.quantity,
                "current_price": current_price,
                "buy_price_avg": asset.buy_price,
                "value_usd": round(item_value, 2),
                "pnl_usd": round(pnl_usd, 2),
                "pnl_percent": round(pnl_percent, 2),
                "rsi": round(rsi_value, 2) if rsi_value else None,
                "signal": get_signal(rsi_value) if rsi_value else "WAITING FOR DATA",
            }
        )

    # 4. Final Aggregation
    total_pnl_usd = total_portfolio_value - total_cost_basis
    total_pnl_percent = (
        (total_pnl_usd / total_cost_basis * 100) if total_cost_basis > 0 else 0
    )

    return {
        "summary": {
            "total_value_usd": round(total_portfolio_value, 2),
            "total_pnl_usd": round(total_pnl_usd, 2),
            "total_pnl_percent": round(total_pnl_percent, 2),
            "asset_count": len(user_assets),
        },
        "assets": detailed_assets,
    }
