import requests
import time
import logging

# Setup logging to print messages to the terminal
logging.basicConfig(level=logging.INFO)

# Hypothetical API URL
API_URL = "https://api.hypixel.net/skyblock/auctions"
# Replace with your actual API key
API_KEY = "1c19e635-6e0e-46f7-aedb-5c95d3a9dbc5"

seen_auctions = []

def get_auction_data():
    """Fetch auction data from the Hypixel API."""
    params = {'key': API_KEY}
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

seen_auctions = []

for a in filter_bin_auctions(get_auction_data()):
    seen_auctions.append(a['uuid'])

def monitor_auctions():
    """Monitor auctions and print new BIN auctions to the terminal."""
    while True:
        auction_data = get_auction_data()
        
        if auction_data:
            # Print out the raw auction data to debug the structure

            # Filter for BIN auctions
            bin_auctions = filter_bin_auctions(auction_data)
            
            if bin_auctions:
                new_auctions = []
                for auction in bin_auctions:
                    auction_id = auction['uuid']
                    if auction_id not in seen_auctions:
                        seen_auctions.append(auction_id)
                        new_auctions.append(auction)

                if new_auctions:
                    for auction in new_auctions:
                        # Print the new BIN auction details to the terminal
                        print(f"New BIN auction found!")
                        print(f"Item: {auction['item_name']}")
                        print(f"Price: {auction['starting_bid']}")
                        print(f"UUID: {auction['uuid']}")
                        print("-" * 40)
                else:
                    # Print "No new BIN auctions" if no new auctions are found
                    print("No new BIN auctions.")
            else:
                print("No BIN auctions received in the latest data.")
        else:
            print("No auction data available or failed to retrieve auctions.")
        
        # Sleep for a specified interval (e.g., 30 seconds)
        time.sleep(5)

if __name__ == "__main__":
    monitor_auctions()
