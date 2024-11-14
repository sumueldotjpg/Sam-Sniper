import asyncio
import websockets

# List to keep track of connected clients
clients = set()

async def handler(websocket, path):
    # Register new client
    clients.add(websocket)
    try:
        # Keep the connection open and listen for incoming messages
        async for message in websocket:
            print(f"Received message: {message}")
            # Echo message back to client
            await websocket.send(f"Echo: {message}")
    finally:
        # Unregister client
        clients.remove(websocket)

# Function to broadcast a message to all clients
async def broadcast(message):
    if clients:  # Only send if there are connected clients
        await asyncio.wait([client.send(message) for client in clients])

# Function to send a message to a specific client
async def send_to_client(client, message):
    if client in clients:
        await client.send(message)

# Run the WebSocket server
async def main():
    port = 8080
    ip = "0.0.0.0"
    async with websockets.serve(handler, ip, port):
        print(f"WebSocket server started on ws://{ip}:{port}")
        await asyncio.Future()  # Run forever

asyncio.run(main())
