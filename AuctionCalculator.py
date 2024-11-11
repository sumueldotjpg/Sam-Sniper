import requests
import concurrent.futures
from collections import defaultdict

api = '1c19e635-6e0e-46f7-aedb-5c95d3a9dbc5'

# Define the set of blacksmith reforges
blacksmith_reforges = {
    'Epic','Fair','Fast','Gentle','Heroic','Legendary','Odd','Sharp','Spicy','Awkward','Deadly','Fine','Grand','Hasty','Neat','Rapid','Rich','Unreal','Clean','Fierce','Heavy','Light','Mythic','Pure','Titanic','Smart','Wise','Stained','Menacing','Hefty','Soft','Honored','Blended','Astute','Colossal','Brilliant','Epic','Fair','Fast','Gentle','Heroic','Legendary','Odd','Sharp','Spicy','Unyielding','Prospector\'s','Excellent','Sturdy','Fortunate','Great','Rugged','Lush','Lumberjack\'s','Double-Bit','Robust','Zooming','Peasant\'s','Green Thumb'
}

def fetch_page(api_key, page):
    """Fetch a specific page of auctions from the Hypixel API."""
    url = f'https://api.hypixel.net/skyblock/auctions?key={api_key}&page={page}'
    response = requests.get(url)
    data = response.json()
    return data.get('auctions', [])

def get_total_pages(api_key):
    """Fetch the total number of pages for auctions."""
    url = f'https://api.hypixel.net/skyblock/auctions?key={api_key}&page=0'
    response = requests.get(url)
    data = response.json()
    return data['totalPages'] if data['success'] else 0

def fetch_all_auctions(api_key):
    """Fetch all auctions using multithreading."""
    total_pages = get_total_pages(api_key)
    all_auctions = []
    
    # Use ThreadPoolExecutor to fetch pages concurrently
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Create a list of futures, each calling fetch_page with a different page number
        futures = [executor.submit(fetch_page, api_key, page) for page in range(total_pages)]
        
        # Gather results as they complete
        for future in concurrent.futures.as_completed(futures):
            all_auctions.extend(future.result())
    
    return all_auctions

all_auctions = fetch_all_auctions(api)

def remove_reforge(item_name):
    """Remove reforge from the item name."""
    for reforge in blacksmith_reforges:
        if reforge in item_name:
            # If reforge is found, remove it from the name
            return item_name.replace(reforge, '').strip()
    return item_name  # Return the original name if no reforge is found

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

    # Write the results to a text file
    write_lowest_prices_to_file(item_data)

def write_lowest_prices_to_file(item_data, filename="lowest_prices.txt"):
    # Open the file with utf-8 encoding to handle all Unicode characters
    with open(filename, 'w', encoding='utf-8') as file:
        for item_key, data in item_data.items():
            # Unpack item properties
            item_name = data["item_name"]
            lowest_price = data["lowest_price"]
            item_rarity = data["item_name"].split()[0]  # Assuming rarity is the first part of the name
            reforge = data["reforge"]

            # Write to the file in the specified format
            file.write(f"{item_name} Price:{lowest_price:.2f}, Rarity:{item_rarity}, Reforge:{reforge}\n")

# Usage: Assuming `all_auctions` is the list of auction data
process_auctions_and_update_prices(all_auctions)