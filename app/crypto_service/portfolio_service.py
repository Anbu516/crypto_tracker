from sqlalchemy import select, delete
from ..database import Portfolio, Users, session_object
from ..models import PortfolioCreate
from fastapi import HTTPException, status
from .market_service import MarketService


async def add_coin_to_portfolio(
    session: session_object, user_id: int, coin_data: PortfolioCreate
):
    market = MarketService()

    is_valid = await market.validate_coin_id(coin_data.coin_id)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid coin_id: '{coin_data.coin_id}'. Please use the official CoinGecko slug (e.g., 'ethereum').",
        )

    statement = (
        select(Portfolio)
        .where(Portfolio.user_id == user_id, Portfolio.coin_id == coin_data.coin_id)
        .with_for_update()
    )
    result = await session.execute(statement)
    existing_item = result.scalars().first()

    if existing_item:
        old_total_cost = existing_item.quantity * existing_item.buy_price
        new_purchase_cost = coin_data.quantity * coin_data.buy_price

        new_quantity = existing_item.quantity + coin_data.quantity
        new_avg_price = (old_total_cost + new_purchase_cost) / new_quantity

        existing_item.quantity = new_quantity
        existing_item.buy_price = new_avg_price
        await session.commit()
        return existing_item

    new_item = Portfolio(**coin_data.model_dump(), user_id=user_id)
    session.add(new_item)
    await session.commit()
    await session.refresh(new_item)
    return new_item


async def get_user_portfolio(user_id: int, session: session_object):
    statement = select(Portfolio).where(Portfolio.user_id == user_id)
    result = await session.execute(statement)
    return result.scalars().all()
