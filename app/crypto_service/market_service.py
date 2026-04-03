import httpx
import logging
import json
import time
from ..config import settings

logger = logging.getLogger("Crypto_api")


class MarketService:
    BASE_URL = settings.base_url
    API_KEY = settings.api_key

    _failure_count = 0
    _last_failure_time = 0
    _MAX_FAILURES = 5
    _RECOVERY_TIME = 60

    async def get_live_prices(self, coin_ids: list[str]) -> dict:
        if not coin_ids:
            return {}

        # --- 1. CHECK CIRCUIT STATE ---
        if self._failure_count >= self._MAX_FAILURES:
            if time.time() - self._last_failure_time < self._RECOVERY_TIME:
                logger.warning(
                    json.dumps(
                        {
                            "event": "circuit_breaker_open",
                            "message": "Skipping API call",
                            "remaining_recovery": round(
                                self._RECOVERY_TIME
                                - (time.time() - self._last_failure_time)
                            ),
                        }
                    )
                )
                return {}
            else:
                # Entering "Half-Open" state (trying one request)
                logger.info(
                    json.dumps(
                        {
                            "event": "circuit_breaker_half_open",
                            "message": "Testing API recovery",
                        }
                    )
                )

        logger.info(
            json.dumps(
                {
                    "event": "external_api_start",
                    "provider": "coingecko",
                    "coins": coin_ids,
                }
            )
        )

        ids_param = ",".join(coin_ids)
        url = f"{self.BASE_URL}/simple/price?ids={ids_param}&vs_currencies=usd"
        headers = {"x-cg-demo-api-key": self.API_KEY}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()

                # --- 2. SUCCESS: RESET EVERYTHING ---
                self._failure_count = 0

                data = response.json()
                logger.info(
                    json.dumps(
                        {"event": "external_api_success", "provider": "coingecko"}
                    )
                )
                return {coin: info["usd"] for coin, info in data.items()}

            except Exception as e:
                # --- 3. FAILURE: INCREMENT AND TIMESTAMP ---
                self._failure_count += 1
                self._last_failure_time = time.time()

                logger.error(
                    json.dumps(
                        {
                            "event": "external_api_error",
                            "failure_count": self._failure_count,
                            "error": str(e),
                        }
                    )
                )
                return {}

    async def validate_coin_id(self, coin_id: str) -> bool:

        url = f"{self.BASE_URL}/simple/price?ids={coin_id}&vs_currencies=usd"
        headers = {"x-cg-demo-api-key": self.API_KEY}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers)
                data = response.json()
                return coin_id.lower() in data
            except Exception:
                return False
