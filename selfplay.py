from player import AIPlayer, RandomPlayer, AIPlayerplus
from game import Game
from board import Board
import time
from policy_value_net import PolicyValueNet
policy_value_net = PolicyValueNet(model_file='./current_policy.model')

from multiprocessing import Pool, Queue, Process
from threading import Thread

'''
请分开测试！用来测试selfplay如何速度最快，后来我们都会采用多进程队列去加速！
'''



black_player = AIPlayerplus(policy_value_net.policy_value_fn, 100)
# black_player = AIPlayerplus(100)
white_player = AIPlayer(100)

n = 10   # 对战次数


# # 普通运行模式

# black_win = 0   # 黑棋获胜数
# white_win = 0   # 白棋获胜数

# start1 = time.time()

# for i in range(n):
#     game = Game(black_player, white_player)
#     game.selfplay_run()
#     if game.board.win() == 1:
#         black_win += 1
#     elif game.board.win() == -1:
#         white_win += 1
#     else:
#         pass
    
# print('黑棋获胜：', black_win)
# print('白棋获胜：', white_win)

# end1 = time.time()

# print('普通运行时间：', end1-start1)



# # 多线程运行模式

# black_win = 0   # 黑棋获胜数
# white_win = 0   # 白棋获胜数

# start2 = time.time()


# for i in range(n):
#     game = Game(black_player, white_player)
#     t = Thread(target=game.selfplay_run())
#     t.start()
#     if game.board.win() == 1:
#         black_win += 1
#     elif game.board.win() == -1:
#         white_win += 1
#     else:
#         pass
    
 
    
# print('黑棋获胜：', black_win)
# print('白棋获胜：', white_win)

# end2 = time.time()

# print('多线程运行时间：', end2-start2)


# # 多进程池

# black_win = 0   # 黑棋获胜数
# white_win = 0   # 白棋获胜数


# if __name__ == '__main__':
    
#     start3 = time.time()
    
#     pool = Pool(2)      # 进程数
    
#     for i in range(n):
#         game = Game(black_player, white_player)
#         pool.apply_async(game.board.win())
#         if game.game_result() == 1:
#             black_win += 1
#         elif game.game_result() == -1:
#             white_win += 1
#         else:
#             pass
    
        
#     print('黑棋获胜：', black_win)
#     print('白棋获胜：', white_win)
    
#     end3 = time.time()
    
#     print('多进程池运行时间：', end3-start3)



# 多进程队列

black_win = 0   # 黑棋获胜数
white_win = 0   # 白棋获胜数

ps_num = 5      # 进程数
chunk_size = n//ps_num   # 每个进程分的对抗数
n_list = range(n)   


def chunk_gamerun(res_queue, start_index, end_index):
    '''
    将每个进程分配游戏入队
    '''
    for game_index in n_list[start_index:end_index]:
        
        game = Game(black_player, white_player)
        game.selfplay_run()
        res_queue.put(game.board.win())       # 实际进入队列的是游戏结果
        
        

if __name__ == '__main__':       


    res_queue = Queue()     # 进程队列
    task_list = []      # 进程列表
    
    
    for i in range(ps_num):    # 确定分的位置
        s_index = i * chunk_size
        if i == ps_num - 1:
            e_index = n
        else:
            e_index = s_index + chunk_size                  
        p_task = Process(target=chunk_gamerun, args=(res_queue,s_index,e_index))  # 每个进程包含数个相同数目任务
        task_list.append(p_task)
        p_task.start()

    get_queue_num = 0
    
    while True:          # 获取队列信息
        res_game = res_queue.get()
        if res_game == 1:
            black_win += 1
        elif res_game == -1:
            white_win +=1
        get_queue_num += 1
        if get_queue_num == n:
            break
    
    time.sleep(5)    # 必要！ 因为第一个进程可能还未入队导致子程序在主程序后运行！
    
    for task in task_list:
        task.join()
        
        
    print('黑棋获胜：', black_win)
    print('白棋获胜：', white_win)