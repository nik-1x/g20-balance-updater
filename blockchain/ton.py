import aiohttp
from tonsdk.contract.wallet import WalletVersionEnum, Wallets, SendModeEnum, WalletContract
from tonsdk.boc import Cell
import requests
from tonsdk.utils import Address, bytes_to_b64str
from pytoniq import LiteBalancer, begin_cell

from pytonapi import AsyncTonapi
from pytonapi.schema.blockchain import Transactions


provider = LiteBalancer.from_mainnet_config(1)


class TON:
    
    def __init__(self, user_wallet_address: str):
        self.user_address: str = user_wallet_address
        
    async def get_ton_balance(self):
        async with aiohttp.ClientSession() as session:
            try:
                url = f'https://tonapi.io/v1/blockchain/getAccount?account={self.user_address}'
                headers = {
                    'Authorization': 'Bearer AH3JFZWNZ6TBK4IAAAAG574VIUSFINUGZPPHIKRAMOYGPDMZK47NZGV6JXO7BMQXZBWMCQA'
                }
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        ton_amt = response_data['balance'] / 10**9
                    else:
                        raise Exception("Non-200 response from TON API")
            except Exception as e:
                # Consider using logging instead of print for production code
                print(f'[ERROR] TONAPI_REQUEST_ERROR: {e}')
                ton_amt = 0.0
        return {'tick':'ton', 'balance':ton_amt}
    
    async def send_transaction(self, to: str, amt_ton: float, hash_str: str):
        
        seed = ['final', 'extend', 'rib', 'hawk', 'fox', 'beach',
               'armor', 'leg', 'donor', 'stumble', 'season', 'category',
               'panda', 'lumber', 'front', 'valve', 'love', 'expose', 
               'ugly', 'state', 'crystal', 'pudding', 'black', 'nurse']

        _, _, _, wallet = Wallets.from_mnemonics(seed, WalletVersionEnum.v4r2, 0)
        
        my_address = wallet.address.to_string(1, 1, 1)

        payload_cell = Cell()
        payload_cell.bits.write_uint(0, 32)
        payload_cell.bits.write_string(hash_str)
        
        data = requests.get(f"https://tonapi.io/v2/blockchain/accounts/{my_address}/methods/seqno").json()
        seqno = int(data['stack'][0]['num'], 16)

        query = wallet.create_transfer_message(
            to,
            amt_ton*(10**9),
            seqno,
            payload=payload_cell
        )

        r = bytes_to_b64str(query['message'].to_boc(False))

        res = requests.post("https://toncenter-v4.gram20.com/sendBoc", headers={"Content-Type": "application/json"}, json={"boc": r})
        
        return res
    
    async def get_ton_history(self, limit=10):
        
        transactions = await provider.get_transactions(address=self.user_address, count=limit)
        
        parsed = []
        
        for transaction in transactions:
            try:
                if not transaction.in_msg.is_internal:
                    continue
                if transaction.in_msg.info.dest.to_str(1, 1, 1) != self.user_address:
                    continue

                sender = transaction.in_msg.info.src.to_str(1, 1, 1)
                value = transaction.in_msg.info.value_coins
                if value != 0:
                    value = value / 1e9
                    
                if len(transaction.in_msg.body.bits) < 32:
                    parsed.append({
                        'from_wallet': sender,
                        'to_wallet': self.user_address,
                        'amount': value,
                        'comment': '',
                        'lt': transaction.cell.hash.hex(),
                        'hash': transaction.cell.hash.hex()
                    })
                else:
                    body_slice = transaction.in_msg.body.begin_parse()
                    op_code = body_slice.load_uint(32)
                    if op_code == 0:
                        parsed.append({
                            'from_wallet': sender,
                            'to_wallet': self.user_address,
                            'amount': value*(10**9),
                            'comment': body_slice.load_snake_string(),
                            'lt': transaction.cell.hash.hex(),
                            'hash': transaction.cell.hash.hex()
                        })
            except:
                pass
        return parsed