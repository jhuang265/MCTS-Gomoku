# Monte Carlo Tree Search based on Two Player UCT in Gomoku environment

from __future__ import print_function
from gomoku_env import GomokuEnv

import time
import sys
from collections import deque, defaultdict
from pathos.multiprocessing import ProcessPool

import numpy as np
from numpy import random
from numba import jit

N, Q = 0, 1
CURRENT = 0
OPPONENT = 1
COLOR = 2
BLACK = 1
WHITE = 0
BOARD_SIZE = 9
HISTORY = 2

SIMULATIONS = BOARD_SIZE**2 * 10
GAME = 1


class MCTS:
    @jit
    def __init__(self, n_simul, board_size, n_history):
        self.env_simul = GomokuEnv(board_size, n_history, display=false)
        self.n_simul = n_simul
        self.board_size = board_size
        self.tree = None
        self.root = None
        self.state = None
        self.board = None
        self.legal_move = None
        self.no_legal_move = None
        self.ucb = None

        # used for backup
        self.key_memory = None
        self.action_memory = None

        # init
        self._reset()
        self.reset_tree()

    @jit
    def _reset(self):
        self.key_memory = deque(maxlen=self.board_size**2)
        self.action_memory = deque(maxlen=self.board_size**2)

    def reset_tree(self):
        self.tree = defaultdict(lambda: np.zeros((self.board_size**2, 2), 'float'))

    @jit
    def get_action(self, state, board):
        self.root = state.copy()
        self._simulation(state)
        # init the root board after simulation
        self.board = board
        #self.board = self.root.reshape(3, BOARD_SIZE**2)
        board_fill = self.board[CURRENT] + self.board[OPPONENT]
        self.legal_move = np.argwhere(board_fill == 0).flatten()
        self.no_legal_move = np.argwhere(board_fill != 0).flatten()
        # root state's key
        root_key = hash(self.root.tostring())
        # argmax Q
        action = self._selection(root_key, c_ucb=0)
        print('')
        print(self.ucb.reshape(self.board_size, self.board_size).round(decimals=4))
        return action

    @jit
    def _simulation(self, state):
        start = time.time()
        reward = 0
        sim = 0
        print('Computing Moves', end='')
        sys.stdout.flush()
        for sim in range(self.n_simul):
            if (sim + 1) % (self.n_simul / 10) == 0:
                print('.', end='')
                sys.stdout.flush()
            # reset state
            self.state, self.board = self.env_simul.reset(state)
            done = False
            n_selection = 0
            n_expansion = 0
            while not done:
                # init board
                # self.board = self.state.reshape(3, BOARD_SIZE**2)
                board_fill = self.board[CURRENT] + self.board[OPPONENT]
                self.legal_move = np.argwhere(board_fill == 0).flatten()
                self.no_legal_move = np.argwhere(board_fill != 0).flatten()
                key = hash(self.state.tostring())
                # search the tree
                if key in self.tree:
                    # selection
                    action = self._selection(key, c_ucb=1)
                    self.action_memory.appendleft(action)
                    self.key_memory.appendleft(key)
                    n_selection += 1
                elif n_expansion == 0:
                    # expansion
                    action = self._expansion(key)
                    self.action_memory.appendleft(action)
                    self.key_memory.appendleft(key)
                    n_expansion += 1
                else:
                    # rollout
                    action = random.choice(self.legal_move)
                self.state, self.board, reward, done = self.env_simul.step(action)
            if done:
                # backup & reset memory
                self._backup(reward, n_selection + n_expansion)
                self._reset()
        finish = round(time.time() - start)
        print('\n"{} Simulations End in {}s"'.format(sim + 1, finish))

    @jit
    def _selection(self, key, c_ucb):
        edges = self.tree[key]
        # get ucb
        ucb = self._ucb(edges, c_ucb)
        self.ucb = ucb
        if self.board[COLOR][0] == WHITE:
            # black's selection
            action = np.argwhere(ucb == ucb.max()).flatten()
        else:
            # white's selection
            action = np.argwhere(ucb == ucb.min()).flatten()
        action = action[random.choice(len(action))]
        return action

    @jit
    def _expansion(self, key):
        # only select once for rollout
        action = self._selection(key, c_ucb=1)
        return action

    @jit
    def _ucb(self, edges, c_ucb):
        total_N = 0
        ucb = np.zeros((self.board_size**2), 'float')
        for i in range(self.board_size**2):
            total_N += edges[i][N]
        # black's UCB
        if self.board[COLOR][0] == WHITE:
            for move in self.legal_move:
                if edges[move][N] != 0:
                    ucb[move] = edges[move][Q] + c_ucb * \
                        np.sqrt(2 * np.log(total_N) / edges[move][N])
                else:
                    ucb[move] = np.inf
            for move in self.no_legal_move:
                ucb[move] = -np.inf
        # white's UCB
        else:
            for move in self.legal_move:
                if edges[move][N] != 0:
                    ucb[move] = edges[move][Q] - c_ucb * \
                        np.sqrt(2 * np.log(total_N) / edges[move][N])
                else:
                    ucb[move] = -np.inf
            for move in self.no_legal_move:
                ucb[move] = np.inf
        return ucb

    @jit
    def _backup(self, reward, steps):
        # steps = n_selection + n_expansion
        # update the edges in the tree
        for i in range(steps):
            edges = self.tree[self.key_memory[i]]
            action = self.action_memory[i]
            edges[action][N] += 1
            edges[action][Q] += (reward - edges[action][Q]) / edges[action][N]

@jit
def play():
    env = GomokuEnv(BOARD_SIZE, HISTORY)
    mcts = MCTS(SIMULATIONS, BOARD_SIZE, HISTORY)
    pool = ProcessPool(nodes=4)
    result = {'Black': 0, 'White': 0, 'Draw': 0}
    for g in range(GAME):
        print('#' * (BOARD_SIZE - 4), ' GAME: {} '.format(g + 1), '#' * (BOARD_SIZE - 4))
        # reset state
        state, board = env.reset()
        done = False
        while not done:
            env.render()
            # start simulation
            # action = mcts.get_action(state)
            action = pool.map(mcts.get_action, [state])
            state, board, z, done = env.step(action)
        if done:
            if z == 1:
                result['Black'] += 1
            elif z == -1:
                result['White'] += 1
            else:
                result['Draw'] += 1
            # render & reset tree
            env.render()
            mcts.reset_tree()
        # print the result
        print('')
        print('=' * 20, " {}  Game End  ".format(g + 1), '=' * 20)
        blw, whw, drw = result['Black'], result['White'], result['Draw']
        stat = ('Black Win: {}  White Win: {}  Draw: {}  Winrate: {:0.1f}%'.format(
            blw, whw, drw, 1 / (1 + np.exp(whw / (g + 1)) / np.exp(blw / (g + 1))) * 100))
        print(stat, '\n')


if __name__ == '__main__':
    play()
