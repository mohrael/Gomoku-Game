from collections import defaultdict
import random
import time
import re 

class Gomoku:
    def __init__(self):
        self.size = 15
        self.board = [['.' for _ in range(self.size)] for _ in range(self.size)]
        self.ai_player1 = 'O'       #minimax
        self.human_player = 'X'
        self.ai_player2 = 'X'        #alpha beta
        self.max_depth = 3  
        self.winning_length = 5
        
        # 
        self.pattern_scores = {
            # Win/Loss
            'ooooo': 1000000,      # AI win
            'xxxxx': -1000000,     # Human win

            # Open four (must-block or win)
            '.oooo.': 100000,     # AI can win next move
            '.xxxx.': -200000,     # Human can win next move (urgent block)
            'xoooox': -150000,     # Blocked but still dangerous

            # Half-open four (threatening)
            'oooo.': 50000,
            '.oooo': 50000,
            'xxxx.': -75000,       # Higher penalty for human threats
            '.xxxx': -75000,
            'xoooo': 40000,        # Blocked but still strong
            'oooox': 40000,
            'oxxxx': -60000,
            'xxxxo': -60000,

            # Open threes
            '.ooo..': 15000,
            '..ooo.': 15000,
            '.xxx..': -30000,      # Higher penalty
            '..xxx.': -30000,
            'x.xxx.': -25000,
            '.xxx.x': -25000,

            # Split threes
            'oo.oo': 20000,
            'xx.xx': -35000,
            'ooo.o': 18000,
            'xxx.x': -30000,
            'o.ooo': 18000,
            'x.xxx': -30000,

            # Open twos
            '.oo..': 5000,
            '..oo.': 5000,
            '.xx..': -10000,
            '..xx.': -10000,
            'x.xx.': -8000,
            '.xx.x': -8000,

            # Center control bonus (special case)
            'center': 500,
            
            # Corner control bonus
            'corner': 200
        }





    def print_board(self):
        # This line prints the column numbers (headers) with 2-space width for alignment.
        print("   " + " ".join(f"{i:2}" for i in range(self.size)))
        for i, row in enumerate(self.board):
            print(f"{i:2} " + " ".join(f"{cell:2}" for cell in row))

    def available_moves(self):

          # Check immediate wins/blocks first
        for player in [self.ai_player1, self.ai_player2, self.human_player]:
            for row in range(self.size):
                for col in range(self.size):
                    if self.board[row][col] == '.':
                        self.board[row][col] = player
                        if self.check_winner() == player:
                            self.board[row][col] = '.'
                            return [(row, col)]
                        self.board[row][col] = '.'
        moves = set()
    # Get moves near existing pieces
        occupied = [(r, c) for r in range(self.size) 
                           for c in range(self.size) if self.board[r][c] != '.']
        
        if not occupied:
                    center = self.size // 2
                    if self.board[center][center] == '.':
                       return [(center, center)]
                    
        # It checks if the human player has a threat (e.g. 4 in a row).
        # If so, it finds blocking moves and immediately returns them — defensive priority
        # Prioritize areas with human threats
        human_threats = self.detect_threats(self.human_player)
        if human_threats:
            blocking_moves = self.get_blocking_moves(human_threats)
            if blocking_moves:
                return blocking_moves

        
        # Also consider AI's own threats
        ai_threats = self.detect_threats(self.ai_player1)
        if ai_threats:
            attacking_moves = self.get_blocking_moves(ai_threats)
            if attacking_moves:
                moves.update(attacking_moves)


        #Add moves near existing pieces
        for (row, col) in occupied:
           for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue     
                    r, c = row + dr, col + dc
                    if 0 <= r < self.size and 0 <= c < self.size and self.board[r][c] == '.':
                        moves.add((r, c))

        return list(moves) if moves else \
                [(r, c) for r in range(self.size) 
                        for c in range(self.size) if self.board[r][c] == '.']

            

    def make_move(self, row, col, player):
        if 0 <= row < self.size and 0 <= col < self.size and self.board[row][col] == '.':
            self.board[row][col] = player
            return True
        return False

    def is_board_full(self):
        return all('.' not in row for row in self.board)

    def check_winner(self):
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        
        for row in range(self.size):
            for col in range(self.size):
                if self.board[row][col] != '.':
                    player = self.board[row][col]
                    for dr, dc in directions:
                        count = 1
                        for i in range(1, self.winning_length):
                            r, c = row + dr * i, col + dc * i
                            if 0 <= r < self.size and 0 <= c < self.size and self.board[r][c] == player:
                                count += 1
                            else:
                                break
                        if count >= self.winning_length:
                            return player
        return None
    def game_over(self):
        return self.check_winner() is not None or self.is_board_full()

    
    def evaluate_board(self):
        total_score = 0

        # Get all lines (rows, cols, diagonals)
        lines = []
        corners = [(0,0), (0,self.size-1), (self.size-1,0), (self.size-1,self.size-1)]

        # Center bonus
        center = self.size // 2
        for row in range(self.size):
            for col in range(self.size):
                piece = self.board[row][col]
                if piece == self.ai_player1:  # AI piece
                    dist = abs(center - row) + abs(center - col)
                    # rewards the AI for placing pieces closer to the center.
                    total_score += self.pattern_scores.get('center', 0) - dist * 10
                
                # Corner control
                if (row, col) in corners:
                    total_score += self.pattern_scores.get('corner', 0)


        # Rows
        for row in self.board:
            lines.append(''.join(row))

        # Columns
        for col in range(self.size):
            line = ''.join(self.board[row][col] for row in range(self.size))
            lines.append(line)

        # Diagonals
        for i in range(-self.size + 1, self.size):
            diag1 = ''.join(self.board[i + j][j] for j in range(self.size)
                            if 0 <= i + j < self.size and 0 <= j < self.size)
            diag2 = ''.join(self.board[i + j][self.size - 1 - j] for j in range(self.size)
                            if 0 <= i + j < self.size and 0 <= j < self.size)
            lines.extend([diag1, diag2])


        full_board_string = ''.join(lines)
        if 'ooooo' in full_board_string:
            return 1_000_000
        if 'xxxxx' in full_board_string:
            return -1_000_000

        # Pattern scoring
        for line in lines:
            for pattern, value in self.pattern_scores.items():
                        if pattern == 'center':
                            continue  # Skip 'center' here, it’s handled separately
                        count = len(re.findall(f'(?={pattern})', line))
                        total_score += count * value    
           
        # Additional defensive consideration - count human threats
        human_threats = self.detect_threats(self.human_player)
        for threat in human_threats:
            if threat['length'] >= 3:
                total_score -= 50000 * threat['length']  # Big penalty for human threats
            elif threat['length'] == 2 and threat['open_ends'] == 2:
                total_score -= 20000  # Penalty for open two


        return total_score

    
    def undo_move(self, row,col):
        # row, col = move
        self.board[row][col] = '.'

    def Alpha_Beta_pruning(self, depth, is_maximizing,alpha,beta):
        if depth == 0 or self.game_over():
            return self.evaluate_board()
        
        player = self.ai_player1 if is_maximizing else self.ai_player2
        best_score = float('-inf') if is_maximizing else float('inf')
        
        for row, col in self.available_moves():
            self.make_move(row,col,player)
            # self.board[row][col] = player
            score = self.Alpha_Beta_pruning(depth-1, alpha, beta, not is_maximizing)
            # self.board[row][col] = '.'
            self.undo_move(row,col)
            if is_maximizing:
                best_score = max(score, best_score)
                alpha = max(alpha, best_score)
            else:
                best_score = min(score, best_score)
                beta = min(beta, best_score)
            
            if alpha >= beta:
                break
                
        return best_score
    

    def minimax(self, depth, is_maximizing):
        if depth == 0 or self.game_over():
            return self.evaluate_board()
        
        moves = self.available_moves()
        
        if is_maximizing:
            best_score = float('-inf')
            for row, col in moves:
                self.board[row][col] = self.ai_player1
                score = self.minimax(depth - 1, False)
                self.board[row][col] = '.'
                best_score = max(score, best_score)
            return best_score
        else:
            best_score = float('inf')
            for row, col in moves:
                self.board[row][col] = self.human_player
                score = self.minimax(depth - 1, True)
                self.board[row][col] = '.'
                best_score = min(score, best_score)
            return best_score

    
    def get_ai_move(self,use_alphabeta=True):
        # First check for immediate wins/blocks
        moves = self.available_moves()
        if len(moves) == 1:
            return moves[0]
        
        # Try center first if empty
        center = self.size // 2
        if self.board[center][center] == '.':
            return (center, center)
        
        # Limit number of moves to evaluate
        max_moves_to_consider = 20
        if len(moves) > max_moves_to_consider:
            moves = random.sample(moves, max_moves_to_consider)
        
        best_score = float('-inf')
        best_move = None  
        alpha = float('-inf')
        beta = float('inf')

        for row, col in moves:
            self.board[row][col] = self.ai_player1
            if(use_alphabeta):
                score = self.Alpha_Beta_pruning(self.max_depth-1 ,False, alpha , beta)
            else:    
                score = self.minimax(self.max_depth - 1, False)
            self.board[row][col] = '.'
            
            if score > best_score:
                best_score = score
                best_move = (row, col)
                # Early exit if found winning move
                if score == float('inf'):
                    break
            alpha = max(alpha, best_score)
            if alpha >= beta and use_alphabeta:
                break

        return best_move or random.choice(moves)


   
    def choose_first_player(self):
        choice = input("Do you want to go first? (y/n): ").lower()
        return choice == 'y'

    def choose_game_option(self):
        while True:
            choice = input("Do you want AI vs. Human or AI vs. AI ? (1/2): ").strip()
            if choice == '1':
                return True
            elif choice == '2':
                return False
            else:
                print("Invalid option. Try again.")


    def detect_threats(self, player):
        """Detect all potential threats for the given player"""
        threats = []
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        
        for row in range(self.size):
            for col in range(self.size):
                if self.board[row][col] == player:
                    for di, dj in directions:
                        # To avoid duplicate detection
                        # Look at the cell just before the current one in the given direction.
                        prev_i, prev_j = row - di, col - dj
                        # If that previous cell is also the player's, we've already processed this sequence before — so skip it (to avoid duplication).
                        if 0 <= prev_i < self.size and 0 <= prev_j < self.size and self.board[prev_i][prev_j] == player:
                            continue
                        
                        length = 1
                        ni, nj = row + di, col + dj
                        while 0 <= ni < self.size and 0 <= nj < self.size and self.board[ni][nj] == player:
                            length += 1
                            ni += di
                            nj += dj
                        
                        # at least 2 in row
                        if length >= 2:  # Only consider sequences of 2 or more
                            open_ends = 0
                            
                            # Check start of sequence
                            start_i, start_j = row - di, col - dj
                            if 0 <= start_i < self.size and 0 <= start_j < self.size and self.board[start_i][start_j] == '.':
                                open_ends += 1
                            
                            # Check end of sequence
                            end_i, end_j = row + di * length, col + dj * length
                            if 0 <= end_i < self.size and 0 <= end_j < self.size and self.board[end_i][end_j] == '.':
                                open_ends += 1
                            
                            if open_ends > 0:  # Only consider threats that can be extended
                                threats.append({
                                    'type': 'horizontal' if (di, dj) == (0, 1) else 
                                           'vertical' if (di, dj) == (1, 0) else
                                           'diagonal_down' if (di, dj) == (1, 1) else
                                           'diagonal_up',
                                    'start_row': row,
                                    'start_col': col,
                                    'length': length,
                                    'open_ends': open_ends,
                                    'direction': (di, dj)
                                })
        # length: the number of consecutive pieces
        # open_ends: how many sides are open (can be extended).
        # two threats are equal in length, we prefer the one with more open ends

        # Sort threats by length and open ends
        threats.sort(key=lambda x: (-x['length'], -x['open_ends']))
        return threats

    def get_blocking_moves(self, threats):
        # best moves to block 
        """Get the best blocking/attacking moves for given threats"""
        blocking_moves = []
        # maps each move position to its threat score.
        # defaultdict sets it to 0
        move_scores = defaultdict(int)
        
        for threat in threats:
            di, dj = threat['direction']
            row, col = threat['start_row'], threat['start_col']
            length = threat['length']
            
            # Score based on threat severity
            threat_score = 10 ** (threat['length'] + threat['open_ends'])
            
            # Check before the sequence
            # If the cell before the sequence is empty, it's a good move to block or extend → add its score.
            before_i, before_j = row - di, col - dj
            if 0 <= before_i < self.size and 0 <= before_j < self.size and self.board[before_i][before_j] == '.':
                move_scores[(before_i, before_j)] += threat_score
            
            # Check after the sequence
            after_i, after_j = row + di * length, col + dj * length
            if 0 <= after_i < self.size and 0 <= after_j < self.size and self.board[after_i][after_j] == '.':
                move_scores[(after_i, after_j)] += threat_score
        
        # Choose all moves with the highest score — these are the most urgent or useful.
        if move_scores:
            max_score = max(move_scores.values())
            return [move for move, score in move_scores.items() if score == max_score]
        return []



    def play_game(self):
        choise=self.choose_game_option()
        if(choise):
            human_turn = self.choose_first_player()
            print(f"You are '{self.human_player}'. AI is '{self.ai_player1}'.")
            self.print_board()
            while not self.game_over():
                if human_turn:
                    while True:
                        try:
                            row, col = map(int, input("Your move (row col): ").split())
                            if self.make_move(row, col, self.human_player):
                                break
                            print("Invalid move. Try again.")
                        except ValueError:
                            print("Enter two numbers separated by space.")
                else:
                    print("\nAI's turn...")
                    start_time = time.time()
                    row, col = self.get_ai_move(False)
                    self.make_move(row, col, self.ai_player1)
                    print(f"AI moved to ({row}, {col}) in {time.time()-start_time:.2f}s")
                
                self.print_board()
                human_turn = not human_turn

            winner = self.check_winner()
            if winner == self.ai_player1:
                print("\nAI wins!")
            elif winner == self.human_player:
                print("\nYou win! Congratulations!")
            else:
                print("\nIt's a tie!")
        
        
        else:
            print(f" player 1: AI(Alpha-Beta pruning algorithm) '{self.ai_player2}' . Player 2: AI(Minimax algorithm) '{self.ai_player1}' .")
            self.print_board()
            current_ai = 'alphabeta'  # Alternate who goes first
            while not self.game_over():
                if current_ai == 'alphabeta':
                    print("\n Player1's turn...")
                    start_time = time.time()
                    row, col = self.get_ai_move(True)
                    self.make_move(row, col, self.ai_player2)
                    print(f"AlphaBeta (X) moved to ({row}, {col}) in {time.time()-start_time:.2f}s")
                    current_ai = 'minimax'
                
                elif current_ai == 'minimax':
                    print("\n Player2's turn...")
                    start_time = time.time()
                    row, col = self.get_ai_move(False)
                    self.make_move(row, col, self.ai_player1)
                    print(f"Minimax (O) moved to ({row}, {col}) in {time.time()-start_time:.2f}s")
                    current_ai = 'alphabeta'
                self.print_board()

            winner = self.check_winner()
            if winner == self.ai_player1:
                print("\nMinimax (O) wins!")
            elif winner == self.ai_player2:
                print("\nAlphaBeta (X) wins!")
            else:
                print("\nIt's a tie!")



if __name__ == "__main__":
    game = Gomoku()
    game.play_game()        
