import asyncio
import websockets
import json
import requests
import time
import concurrent.futures
from collections import defaultdict

API_URL = "https://api.hypixel.net/skyblock/auctions"
API_KEY = '1c19e635-6e0e-46f7-aedb-5c95d3a9dbc5'
WS_PORT = 8765  # WebSocket port

seen_auctions = []
auctionism = defaultdict(lambda: {"lowest_price": float('inf'), "enchantments": None, "item_name": None, "reforge": None})

# Define the WebSocket server
async def websocket_handler(websocket, path):
    """Handle incoming WebSocket connections."""
    print("New client connected!")
    try:
        async for message in websocket:
            print("Received message from client:", message)
    except websockets.ConnectionClosed:
        print("Client disconnected.")

# Broadcast new auction updates to WebSocket clients
connected_clients = set()

async def broadcast_message(message):
    """Send a message to all connected WebSocket clients."""
    if connected_clients:
        await asyncio.gather(*(client.send(message) for client in connected_clients))

# WebSocket server for handling client connections
async def websocket_server():
    async with websockets.serve(websocket_handler, "localhost", WS_PORT):
        await asyncio.Future()  # Run forever

# Fetch Hypixel auction data
def get_auction_data():
    params = {'key': API_KEY}
    response = requests.get(API_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        return data if 'auctions' in data else None
    return None

def filter_bin_auctions(auction_data):
    return [auction for auction in auction_data['auctions'] if auction.get('bin', False)]

async def monitor_auctions(profit_margin_threshold=10):
    """Monitor auctions and broadcast new BIN auctions over WebSocket."""
    while True:
        auction_data = get_auction_data()
        if auction_data:
            bin_auctions = filter_bin_auctions(auction_data)
            if bin_auctions:
                new_auctions = []
                for auction in bin_auctions:
                    auction_id = auction['uuid']
                    starting_bid = auction.get('starting_bid', 0)
                    item_name = auction.get('item_name', 'Unknown Item')
                    
                    # New BIN auction found
                    if auction_id not in seen_auctions:
                        seen_auctions.append(auction_id)
                        message = f"Snipe: {item_name} at {starting_bid}"
                        new_auctions.append(message)
                        await broadcast_message(json.dumps({"item": item_name, "price": starting_bid}))
                if new_auctions:
                    print(f"Broadcasting {len(new_auctions)} new auctions.")
            else:
                print("No BIN auctions found.")
        else:
            print("Failed to retrieve auction data.")
        
        await asyncio.sleep(5)

async def main():
    await asyncio.gather(websocket_server(), monitor_auctions())

# Run both the WebSocket server and auction monitor
asyncio.run(main())
