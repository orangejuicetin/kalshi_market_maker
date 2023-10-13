# Project TAJIR - a market maker for [Kalshi](https://kalshi.com/)

Started in my time at the [Recurse Center](https://recurse.com/about) and a wonderful way to get in the weeds concerning markets, orderbooks, and figuring out how to navigate the treacherous, low-liquidity/volume terrain that is an early stage market. 

Built simply and entirely in Python, meant to be lightweight so as to run on a Droplet and not need too much computational strain.  

## Breakdown
This script makes use of the [`asyncio`](https://docs.python.org/4/library/asyncio.html) package in Python.

Two coroutines. The main coroutine: our async `strategy()` function that we think of as main. Separately, `spin_up_markets_trader()` running only as long as given market does. To get here took many hours of [debugging and struggle](https://juicetin.bearblog.dev/asyncio_nightmares_in_python/?preview=true) which I did a writeup on, but the final product is clean and simple.

Hence, if we spin up a markets trader on the `INXW-23OCT13` event, `strategy()` goes ahead and calculates the exact amount of time in seconds to run `spin_up_markets_trader()` for, running it with a timeout value of said seconds with [`asyncio.wait_for()`](https://github.com/orangejuicetin/kalshi_market_maker/blob/cb79c44f018d635907720c846c7a6ed7c6712b85/market_maker.py#L190) before gracefully shutting it down. It's inside `spin_up_markets_trader()` that we have the bulk of our logic that listens to the Kalshi market feed through websocket, handles update messages as they come, executes our trading logic, etc. 

Simple. Easy.

## Planned next steps

A natural extension being considered is to increase this event loop to handle different events with different expiries – have this main coroutine spin up one coroutine that tracks a certain event that expires weekly, spin up a different one that tracks a same-day expiring event, so on and so forth. For now, this project is in a steady state so as for me to commit these changes, but as time goes on if this structure changes I'll update this repo accordingly. 

If you're also interested in markets and ever want to chat finance, more than happy to chat! Ping me on email ~

## Some interesting explorations of market behavior 
Generated these in a separate Jupyter notebook I didn't commit to this repo b/c of credentials, but thought that they were interesting enough to exhibit here: 

![INXD-23SEP11-B4462_trade_vs_price](https://github.com/orangejuicetin/kalshi_market_maker/assets/47411373/5ca0b16c-3056-4947-8401-735de784116a)

![INXD-23SEP11-B4462_bidask_vs_price](https://github.com/orangejuicetin/kalshi_market_maker/assets/47411373/3b2b4bc7-328c-49df-a5e6-4757bd07f01b)

1. The initial volatility in bid-ask quotes is quite crazy, makes me wonder how this would compare to a standard options/equities orderbook graph. Also wondering if it's Kalshi themselves making these very frequent, constant changing in limit order placing til something catches! 
2. The timing and quantity of certain trades at various prices seem to suggest the activity of other market makers on platform or just very heuristic-based retail traders. This was the starting point for me trying to find places where this algorithm can ultimately be _useful_, providing a service of some sort to provide liquidity. 
