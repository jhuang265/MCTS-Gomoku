from __future__ import print_function
from gomoku_env import GomokuEnv
from mcts_self_play import MCTS
import numpy as np

N, Q = 0, 1
CURRENT = 0
OPPONENT = 1
COLOR = 2
BLACK = 1
WHITE = 0
HISTORY = 2
COLUMN = {"a": 0, "b": 1, "c": 2,
          "d": 3, "e": 4, "f": 5,
          "g": 6, "h": 7, "i": 8,
          "j": 9, "k": 10, "l": 11,
          "m": 12, "n": 13, "o": 14,
          "A": 0, "B": 1, "C": 2,
          "D": 3, "E": 4, "F": 5,
          "G": 6, "H": 7, "I": 8,
          "J": 9, "K": 10, "L": 11,
          "M": 12, "N": 13, "O": 14}
BOARD_SIZE = 9  # 9x9 ~ 15x15
N_SIMUL = 50000  # number of simulations for 1 move
GAME = 1


class HumanAgent:
    def get_action(self):
        last_str = str(BOARD_SIZE)
        for k, v in COLUMN.items():
            if v == BOARD_SIZE - 1:
                last_str += k
                break
        move_target = input('1a ~ {}: '.format(last_str)).strip()
        row = int(move_target[:1]) - 1
        col = COLUMN[move_target[1:2]]
        action = row * BOARD_SIZE + col
        return action


class HumanUI:
    def __init__(self):
        self.human = HumanAgent()
        self.ai = MCTS(BOARD_SIZE, HISTORY, N_SIMUL)

    def get_action(self, state, board, idx):
        if idx % 2 == 0:
            action = self.human.get_action()
        else:
            action = self.ai.get_action(state, board)
        return action

def main()
    env = GomokuEnv(BOARD_SIZE, HISTORY)
    manager = HumanUI()
    result = {-1: 0, 0: 0, 1: 0}
    for g in range(GAME):
        print('#####  Game: {}  #####'.format(g + 1))
        state, board = env.reset()
        done = False
        idx = 0
        while not done:
            env.render()
            # start simulations
            action = manager.get_action(state, board, idx)
            state, board, z, done = env.step(action)
            #print(board)
            idx += 1
        if done:
            if z == 1:
                result['Black'] += 1
            elif z == -1:
                result['White'] += 1
            else:
                result['Draw'] += 1
            # render & reset tree
            env.render()
            manager.ai.reset_tree()
        # result
        print('')
        print('=' * 20, " {}  Game End  ".format(g + 1), '=' * 20)
        blw, whw, drw = result['Black'], result['White'], result['Draw']
        stat = (
            'Black Win: {}  White Win: {}  Draw: {}  Winrate: {:0.1f}%'.format(
                blw, whw, drw,
                1 / (1 + np.exp(whw / (g+1)) / np.exp(blw / (g+1))) * 100))
        print(stat, '\n')

if __name__ == '__main__':
    main()
