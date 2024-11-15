import requests
import time
import logging
import requests
import concurrent.futures
from collections import defaultdict
import asyncio
import websockets
import sys

sys.stdout.reconfigure(encoding='utf-8')


seen_auctions = []
auctionism = defaultdict(lambda: {"lowest_price": float('inf'), "enchantments": None, "item_name": None, "reforge": None})
api = '1c19e635-6e0e-46f7-aedb-5c95d3a9dbc5'
API_URL = "https://api.hypixel.net/skyblock/auctions"
onifications = False

def get_auction_data():
    """Fetch auction data from the Hypixel API."""
    params = {'key': api}
    response = requests.get(API_URL, params=params)
    
    if response.status_code == 200:
        try:
            data = response.json()
            if 'auctions' in data and isinstance(data['auctions'], list):
                return data
            else:
                logging.warning("No 'auctions' key found in the API response.")
                return None
        except ValueError:
            logging.error("Failed to parse JSON response.")
            return None
    else:
        logging.error(f"Failed to fetch auction data: {response.status_code}")
        return None

def filter_bin_auctions(auction_data):
    """Filter out BIN auctions."""
    return [auction for auction in auction_data['auctions'] if auction.get('bin', False)]

# Define the set of blacksmith reforges
blacksmith_reforges = {
    'Epic','Fair','Fast','Gentle','Heroic','Legendary','Odd','Sharp','Spicy','Awkward','Deadly','Fine','Grand','Hasty','Neat','Rapid','Rich','Unreal','Clean','Fierce','Heavy','Light','Mythic','Pure','Titanic','Smart','Wise','Stained','Menacing','Hefty','Soft','Honored','Blended','Astute','Colossal','Brilliant','Epic','Fair','Fast','Gentle','Heroic','Legendary','Odd','Sharp','Spicy','Unyielding','Prospector\'s','Excellent','Sturdy','Fortunate','Great','Rugged','Lush','Lumberjack\'s','Double-Bit','Robust','Zooming','Peasant\'s','Green Thumb'
}

def remove_reforge(item_name):
    """Remove reforge from the item name."""
    for reforge in blacksmith_reforges:
        if reforge in item_name:
            # If reforge is found, remove it from the name
            return item_name.replace(reforge, '').strip()
    return item_name  # Return the original name if no reforge is found

seen_auctions = []

for a in filter_bin_auctions(get_auction_data()):
    seen_auctions.append(a['uuid'])

async def send_message(command):
    uri = "ws://localhost:8080"  # Server address
    async with websockets.connect(uri) as websocket:
        await websocket.send(command)  # Send the message asynchronously
        print(f"Sent: {command}")    
    



def fetch_page(api, page):
    """Fetch a specific page of auctions from the Hypixel API."""
    url = f'https://api.hypixel.net/skyblock/auctions?key={api}&page={page}'
    response = requests.get(url)
    data = response.json()
    return data.get('auctions', [])

def get_total_pages(api):
    """Fetch the total number of pages for auctions."""
    url = f'https://api.hypixel.net/skyblock/auctions?key={api}&page=0'
    response = requests.get(url)
    data = response.json()
    return data['totalPages'] if data['success'] else 0

def fetch_all_auctions(api):
    """Fetch all auctions using multithreading."""
    total_pages = get_total_pages(api)
    all_auctions = []
    
    # Use ThreadPoolExecutor to fetch pages concurrently
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Create a list of futures, each calling fetch_page with a different page number
        futures = [executor.submit(fetch_page, api, page) for page in range(total_pages)]
        
        # Gather results as they complete
        for future in concurrent.futures.as_completed(futures):
            all_auctions.extend(future.result())
    
    return all_auctions

all_auctions = fetch_all_auctions(api)



def process_auctions_and_update_prices(auctions):
    # Dictionary to hold the lowest price for each unique item
    item_data = defaultdict(lambda: {"lowest_price": float('inf'), "enchantments": None, "item_name": None, "reforge": None})
    
    # Loop through each auction
    for auction in auctions:
        # Skip if not a BIN auction
        if auction.get('bin') is not True:
            continue
        
        # Extract relevant fields for grouping items
        item_name = auction.get('item_name')
        reforge = auction.get('reforge')
        rarity = auction.get('rarity', 'Common')

        # Strip the reforge from the item name to compare base items
        base_item_name = remove_reforge(item_name)

        # Create a unique key for each item based on its properties
        item_key = (base_item_name, rarity)

        # Check if the item is already in the dictionary
        if item_key in item_data:
            # If the item is already in the dict, compare prices
            current_lowest_price = item_data[item_key]["lowest_price"]
            starting_bid = auction.get('starting_bid', 0)  # Get the starting bid from the auction data
            
            if starting_bid < current_lowest_price:
                # If the new price is lower, update the dictionary
                item_data[item_key]["lowest_price"] = starting_bid
                item_data[item_key]["reforge"] = reforge  # Update the reforge
        else:
            # If the item is not in the dict, add it with the current price
            starting_bid = auction.get('starting_bid', 0)
            item_data[item_key]["lowest_price"] = starting_bid
            item_data[item_key]["item_name"] = item_name  # Store the full item name
            item_data[item_key]["reforge"] = reforge  # Store the reforge


    auctionism = item_data

