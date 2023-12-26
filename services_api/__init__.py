import aiohttp


class Request:

    async def get_request(self, url, query: dict = None, headers: dict = {}):
        async with aiohttp.ClientSession() as session:
            query_string = ""
            if query is not None:
                query_string = "?" + "&".join([f"{key}={query[key]}" for key in list(query.keys())])
            async with session.get(url + query_string, headers=headers) as response:
                if response.status == 200:
                    response_data = await response.json()
                else:
                    raise Exception("Non-200 response from TON API")
        return response_data

    async def post_request(self, url, data: dict = None, headers: dict = {}):
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers) as response:
                if response.status == 200:
                    response_data = await response.json()
                else:
                    raise Exception("Non-200 response from API")
        return response_data


class Service(Request):

    def __init__(self):
        super().__init__()

    async def get_balances(self):
        return await self.get_request(
            url="http://localhost:5001/balances"
        )

    async def get_app_config(self):
        config = await self.get_request(
            url="http://localhost:5002/get-config"
        )
        return {
            'buyprice_per_gram': float(config['buyprice_per_gram']),
            'sellprice_per_gram': float(config['sellprice_per_gram']),
            'minbuy_in_ton': float(config['minbuy_in_ton']),
            'maxbuy_in_ton': float(config['maxbuy_in_ton']),
            'ton_send_min_balance': float(config['ton_send_min_balance']),
            'minsell_in_ton': float(config['minsell_in_ton']),
            'maxsell_in_ton': float(config['maxsell_in_ton']),
            'gram_send_min_balance': float(config['gram_send_min_balance']),
            'clientbot_status': config['clientbot_status'],
        }

    async def get_wallet_config(self, apikey: str = None):
        return await self.get_request(
            url="http://localhost:5002/get-wallets",
            query={'apikey': apikey} if apikey is not None else None
        )