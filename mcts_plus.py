import math
import copy
import numpy as np
import random
from board import Board

'''
此为采用神经网络改进探索策略的蒙特卡洛树搜索
未考虑蒙特卡洛树搜索中对方或者我方连续下棋
'''

def softmax(x):
    probs = x
    probs /= np.sum(probs)
    return probs


class Node_plus(object):
    '''
    建立节点
    '''
    def __init__(self):
        '''
        下棋位置
        '''
        self.color = None
        self.board = Board()
        self.candidate = None
        self.visit = 0
        self.score = 0  #白棋赢为-1分，平为0分，黑棋赢+1分
        self.parent = None
        self.child = []     # 从该结点走过的子结点
        self.childnodes = []    # 从该结点走过的子结点坐标
        self.next_locations = None
        self.status = 0      # 0为未完全扩展 1为完全扩展
        self.prob = 1       # 结点的先验概率
        self.nextlocation_prob = None    #结点可行位置的先验概率
    

class Mcts_plus(object):
    '''
    蒙特卡洛树搜索的实现
    '''
    
    def __init__(self, board, policy_value_function, r, is_selfplay = 0):
        self.color = board.color 
        self.board = copy.deepcopy(board)
        self.r = r    # 为迭代次数
        self.func = policy_value_function
        self.is_selfplay = is_selfplay
        
    def ucb1(self, node, c=1/math.sqrt(2)):   # 查论文似乎有这个c值比较好
        '''
        计算落点取值l，采用神经网络策略后计算公式已经改变
        '''
        l = node.score/node.visit + c*node.prob*math.sqrt(2*node.parent.visit)/(1+node.visit)
        return l
        
    def selection(self, node):
        '''
        选择
        '''
        selection_node = node
        while selection_node.status == 1:
            best_child_value = -float('inf')  # 负无穷
            best_child = None
            for i in range(len(selection_node.child)):
                if self.ucb1(selection_node.child[i]) > best_child_value:
                    best_child_value = self.ucb1(selection_node.child[i])
                    best_child = selection_node.child[i]
            selection_node = best_child
        return selection_node
            
        
    def expand(self, node):
        '''
        对节点进行扩展
        注：因为采用了神经网络，所以扩展前要先进行状态输入
        '''
        no_child_candidates = []
        for i in range(len(node.next_locations)):
            if node.next_locations[i] not in node.childnodes:
                no_child_candidates.append(node.next_locations[i])
                
        if len(no_child_candidates) == 1:
            node.status = 1     # 对状态进行更改
        
        max_candidate_prob = -float('inf') 
        for i in range(len(no_child_candidates)):
            x1 = no_child_candidates[i][0]
            x2 = no_child_candidates[i][1]
            if node.nextlocation_prob[x1][x2] > max_candidate_prob:
                max_candidate_prob = node.nextlocation_prob[x1][x2]
                expand_node_candidate = no_child_candidates[i]

        node.childnodes.append(expand_node_candidate) # 只在childnodes里加了坐标，并未在child增加节点，下面加！
        expand_node = Node_plus()
        if node.parent == None:    # 若为根节点，扩展棋子颜色仍相同
            expand_node.color = self.color
        else:
            if node.color == 'X':
                expand_node.color = 'O'
            else:
                expand_node.color = 'X'
        expand_node.prob = max_candidate_prob
        expand_node.parent = node
        expand_node.candidate = expand_node_candidate
        
        node.child.append(expand_node) # 在child里添加结点 yeah
        return expand_node
 
       
    def simulation(self, node):
        '''
        随机模拟
        我们通过价值网络可以获得该处的value，直接回溯即可，不再需要进行模拟对局
        '''
        board_1 = copy.deepcopy(node.board)
        board_1.locations()
        board_1.pieces_index()        
        node.nextlocation_prob, node.score = self.func(board_1)  # 这里给的是对手局面评分，因此我们要加负号
        node.score = -node.score
        
 
       
    def back_update(self, node):
        '''
        回溯并更新
        '''
        score = node.score
        while node.parent != None:
            node.parent.visit += 1
            score = -score
            node.parent.score += score  
            node = node.parent

            
    def mcts_run(self):  # 若为0 为对战模式，传输action为最大概率
        '''                               #若为1，为自我对抗模式，前30步传输正比概率的action
        进行蒙特卡洛树搜索                                        之后传输带Dirichlet noise的action
        '''
        root = Node_plus()
        root.color = self.color 
        root.board = self.board
        root.board.color = root.color
        root.next_locations = root.board.locations()
        self.simulation(root)
        expand_node = self.expand(root)   # 第一次不进行选择直接扩展
        board_1 = copy.deepcopy(self.board)
        board_1.reversi_pieces(expand_node.candidate)
        expand_node.board = board_1  #对复制棋盘进行第一次扩展翻转
        expand_node.visit = 1
        
        if expand_node.color == 'X':
            expand_node.board.color = 'O'   # 结点对应棋盘为翻转后棋盘，棋盘颜色（此时改下棋色）应与结点颜色相反
            self.simulation(expand_node)
        else:
            expand_node.board.color = 'X'
            self.simulation(expand_node)   
        expand_node.next_locations = expand_node.board.locations()
        expand_node.board.pieces_index()
        if (expand_node.board.black_count+expand_node.board.white_count) == 64:
            if expand_node.color == 'X':
                expand_node.score = expand_node.board.win()
            else:
                expand_node.score = -expand_node.board.win()
        self.back_update(expand_node)
        
        i = 0
        
        while i < self.r and len(expand_node.next_locations) != 0:
            i += 1
            selection_node = self.selection(root)
            expand_node = self.expand(selection_node)              
            board_2 = copy.deepcopy(selection_node.board)
            board_2.reversi_pieces(expand_node.candidate)
            expand_node.board = board_2         
            expand_node.visit = 1
            
            if expand_node.color == 'X':
                expand_node.board.color = 'O'   # 结点对应棋盘为翻转后棋盘，棋盘颜色（此时改下棋色）应与结点颜色相反
                self.simulation(expand_node)         
            else:
                expand_node.board.color = 'X'
                self.simulation(expand_node)   
            expand_node.next_locations = expand_node.board.locations()
            expand_node.board.pieces_index()
            if (expand_node.board.black_count+expand_node.board.white_count) == 64:
                if expand_node.color == 'X':
                    expand_node.score = expand_node.board.win()
                else:
                    expand_node.score = -expand_node.board.win()
            self.back_update(expand_node)
        
        action = None
        max_visit = 0
        mcts_visit = []
        mcts_prob = np.zeros((8, 8))
        if self.is_selfplay == 0:
            for i in range(len(root.child)):
                if root.child[i].visit > max_visit:
                    max_visit = root.child[i].visit
                    action = root.child[i].candidate
                a = root.child[i].candidate[0]
                b = root.child[i].candidate[1]
                mcts_prob[a][b] = root.child[i].visit
                
        else: 
            for i in range(len(root.child)):
                a = root.child[i].candidate[0]
                b = root.child[i].candidate[1]
                mcts_prob[a][b] = root.child[i].visit
                mcts_visit.append(root.child[i].visit)
            mcts_visit = np.array(mcts_visit)
            action_node = random.choices(root.child, 
                                         weights=0.75*mcts_visit+0.25*np.random.dirichlet(0.3*root.visit*np.ones(len(mcts_visit))),
                                         k=1)
            action_node = action_node[0]  # 因为choices后是一个列表
            action = action_node.candidate
        mcts_prob = softmax(mcts_prob)
        
        return action, mcts_prob