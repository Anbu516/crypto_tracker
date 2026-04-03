from ..crypto_service.market_service import MarketService


async def get_portfolio_valuation(db_items):
    """
    db_items: A list of portfolio objects from your database
    Example: [Portfolio(coin_id="bitcoin", quantity=0.5), Portfolio(coin_id="ethereum", quantity=2)]
    """
    market = MarketService()

    # 1. Get unique coin IDs from the database results
    coin_ids = [item.coin_id for item in db_items]

    # 2. Fetch the live prices
    live_prices = await market.get_live_prices(coin_ids)

    # 3. Calculate valuation
    portfolio_details = []
    total_value = 0

    for item in db_items:
        price = live_prices.get(item.coin_id, 0)
        value = item.quantity * price
        total_value += value

        portfolio_details.append(
            {
                "coin_id": item.coin_id,
                "quantity": item.quantity,
                "current_price": price,
                "total_value": value,
            }
        )

    return {"total_portfolio_value_usd": total_value, "assets": portfolio_details}
