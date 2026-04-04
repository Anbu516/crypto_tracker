async def calculate_rsi(prices: list[float], period: int = 14):
    if len(prices) < period:
        return None

    gains = []
    losses = []
    for i in range(1, len(prices)):
        change = prices[i] - prices[i - 1]
        gains.append(max(change, 0))
        losses.append(abs(min(change, 0)))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def get_signal(rsi_value: float):
    if rsi_value >= 70:
        return "SELL (Overbought)"
    if rsi_value <= 30:
        return "BUY (Oversold)"
    return "HOLD"
