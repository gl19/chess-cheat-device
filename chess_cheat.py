import socket
from collections import deque
import tkinter as tk
from tkinter import messagebox
import chess
import chess.svg
from stockfish import Stockfish
from svglib.svglib import svg2rlg
from PIL import ImageTk
from reportlab.graphics import renderPDF
import pypdfium2 as pdfium
import time


BOARD_HEIGHT = 27
BOARD_WIDTH = 49
# Change to stockfish executable location
STOCKFISH_DIR = r"stockfish\\stockfish_15_x64_avx2.exe"
# Change this to depending on computer performance and speed needed
EVAL_DEPTH = 20

# Change IP and socket depending on the configuration of the pi
PI_IP = ''
SOCKET = 8080


def get_best_moves(window, fish):
    best_move = fish.get_top_moves(3)
    formatted_moves = "Move\tCentipawn\n"
    for v in best_move:
        formatted_moves += v["Move"] + "\t" + str(v["Centipawn"]) + "\n"

    window.move.delete("1.0", tk.END)
    window.move.insert("1.0", formatted_moves)


def display_board(window, fish):
    is_flipped = window.getvar(name="flip")
    board = chess.Board(fish.get_fen_position())
    board_svg = chess.svg.board(board, flipped=is_flipped)

    f = open("board.svg", "w")
    f.write(board_svg)
    f.close()

    drawing = svg2rlg("board.svg")
    renderPDF.drawToFile(drawing, "board.pdf")
    pages = pdfium.PdfDocument("board.pdf")
    page = pages.get_page(0)
    pil_image = page.render_topil()
    board_image = ImageTk.PhotoImage(pil_image)
    window.board.configure(image=board_image)
    window.board.image = board_image


def undo_move(window, fish):
    if window.history:
        fen = window.history.pop()
        fish.set_fen_position(fen, False)
        display_board(window, fish)


def send_move(window, socket, fish):
    move = window.send_entry.get()
    if fish.is_move_correct(move):
        window.status.configure(text="Move correct")
        window.send_entry.delete(0, "end")
        socket.send(move.encode())
    else:
        window.status.configure(text="Move is not valid!")


def make_move(window, fish):
    move = window.move_entry.get()
    if fish.is_move_correct(move):
        window.history.append(fish.get_fen_position())
        fish.make_moves_from_current_position([move])
        display_board(window, fish)
        clear_text(window)


def clear_text(window):
    window.move_entry.delete(0, "end")
    window.move.delete("1.0", "end")


def flip_board(window, fish):
    window.setvar(name="flip", value=not window.getvar(name="flip"))
    display_board(window, fish)


def setup_socket():
    client_socket = socket.socket()
    try:
        client_socket.connect((PI_IP, SOCKET))
        print("Connection success!")
        return client_socket
    except ConnectionError:
        print("Failed to connect to pi!")
        return False


def attempt_pi_connection():
    while True:
        socket = setup_socket()
        if socket:
            break

        print("Reconnecting in 5 seconds...")
        time.sleep(5)

    return socket

def init_window(fish, socket):
    window = tk.Tk()
    window.title("Chess Cheat")
    window.minsize(300, 300)
    window.setvar(name="flip", value=False)
    window.history = deque()

    flip = tk.Button(
        window, text="Flip Board", command=lambda: flip_board(window, fish)
    )
    undo = tk.Button(window, text="Undo", command=lambda: undo_move(window, fish))
    reset = tk.Button(window, text="Reset", command=lambda: reset_game(window, fish))
    window.move_entry = tk.Entry()
    evaluate = tk.Button(
        window, text="Evaluate", command=lambda: get_best_moves(window, fish)
    )
    make = tk.Button(window, text="Make Move", command=lambda: make_move(window, fish))
    window.move = tk.Text()
    window.move.config(width=18, height=4)
    window.send_entry = tk.Entry()
    send = tk.Button(
        window, text="Send Move", command=lambda: send_move(window, socket, fish)
    )
    window.status = tk.Label(window)

    pages = pdfium.PdfDocument("begin_board.pdf")
    page = pages.get_page(0)
    pil_image = page.render_topil()
    board_image = ImageTk.PhotoImage(pil_image)
    window.board = tk.Label(window, image=board_image)
    window.board.image = board_image

    window.board.grid(row=1, column=2, rowspan=25, columnspan=3)
    flip.grid(row=26, column=2)
    undo.grid(row=26, column=3)
    reset.grid(row=26, column=4)
    window.move_entry.grid(row=4, column=1)
    make.grid(row=5, column=1)
    evaluate.grid(row=6, column=1)
    window.move.grid(row=7, column=1)
    window.send_entry.grid(row=8, column=1)
    send.grid(row=9, column=1)
    window.status.grid(row=10, column=1)

    return window


def reset_game(window, fish):
    fish.set_position()
    display_board(window, fish)
    window.history.clear()
    clear_text(window)


def on_closing(window, socket):
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        socket.close()
        window.destroy()


def create_fish():
    fish = Stockfish(STOCKFISH_DIR)
    # Other settings can be set here
    # For example:
    # fish.update_engine_parameters(
	# 	{
	# 		"Threads": 3,
	# 		'Skill Level': 11,
	# 		'Minimum Thinking Time': 0,
	# 		'Slow Mover': 0,
	# 		'Hash': 12
	# 	}
	# )

    fish.set_depth(EVAL_DEPTH)
    return fish


def main():
    fish = create_fish()
    socket = attempt_pi_connection()
    window = init_window(fish, socket)
    window.protocol("WM_DELETE_WINDOW", lambda: on_closing(window, socket))
    window.mainloop()


if __name__ == "__main__":
    main()
