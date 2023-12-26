import aiohttp
from tonsdk.contract.wallet import WalletVersionEnum, Wallets, SendModeEnum, WalletContract
from tonsdk.boc import Cell
import requests
from tonsdk.utils import Address, bytes_to_b64str

class Gram20:
    
    def __init__(self, user_wallet_address: str):
        self.user_address: str = user_wallet_address
        
    async def get_token_history(self, tick: str = "gram"):
        async with aiohttp.ClientSession() as session:
            try:
                url = f'https://api-2.gram20.com/v1/gram20/history/{self.user_address}/{tick}'
                async with session.get(url) as response:
                    gram_txs = await response.json()
                parsed_txs = []
                for tx in gram_txs:
                    parsed_txs.append({
                        'from_wallet': tx['peer'] if tx['delta'] >= 0 else tx['address'],
                        'to_wallet': tx['address'] if tx['delta'] >= 0 else tx['peer'],
                        'amount': tx['delta'],
                        'lt': tx['lt'],
                        'hash': tx['hash'],
                        'time': tx['time'],
                        'comment': tx['comment']                
                    })
            except Exception as e:
                print(f"An error occurred: {e}")
                parsed_txs = []

        return parsed_txs
    
    async def send_transaction(self, to: str, amt_gram: int, hash_str: str):
        
        seed = ['final', 'extend', 'rib', 'hawk', 'fox', 'beach',
               'armor', 'leg', 'donor', 'stumble', 'season', 'category',
               'panda', 'lumber', 'front', 'valve', 'love', 'expose', 
               'ugly', 'state', 'crystal', 'pudding', 'black', 'nurse']

        _, _, _, wallet = Wallets.from_mnemonics(seed, WalletVersionEnum.v4r2, 0)

        my_address = wallet.address.to_string(1, 1, 1)

        token_address = 'EQCzYd9cZUzcXA7OSGeDNc5iPgokIWboUJ6u7xEdDFK5tGd4'
        res = requests.get(f"https://tonapi.io/v2/blockchain/accounts/{token_address}/methods/get_user_data?args={my_address}").json()
        state_init = Cell.one_from_boc(res['stack'][0]['cell'])
        r = state_init.bytes_hash()
        a = Address('0:' + r.hex())
        mint_address = a.to_string(1, 1, 1)
        addr = res['stack'][1]['cell']

        payload_cell = Cell()
        payload_cell.bits.write_uint(0, 32)
        data = 'data:application/json,{"p":"gram-20","op":"transfer","tick":"gram","amt":"'+str(amt_gram)+'","to":"'+to+'"}'
        def snake(s, cell):
            if len(s) > 120:
                cell.bits.write_string(s[:120])
                child = snake(s[120:], Cell())
                cell.refs.append(child)
            else:
                cell.bits.write_string(s)
            return cell

        payload_cell = snake(data, payload_cell)

        seqno = int(requests.get(f"https://tonapi.io/v2/blockchain/accounts/{my_address}/methods/seqno").json()['stack'][0]['num'], 16)


        query = wallet.create_transfer_message(
            mint_address,
            50000000,
            seqno,
            payload=payload_cell,
            state_init=state_init
        )
        r = bytes_to_b64str(query['message'].to_boc(False))
        res = requests.post("https://toncenter-v4.gram20.com/sendBoc",
                            headers={"Content-Type": "application/json"},
                            json={"boc": r})
        return res
    
    async def get_token_balance(self, tick: str = "gram"):
        async with aiohttp.ClientSession() as session:
            try:
                url = f'https://api-2.gram20.com/v1/gram20/balance/{self.user_address}/{tick}'
                async with session.get(url) as response:
                    if response.status == 200:
                        token_amt = await response.json()
                        balance = token_amt['balance']
                    else:
                        raise Exception("Non-200 response from API")
            except Exception as e:
                # Consider using logging instead of print for production code
                print(f'[ERROR] GRAM20_API_REQUEST_ERROR: {e}')
                balance = 0
        return {'tick':tick, 'balance':balance}