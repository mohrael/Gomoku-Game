import tkinter as tk
from tkinter import messagebox
import threading
import time

from Gomoku import Gomoku  # Assume your logic is saved in gomoku_core.py

class GomokuGUI:
    def __init__(self, root):
        self.root = root
        self.game = Gomoku()
        self.cell_size = 30
        self.margin = 20
        self.canvas_size = self.cell_size * self.game.size + 2 * self.margin
        self.mode = None  # 'ai_vs_ai' or 'human_vs_ai'
        self.human_turn = True
        self.create_start_menu()

    def create_start_menu(self):
        self.clear_root()

        label = tk.Label(self.root, text="Choose Game Mode", font=("Arial", 16))
        label.pack(pady=20)

        btn1 = tk.Button(self.root, text="Human vs AI", font=("Arial", 14),
                         command=lambda: self.start_game("human_vs_ai"))
        btn1.pack(pady=10)

        btn2 = tk.Button(self.root, text="AI vs AI", font=("Arial", 14),
                         command=lambda: self.start_game("ai_vs_ai"))
        btn2.pack(pady=10)

    def start_game(self, mode):
        self.mode = mode
        self.clear_root()

        self.canvas = tk.Canvas(self.root, width=self.canvas_size, height=self.canvas_size, bg='#ffe6ff')
        self.canvas.pack()

        # 🎯 Add Restart Button
        restart_btn = tk.Button(self.root, text="Restart Game", font=("Arial", 12), command=self.restart_game)
        restart_btn.pack(pady=10)

        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.draw_board()

        if mode == 'ai_vs_ai':
            threading.Thread(target=self.ai_vs_ai_loop, daemon=True).start()

    def draw_board(self):
        self.canvas.delete("all")
        for i in range(self.game.size):
            x0 = self.margin
            x1 = self.canvas_size - self.margin
            y = self.margin + i * self.cell_size
            self.canvas.create_line(x0, y, x1, y)

            y0 = self.margin
            y1 = self.canvas_size - self.margin
            x = self.margin + i * self.cell_size
            self.canvas.create_line(x, y0, x, y1)

        for r in range(self.game.size):
            for c in range(self.game.size):
                piece = self.game.board[r][c]
                if piece != '.':
                    x = self.margin + c * self.cell_size
                    y = self.margin + r * self.cell_size
                    color = 'black' if piece == 'X' else 'white'
                    self.canvas.create_oval(x - 10, y - 10, x + 10, y + 10, fill=color)

    def on_canvas_click(self, event):
        if self.mode != 'human_vs_ai' or not self.human_turn or self.game.game_over():
            return

        col = (event.x - self.margin) // self.cell_size
        row = (event.y - self.margin) // self.cell_size

        if self.game.make_move(row, col, self.game.human_player):
            self.human_turn = False
            self.draw_board()
            self.check_game_end()

            threading.Thread(target=self.ai_move_after_human, daemon=True).start()

    def ai_move_after_human(self):
        time.sleep(0.5)
        if self.game.game_over():
            return
        row, col = self.game.get_ai_move(False)
        self.game.make_move(row, col, self.game.ai_player1)
        self.draw_board()
        self.check_game_end()
        self.human_turn = True

    def ai_vs_ai_loop(self):
        current_ai = 'alphabeta'
        while not self.game.game_over():
            time.sleep(0.5)
            if current_ai == 'alphabeta':
                row, col = self.game.get_ai_move(True)
                self.game.make_move(row, col, self.game.ai_player2)
                current_ai = 'minimax'
            else:
                row, col = self.game.get_ai_move(False)
                self.game.make_move(row, col, self.game.ai_player1)
                current_ai = 'alphabeta'
            self.draw_board()
        self.check_game_end()

    def check_game_end(self):
        if self.game.game_over():
            winner = self.game.check_winner()

            if self.mode == 'human_vs_ai':
                if winner == self.game.human_player:
                    messagebox.showinfo("Game Over", "You win!")
                elif winner == self.game.ai_player1:
                    messagebox.showinfo("Game Over", "AI wins!")
                else:
                    messagebox.showinfo("Game Over", "It's a tie!")
            else:  # AI vs AI
                if winner == self.game.ai_player1:
                    messagebox.showinfo("Game Over", "AI (Minimax) wins!")
                elif winner == self.game.ai_player2:
                    messagebox.showinfo("Game Over", "AI (Alpha-Beta) wins!")
                else:
                    messagebox.showinfo("Game Over", "It's a tie!")

    def clear_root(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def restart_game(self):
        if messagebox.askyesno("Restart", "Are you sure you want to restart?"):
            self.game = Gomoku()
            self.human_turn = True
            self.create_start_menu()


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Gomoku")
    gui = GomokuGUI(root)
    root.mainloop()
