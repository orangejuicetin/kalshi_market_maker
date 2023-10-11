# Project TAJIR - a market maker for [Kalshi](https://kalshi.com/)

Started in my time at the [Recurse Center](https://recurse.com/about) and a wonderful way to get in the weeds concerning markets, orderbooks, and figuring out how to navigate the treacherous, low-liquidity/volume terrain that is an early stage market. 

Built simply and entirely in Python, meant to be lightweight so as to run on a Droplet and not need too much computational strain. Reach out to me if you ever want to chat concerning it! 

## Breakdown
This script makes use of the [`asyncio`](https://docs.python.org/4/library/asyncio.html) package in Python to spin up a separate coroutine outside of main coroutine `strategy()` function that's running which will only last as long as given market does. To get here took many hours of [debugging and struggle](https://juicetin.bearblog.dev/asyncio_nightmares_in_python/?preview=true) which I did a writeup on, but the final product is clean and simple.

Hence, if we spin up a markets trader on the `INXW-23OCT13` event, our initial coroutine of `strategy()` goes ahead and calculates the exact amount of time in seconds to run this coroutine for, running it with a timeout value of said seconds with [`asyncio.wait_for()`](https://github.com/orangejuicetin/kalshi_market_maker/blob/cb79c44f018d635907720c846c7a6ed7c6712b85/market_maker.py#L190). It's here that we have logic that listens to the Kalshi market feed through websocket, handles update messages as they come, execute our trading logic, etc. 

Simple. Easy.

A natural extension being considered is to increase this event loop to handle different events with different expiries – have this main coroutine spin up one coroutine that tracks a certain event that expires weekly, spin up a different one that tracks a same-day expiring event, so on and so forth. For now, this project is in a steady state so as for me to commit these changes, but as time goes on if this structure changes I'll update this repo accordingly. 