# List to keep track of all active WebSocket connections
active_connections = set()

async def handle_client(websocket, path):
    # Register the new connection
    active_connections.add(websocket)
    print(f"New connection: {websocket.remote_address}")

    try:
        # Receive and handle messages from the client
        async for message in websocket:
            print(message)
            if str(message) == '{"message":"START"}':
                onifications = True
                process_auctions_and_update_prices(all_auctions)
                # Use await to run monitor_auctions as a coroutine
                """Monitor auctions and print new BIN auctions to the terminal with a profit margin threshold."""
                while onifications:
                    auction_data = get_auction_data()
                    
                    if auction_data:
                        # Filter for BIN auctions
                        bin_auctions = filter_bin_auctions(auction_data)
                        
                        if bin_auctions:
                            new_auctions = []
                            blocked_count = 0  # Counter for auctions blocked by the filter

                            for auction in bin_auctions:
                                auction_id = auction['uuid']
                                starting_bid = auction.get('starting_bid', 0)
                                item_name = auction.get('item_name', 'Unknown Item')
                                reforge = auction.get('reforge')
                                rarity = auction.get('rarity', 'Common')

                                # Create a unique key to look up the item in auctionism
                                base_item_name = remove_reforge(item_name)
                                item_key = (base_item_name, rarity)
                                
                                # Update the part where new auctions are added to the list
                                if auction_id not in seen_auctions:
                                    seen_auctions.append(auction_id)
                                    
                                    # Check if item exists in auctionism
                                    if item_key not in auctionism:
                                        # If item is not in auctionism, add it as a new entry
                                        auctionism[item_key] = {
                                            "lowest_price": starting_bid,
                                            "item_name": item_name,
                                            "reforge": reforge,
                                            "uuid": auction_id  # Add the uuid to auctionism
                                        }
                                        # This is a new lowest BIN auction because it’s newly added
                                        new_auctions.append(auction)
                                    else:
                                        # Item exists in auctionism, check if this price is lower
                                        current_lowest_price = auctionism[item_key]["lowest_price"]
                                        if current_lowest_price is None:
                                            current_lowest_price = 0
                                        if starting_bid < current_lowest_price:
                                            # Calculate the profit margin
                                            profit_margin = ((current_lowest_price / starting_bid) * 100) - 100
                                            profit_min = current_lowest_price - starting_bid
                                            
                                            # Only update and display if profit margin is above threshold
                                            if profit_margin > 10 and profit_min > 1000000:
                                                # Update auctionism with the new lowest price for this item
                                                auctionism[item_key]["lowest_price"] = starting_bid
                                                auctionism[item_key]["item_name"] = item_name
                                                auctionism[item_key]["reforge"] = reforge
                                                auctionism[item_key]["uuid"] = auction_id  # Add the uuid to auctionism
                                                
                                                # Add to new_auctions list to print details
                                                new_auctions.append(auction)
                                                print("Snipe: {} going for {} -> {} with profit margin {:.2f}%".format(repr(item_name), starting_bid, current_lowest_price, profit_margin))
                                                message = f'/viewauction {auction_id}'
                                                if active_connections:  # Check if there are any connected clients
                                                    # Send the message to all connected clients
                                                    await asyncio.gather(
                                                        *[client.send(message) for client in active_connections]
                                                    )
                                                    print(f"Broadcasted message: {message}")
                                                else:
                                                    print("No clients to broadcast to.")
                                                
                                            else:
                                                # Increment the counter if the auction was blocked by the filter
                                                blocked_count += 1
                            
                            # Print the details of the new lowest BIN auctions if any were found
                            if not new_auctions:
                                print("No new lowest BIN auctions.")
                            
                            # Print the count of auctions blocked by the filter, if any
                            if blocked_count > 0:
                                print(f"{blocked_count} auctions have been blocked by your filter.")
                            
                        else:
                            print("No BIN auctions received in the latest data.")
                        
                    else:
                        print("No auction data available or failed to retrieve auctions.")


                    
                    
                    # Sleep for a specified interval (e.g., 5 seconds)
                    if new_auctions:
                        await asyncio.sleep(55)
                    else:
                        await asyncio.sleep(0.05)
            elif message == {"message":"STOP"}:
                onifications = False
            # Process the message or send a response
            response = f"Message received: {message}"
            await websocket.send(response)
    except websockets.ConnectionClosed:
        print(f"Connection closed with {websocket.remote_address}")
    finally:
        # Unregister the connection when it's closed
        active_connections.remove(websocket)

async def main():
    # Start the WebSocket server, listening on all interfaces and port 8765
    server = await websockets.serve(handle_client, "0.0.0.0", 8080)
    print("WebSocket server running on ws://87.106.65.12:8080")
    
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
