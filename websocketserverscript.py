import asyncio
import websockets

# Define the WebSocket server handler
async def echo(websocket):
    print("Client connected")
    try:
        async for message in websocket:
            print(f"Received message: {message}")
            await websocket.send(f"Echo: {message}")  # Echo the message back to the client
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")

# Start the WebSocket server
async def main():
    server = await websockets.serve(echo, "localhost", 8080)
    print("WebSocket server started on ws://localhost:8080")
    await server.wait_closed()

# Run the server
if __name__ == "__main__":
    asyncio.run(main())
