# python-gridcoin

A python library for Gridcoin-related stuff. `python-gridcoin` is a [sans-IO library](https://sans-io.readthedocs.io/) so you'll have to bring your own networking library in order to use the networking related functions.

## Installation

```sh
pip install .

# Alternatively, in edit mode for development:

pip install -e .
```

## Quickstart

```python
import httpx # or requests
from gridcoin.rpc import WalletRPC

# Connect to the mainnet client automatically:
rpc = WalletRPC(httpx.post)

# Testnet:
rpc = WalletRPC(httpx.post, testnet)

# You can also provide your own URL to connect:
rpc = WalletRPC(httpx.post, url="http://user:password@localhost:15715")

print(rpc.help())
```

Async IO is also supported:

```python
import asyncio

import aiohttp
from gridcoin.rpc import WalletRPC


async def main():
    async with aiohttp.ClientSession() as client_session:
        rpc = WalletRPC(client_session.post)
        print(await rpc.getblockcount())


if __name__ == "__main__":
    asyncio.run(main())
```

## License

python-gridcoin is under the [MIT License](LICENSE).
