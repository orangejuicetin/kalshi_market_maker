"""
Project TAJIR = means "trader/merchant" in Arabic, as "kalshi" means "everything". Market making strategy, naming this as inspiration from Nolen Royalty, S2 '23 :))
"""
import asyncio
import json
from pprint import pprint
import os
from collections import defaultdict
import uuid
import random
import websockets.exceptions
import websockets.client
import requests
from dotenv import load_dotenv

import pandas as pd

from datetime import datetime as dt, timezone

from KalshiClientsBaseV2 import ExchangeClient


async def spin_up_markets_trader(
    channels: list[str],
    desired_markets: list[str],
    exchange_client: ExchangeClient,
    expiry_datetime: dt,
    open_datetime: float,
    is_production: bool,
):
    """
    Listens in on the market feed websocket:
    https://trading-api.readme.io/reference/introduction#snapshot--deltas
    """
    api_base = (
        os.getenv("PROD_API_BASE") if is_production else os.getenv("DEMO_API_BASE")
    )
    email = os.getenv("PROD_EMAIL") if is_production else os.getenv("DEMO_EMAIL")
    pword = os.getenv("PROD_PASSWORD") if is_production else os.getenv("DEMO_PASSWORD")

    response = requests.post(
        api_base + "/login",
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        json={
            "email": email,
            "password": pword,
        },
        timeout=10,
    )

    token = response.json()["token"]

    uri = "wss://trading-api.kalshi.com/trade-api/ws/v2"
    unique_cmd_id = 1

    # using async iterator helps reconnect if connection drops
    async for websocket in websockets.client.connect(
        uri, extra_headers={"Authorization": "Bearer " + token}
    ):
        try:
            # Subscribe to the desired topics
            await websocket.send(
                json.dumps(
                    {
                        "id": unique_cmd_id,
                        "cmd": "subscribe",
                        "params": {
                            "channels": channels,
                            # "market_tickers": desired_markets,
                        },
                    }
                )
            )

            orders_for = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))

            unique_cmd_id += 1
            while True:
                try:
                    async for ws_msg in websocket:
                        payload = json.loads(ws_msg)
                        msg = payload["msg"]
                        pprint(msg)
                        if msg and payload["type"] != "subscribed":
                            mkt_ticker = msg["market_ticker"]
                            mkt_volume = msg["volume"]

                            # since this isn't given to us in the websocket, we have to calculate it ourselves for this market, mkt_volume / (time passed since open_datetime of market)
                            avg_daily_mkt_volume = mkt_volume / (
                                (dt.now(timezone.utc) - open_datetime).total_seconds()
                                / (60 * 60 * 24)
                            )

                            if payload["type"] == "fill":
				# track when our orders have been filled! and re-quote limit orders in response if need be
                            elif (
                                payload["type"] == "ticker"
                            ):  # will be sent whenever there is a new trade or the bid / ask values move
                                yes_midprice = (msg["yes_ask"] + msg["yes_bid"]) // 2
                                spread = msg["yes_ask"] - msg["yes_bid"]

                                balance = exchange_client.get_balance()["balance"]
                                # set up our EMERGENCY stop in case balance is below a certain amount
                                if balance < 1500:
                                    await websocket.close()
                                    print(
                                        f"closing {channels} data feed on {desired_markets[0] if desired_markets else 'all_markets'} because of insufficent funds at {balance / 100} dollars"
                                    )
                                    return

                                our_stake = balance * 0.05

                                count_bought = {}
                                if our_stake > avg_daily_mkt_volume:
                                    count_bought = {
                                        "yes": int(avg_daily_mkt_volume // our_yes_bid),
                                        "no": int(avg_daily_mkt_volume // our_no_bid),
                                    }

                                else:
                                    count_bought = {
                                        "yes": int(our_stake // our_yes_bid),
                                        "no": int(our_stake // our_no_bid),
                                    }
 			   	
				# Just some boilerplate logic on finding quantity that we'll be trading
				# From here, the fun part I've abstracted away is figuring out the strategy itself ;)))

                except websockets.exceptions.ConnectionClosedOK:
                    break
                except asyncio.exceptions.CancelledError:
                    await websocket.close()
                    # TODO: make sure that all your positions are closed out before returning
                    print(
                        f"closing {channels} data feed on {desired_markets[0] if desired_markets else 'all_markets'}"
                    )
                    return
        except websockets.exceptions.ConnectionClosed:
            continue


async def strategy(is_production=False):
    """
    The name of the game
    """
    load_dotenv()

    exchange_client = ExchangeClient(
        exchange_api_base=os.getenv("DEMO_API_BASE"),
        email=os.getenv("DEMO_EMAIL"),
        password=os.getenv("DEMO_PASSWORD"),
    )

    ## TODO: Start time of script in a given month in order to track volume for the given month, reset once new month happens - keep active track of current P/L
    initialization_datetime = dt.today()
    print(
        f"starting up TAJIR on {initialization_datetime.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    status = exchange_client.get_exchange_status()
    print(status)
    if status["exchange_active"]:
        while True:
	    # For this specific trader, the only event we're trying to trade on right now is S&P500 weekly close
            get_events = exchange_client.get_events(series_ticker="INXW", limit=1)[
                "events"
            ]
            newest_event = get_events[0]

            current_trading_event_ticker = newest_event["event_ticker"]
            print(
                f"tracking a new event: {current_trading_event_ticker}! --------------"
            )
            if not newest_event["markets"]:
                print(
                    "No markets available in this event that we're trading!! Shutting down TAJIR"
                )
                return

            markets_df = pd.DataFrame(newest_event["markets"])
            desired_markets_list = (
                markets_df["ticker"].to_list() if newest_event["markets"] else []
            )

            strike_datetime = dt.fromisoformat(newest_event["strike_date"])
            open_datetime = dt.fromisoformat(newest_event["markets"][0]["open_time"])
            til_then = (strike_datetime - dt.now(timezone.utc)).total_seconds()

            try:
                await asyncio.wait_for(
                    spin_up_markets_trader(
                        channels=["ticker", "fill"],
                        desired_markets=desired_markets_list,
                        exchange_client=exchange_client,
                        expiry_datetime=strike_datetime,
                        open_datetime=open_datetime,
                        is_production=is_production,
                    ),
                    timeout=til_then,
                )
                print(
                    f"strategy() is back! Going to cancel tracking the event {current_trading_event_ticker} trader now"
                )
            except asyncio.exceptions.CancelledError:
                print(f"\nTAJIR ceasing on {dt.today().strftime('%Y-%m-%d %H:%M:%S')}")
                return


# Run the event loop
if __name__ == "__main__":
    asyncio.run(strategy(is_production=True))
