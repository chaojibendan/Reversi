import math
import copy
import random
from board import Board

'''
未考虑蒙特卡洛树搜索中对方或者我方连续下棋
'''

class Node(object):
    '''
    建立节点
    '''
    def __init__(self):
        '''
        下棋位置
        '''
        self.color = None
        self.board = Board()
        self.coordinate = None
        self.visit = 0
        self.score = 0  #白棋赢为-1分，平为0分，黑棋赢+1分
        self.parent = None
        self.child = []     # 从该结点走过的子结点
        self.childnodes = []    # 从该结点走过的子结点坐标
        self.next_locations = None
        self.status = 0      # 0为未完全扩展 1为完全扩展
    

class Mcts(object):
    '''
    蒙特卡洛树搜索的实现
    '''
    
    def __init__(self, board, r):
        self.color = board.color 
        self.board = copy.deepcopy(board)
        self.r = r    # 为迭代次数
        
    def ucb1(self, node, c=1/math.sqrt(2)):   # 查论文似乎有这个c值比较好
        '''
        计算落点取值l，用ucb1，c为超参数（用来调节好奇心程度）
        '''
        l = node.score/node.visit + c*math.sqrt(2*math.log(node.parent.visit)/node.visit)
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
        '''
        no_child_coordinates = []
        for i in range(len(node.next_locations)):
            if node.next_locations[i] not in node.childnodes:
                no_child_coordinates.append(node.next_locations[i])
                
        if len(no_child_coordinates) == 1:
            node.status = 1     # 对状态进行更改
            
        random_seed = random.randint(0, len(no_child_coordinates)-1)
        expand_node_coordinate = no_child_coordinates[random_seed]
        node.childnodes.append(expand_node_coordinate) # 只在childnodes里加了坐标，并未在child增加节点，下面加！
        expand_node = Node()
        if node.parent == None:    # 若为根节点，扩展棋子颜色仍相同
            expand_node.color = self.color
        else:
            if node.color == 'X':
                expand_node.color = 'O'
            else:
                expand_node.color = 'X'
        expand_node.parent = node
        expand_node.coordinate = expand_node_coordinate
        node.child.append(expand_node) # 在child里添加结点 yeah
        return expand_node
 
       
    def simulation(self, node):
        '''
        随机模拟，注意此时棋盘扩展点已落位，棋盘发生变化，第一落子应为扩展棋子的对手
        '''
        board_1 = copy.deepcopy(node.board)
        switch = 0
        while switch != 2:  # 模拟游戏开始
            if len(board_1.locations()) == 0:
                switch += 1
            else:
                random_seed = random.randint(0, len(board_1.locations())-1)
                board_1.reversi_pieces(board_1.locations()[random_seed])   
                switch = 0
            if board_1.color == 'X':
                board_1.color = 'O'
            else:
                board_1.color = 'X'
        board_1.pieces_index()
        return board_1.win()
 
       
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

            
    def mcts_run(self):
        '''
        进行蒙特卡洛树搜索
        '''
        root = Node()
        root.color = self.color 
        root.board = self.board
        root.board.color = root.color
        root.next_locations = root.board.locations()
        expand_node = self.expand(root)   # 第一次不进行选择直接扩展
        board_1 = copy.deepcopy(self.board)
        board_1.reversi_pieces(expand_node.coordinate)
        expand_node.board = board_1  #对复制棋盘进行第一次扩展翻转
        expand_node.visit = 1
        if expand_node.color == 'X':
            expand_node.board.color = 'O'   # 结点对应棋盘为翻转后棋盘，棋盘颜色（此时改下棋色）应与结点颜色相反
            expand_node.score = self.simulation(expand_node)            
        else:
            expand_node.board.color = 'X'
            expand_node.score = -self.simulation(expand_node)           
        expand_node.next_locations = expand_node.board.locations()
        self.back_update(expand_node)
        
        i = 0
        
        while i < self.r and len(expand_node.next_locations) != 0:
            i += 1
            selection_node = self.selection(root)
            expand_node = self.expand(selection_node)              
            board_2 = copy.deepcopy(selection_node.board)
            board_2.reversi_pieces(expand_node.coordinate)
            expand_node.board = board_2
            
            expand_node.visit = 1
            if expand_node.color == 'X':
                expand_node.board.color = 'O'   # 结点对应棋盘为翻转后棋盘，棋盘颜色（此时改下棋色）应与结点颜色相反
                expand_node.score = self.simulation(expand_node)            
            else:
                expand_node.board.color = 'X'
                expand_node.score = -self.simulation(expand_node)           
            expand_node.next_locations = expand_node.board.locations()
            self.back_update(expand_node)
        
        action = None
        max_visit = 0
        for i in range(len(root.child)):
            if root.child[i].visit > max_visit:
                max_visit = root.child[i].visit
                action = root.child[i].coordinate
        # 走的最多还是胜率最大？我选择走的多
        return action