import asyncio
import sys
import logging
import pathlib
import os
from client_model import Client
from datetime import datetime


class Server:
    def __init__(self, ip: str, port: int, loop: asyncio.AbstractEventLoop):
        self.__ip: str = ip
        self.__port: int = port
        self.__loop: asyncio.AbstractEventLoop = loop
        self.__logger: logging.Logger = self.initialize_logger()
        self.__clients: dict[asyncio.Task, Client] = {}
        self.__rooms = {
                'default': []
                }

        self.logger.info(f"Server Initialized with {self.ip}:{self.port}")

    @property
    def ip(self):
        return self.__ip

    @property
    def port(self):
        return self.__port

    @property
    def loop(self):
        return self.__loop

    @property
    def logger(self):
        return self.__logger

    @property
    def clients(self):
        return self.__clients

    def initialize_logger(self):
        path = pathlib.Path(os.path.join(os.getcwd(), "logs"))
        path.mkdir(parents=True, exist_ok=True)

        logger = logging.getLogger('Server')
        logger.setLevel(logging.DEBUG)

        ch = logging.StreamHandler()
        fh = logging.FileHandler(
            filename=f'logs/{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}_server.log'
        )
        ch.setLevel(logging.INFO)
        fh.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            '[%(asctime)s] - %(levelname)s - %(message)s'
        )

        ch.setFormatter(formatter)
        fh.setFormatter(formatter)
        logger.addHandler(ch)
        logger.addHandler(fh)

        return logger

    def start_server(self):
        try:
            self.server = asyncio.start_server(
                self.accept_client, self.ip, self.port
            )
            self.loop.run_until_complete(self.server)
            self.loop.run_forever()
        except Exception as e:
            self.logger.error(e)
        except KeyboardInterrupt:
            self.logger.warning("Keyboard Interrupt Detected. Shutting down!")

        self.shutdown_server()

    def accept_client(self, client_reader: asyncio.StreamReader, client_writer: asyncio.StreamWriter):
        client = Client(client_reader, client_writer)
        task = asyncio.Task(self.incoming_client_message_cb(client))
        self.clients[task] = client
        self.__rooms['default'].append(client.nickname)

        client_ip = client_writer.get_extra_info('peername')[0]
        client_port = client_writer.get_extra_info('peername')[1]
        self.logger.info(f"New Connection: {client_ip}:{client_port}")
        client.writer.write("Write /help".encode('utf8'))

        task.add_done_callback(self.disconnect_client)

    async def incoming_client_message_cb(self, client: Client):
        while True:
            client_message = await client.get_message()

            if client_message.startswith("quit"):
                break
            elif client_message.startswith("/"):
                self.handle_client_command(client, client_message)
            else:
                recipients = None
                for room in self.__rooms:
                    if client.nickname in self.__rooms[room]:
                        recipients = self.__rooms[room]
                        break

                self.broadcast_message(
                    f"{client.nickname}: {client_message}".encode('utf8'),
                    inclusion_list=recipients)

            self.logger.info(f"{client_message}")

            await client.writer.drain()

        self.logger.info("Client Disconnected!")

    def handle_client_command(self, client: Client, client_message: str):
        client_message = client_message.replace("\n", "").replace("\r", "")

        if client_message.startswith("/nick"):
            user_room = None
            for room in self.__rooms:
                if client.nickname in self.__rooms[room]:
                    user_room = room
                    break
            split_client_message = client_message.split(" ")
            if len(split_client_message) >= 2:
                self.__rooms[room].remove(client.nickname)
                client.nickname = split_client_message[1]
                self.__rooms[room].append(client.nickname)
                client.writer.write(
                    f"Nickname changed to {client.nickname}\n".encode('utf8'))
                return
        elif client_message.startswith("/rooms"):
            rooms = '\n'.join([f"{key}: {value}" for key, value in self.__rooms.items()])
            client.writer.write(rooms.encode('utf8'))
            return
        elif client_message.startswith("/join"):
            command = client_message.split(' ')
            if len(command) == 2:
                user_room = None
                for room in self.__rooms:
                    if client.nickname in self.__rooms[room]:
                        user_room = room
                        break
                if user_room == command[1]:
                    client.writer.write("You already in this room\n".encode('utf8'))
                    return

                self.__rooms[user_room].remove(client.nickname)
                if command[1] not in self.__rooms:
                    self.__rooms[command[1]] = []
                self.__rooms[command[1]].append(client.nickname)
                client.writer.write("Room changed\n".encode('utf8'))
                return
        elif client_message.startswith("/myroom"):
            user_room = None
            for room in self.__rooms:
                if client.nickname in self.__rooms[room]:
                    user_room = room
                    break
            client.writer.write(f"Your room is {room}\n".encode('utf8'))
            return
        elif client_message.startswith("/personal"):
            command = client_message.split(' ')
            if len(command) > 2:
                self.broadcast_message(
                        f"personal:{client.nickname}: {' '.join(command[2:])}".encode('utf8'),
                    inclusion_list=[client.nickname, command[1]])
                return

        elif client_message.startswith("/help"):
                client.writer.write(
                    '''/nick <nickname> to change nickname
/rooms to see list of rooms
/join <room> to join room
/myroom to see your room
/personal <nick> <message> to send personal message'''.encode('utf8'))
                return

        client.writer.write("Invalid Command use /help\n".encode('utf8'))


    def broadcast_message(self, message: bytes, inclusion_list: list = []):
        for client in self.clients.values():
            if client.nickname in inclusion_list:
                client.writer.write(message)

    def disconnect_client(self, task: asyncio.Task):
        client = self.clients[task]

        user_room = None
        for room in self.__rooms:
            if client.nickname in self.__rooms[room]:
                self.__rooms[room].remove(client.nickname)
                break

        self.broadcast_message(
            f"{client.nickname} has left!".encode('utf8'), [client])

        del self.clients[task]
        client.writer.write('quit'.encode('utf8'))
        client.writer.close()
        self.logger.info("End Connection")

    def shutdown_server(self):
        '''
        Shuts down server.
        '''
        self.logger.info("Shutting down server!")
        for client in self.clients.values():
            client.writer.write('quit'.encode('utf8'))
        self.loop.stop()


if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.exit(f"Usage: {sys.argv[0]} HOST_IP PORT")

    loop = asyncio.get_event_loop()
    server = Server(sys.argv[1], sys.argv[2], loop)
    server.start_server()
