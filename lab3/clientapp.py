import asyncio
import tkinter as tk
from tkinter import scrolledtext


async def tk_main(root):
    while True:
        root.update()
        await asyncio.sleep(0.05)


async def send_message(writer, message):
    writer.write(message.encode())
    await writer.drain()
    text_box.insert(tk.END, "\n" + message)


async def receive_messages(reader):
    while True:
        data = await reader.read(100)
        if not data:
            break
        message = data.decode()
        text_box.insert(tk.END, "\n" + message)
        print(message)


async def main(root):
    global writer
    global reader
    reader, writer = await asyncio.open_connection('127.0.0.1', 8888)
    tkmain = asyncio.ensure_future(tk_main(root))
    await receive_messages(reader)


def click():
    asyncio.create_task(send())


async def send():
    message = n.get()
    await send_message(writer, message)
    n.set("")


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x600")
    n = tk.StringVar()
    text_box = scrolledtext.ScrolledText(root,wrap=tk.WORD, width=75, height=36)
    send_entry = tk.Entry(root, textvariable=n)
    buttn = tk.Button(root, command=click, text="send")
    send_entry.grid(row = 10, column=1)
    buttn.grid(row=11, column=1)

    text_box.grid(row=4, column=1)
    asyncio.run(main(root))
