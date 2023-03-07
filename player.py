from mcts import Mcts
from mcts_plus import Mcts_plus
import random

    
class HumanPlayer():
    '''
    人类玩家
    '''
    
    def move(self, board):
        '''
        玩家下棋
        '''
        
        action = tuple(map(int, input().split()))
        while action not in board.locations():
            print('输入不合法，请重新输入：')
            action = tuple(map(int, input().split()))
        return action

         
class RandomPlayer():
    '''
    随机玩家
    '''
        
    def move(self, board):
        
        random_seed = random.randint (0, len(board.locations())-1)
        action = board.locations()[random_seed]       
        return action
    
class AIPlayer():    # 利用蒙特卡洛树搜索的AI玩家，迭代次数为20次
    '''
    电脑玩家
    '''
    def __init__(self, mcts_n=20):
        self.mcts_n = mcts_n
        
    def move(self, board):
        
        action = Mcts(board, self.mcts_n).mcts_run()
    
        return action
    
class AIPlayerplus():    # 利用结合神经网络的蒙特卡洛树搜索的AI玩家，迭代次数固定为100次
    '''
    超级电脑玩家
    '''
    def __init__(self, policy_value_function, mcts_n=400):
        self.mcts_n = mcts_n
        self.policy_value_function = policy_value_function
        
    def move(self, board):
        '''
        实际用 不传输mcts中数据
        '''
        board.pieces_index()
        
        action1 = Mcts_plus(board, self.policy_value_function, self.mcts_n).mcts_run()
        action = action1[0]
        return action
    
    def move1(self, board):
        '''
        自我对战用 需要传输数据
        '''
        board.pieces_index()

        action = Mcts_plus(board, self.policy_value_function, self.mcts_n, 1).mcts_run()
            
        return action