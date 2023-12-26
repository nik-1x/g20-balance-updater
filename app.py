from sanic import Sanic, Request, response
from blockchain.gram20 import Gram20
from blockchain.ton import TON
import asyncio
from services_api import Service


app = Sanic('admin-service')
service = Service()

wallets = asyncio.run(service.get_wallet_config())['wallets']

gram20_receive = Gram20(wallets['gram20_receive_address'])
gram20_send = Gram20(wallets['gram20_send_address'])
ton_send = TON(wallets['ton_send_address'])
ton_receive = TON(wallets['ton_receive_address'])

actual_balances = {
    'gram': {
        'send': {
            'balance': 0,
            'wallet': gram20_send.user_address
        },
        'receive': {
            'balance': 0,
            'wallet': gram20_receive.user_address
        }
    },
    'ton': {
        'send': {
            'balance': 0,
            'wallet': ton_send.user_address
        },
        'receive': {
            'balance': 0,
            'wallet': ton_receive.user_address
        }
    }
}


@app.route('/balances', methods=['GET'])
async def get_config(data: Request):
    print(data.get_query_args())
    return response.json(actual_balances)
    
    
async def balance_updater():
    global actual_balances
    while True:
        actual_balances['gram']['send']['balance']     = (await gram20_send.get_token_balance('gram'))['balance']
        actual_balances['gram']['receive']['balance']  = (await gram20_receive.get_token_balance('gram'))['balance']
        actual_balances['ton']['send']['balance']      = (await ton_send.get_ton_balance())['balance']
        actual_balances['ton']['receive']['balance']   = (await ton_receive.get_ton_balance())['balance']
        await asyncio.sleep(5.0)
        
        
app.add_task(balance_updater)

if __name__ == "__main__":
    app.run('localhost', 5001, dev=True, fast=True, auto_reload=True, motd=False)