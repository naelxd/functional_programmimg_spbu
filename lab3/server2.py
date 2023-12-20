import asyncio

class AsyncServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.clients = {}
        self.rooms = {}

    async def start(self):
        self.server = await asyncio.start_server(self.handle_client, self.host, self.port)
        print(f'Server started at {self.host}:{self.port}')

        async with self.server:
            await self.server.serve_forever()

    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        print(f'New connection from {addr}')

        # Register new client
        client_name = await self.register_client(reader, writer)

        try:
            while True:
                data = await reader.readline()
                if not data:
                    break

                message = data.decode().strip()
                if message.startswith('/'):
                    await self.handle_command(client_name, message)
                else:
                    await self.send_message(client_name, message)
        except ConnectionResetError:
            pass
        finally:
            # Unregister client
            await self.unregister_client(client_name)
            writer.close()
            print(f'Connection from {addr} closed')

    async def register_client(self, reader, writer):
        # Ask client for username
        writer.write(b'Enter your name: ')
        await writer.drain()

        # Wait for client's response
        client_name = (await reader.readline()).decode().strip()

        # Check if username is already taken
        while client_name in self.clients:
            writer.write(b'This name is already taken. Enter another name: ')
            await writer.drain()
            client_name = (await reader.readline()).decode().strip()

        # Register new client
        self.clients[client_name] = (reader, writer)
        print(f'{client_name} has joined the server')

        # Put client in default room
        await self.join_room(client_name, 'default')

        return client_name

    async def unregister_client(self, client_name):
        if client_name in self.clients:
            del self.clients[client_name]
            print(f'{client_name} has left the server')

            # Remove client from all rooms
            for room_name, room_clients in self.rooms.items():
                if client_name in room_clients:
                    room_clients.remove(client_name)
                    await self.send_message_to_room(room_name, f'{client_name} has left the room')

    async def handle_command(self, client_name, message):
        parts = message.split()
        command = parts[0][1:].lower()

        if command == 'rooms':
            await self.list_rooms(client_name)
        elif command == 'join':
            if len(parts) < 2:
                await self.send_error(client_name, 'Usage: /join <room>')
            else:
                await self.join_room(client_name, parts[1])
        elif command == 'leave':
            if len(parts) < 2:
                await self.send_error(client_name, 'Usage: /leave <room>')
            else:
                await self.leave_room(client_name, parts[1])
        else:
            await self.send_error(client_name, f'Unknown command: {command}')

    async def list_rooms(self, client_name):
        rooms = ', '.join(self.rooms.keys())
        await self.send_message_to_client(client_name, f'Available rooms: {rooms}')

    async def join_room(self, client_name, room_name):
        if room_name not in self.rooms:
            self.rooms[room_name] = []

        if client_name in self.rooms[room_name]:
            await self.send_error(client_name, f'You are already in room "{room_name}"')
        else:
            # Remove client from all other rooms
            for other_room_name, other_room_clients in self.rooms.items():
                if client_name in other_room_clients and other_room_name != room_name:
                    other_room_clients.remove(client_n)
