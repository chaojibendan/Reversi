import random
import numpy as np
from collections import defaultdict, deque
from game import Game
from player import AIPlayerplus, AIPlayer
from policy_value_net import PolicyValueNet  # Pytorch

class TrainPipeline():
    def __init__(self, init_model=None):
        # 训练参数
        self.learn_rate = 1e-4
        self.lr_multiplier = 1  # 自适应调节学习率
        self.batch_size = 512  # mini-batch size
        self.epochs = 5  # 每次更新训练次数
        self.check_freq = 50 # 每50次就与纯mcts进行对战查看情况
        self.buffer_size = 10000
        self.data_buffer = deque(maxlen=self.buffer_size)
        self.game_batch_num = 2000
        self.play_batch_size = 2
        self.kl_targ = 0.01
        self.best_win_ratio = 0.0
        self.AIPlayerplus_num = 1000      # mcts升级版玩家搜索次数
        self.AIPlayer_num = 100      # 纯mcts玩家搜索次数
        if init_model:
            # 从初始策略价值网络开始学习
            self.policy_value_net = PolicyValueNet(model_file=init_model)
        else:
            # 从一个新的策略网络开始学习
            self.policy_value_net = PolicyValueNet()
            
        self.AIPlayerplus = AIPlayerplus(self.policy_value_net)

    def get_equi_data(self, play_data):
        '''
        将棋盘翻转和取镜像来获得更多对抗数据
        '''
        extend_data = []
        for state, mcts_prob, winner in play_data:
            for i in [1, 2, 3, 4]:
                # 逆时针旋转90度
                equi_state = np.array([np.rot90(s, i) for s in state])
                equi_mcts_prob = np.rot90(mcts_prob, i)
                extend_data.append((equi_state, equi_mcts_prob, winner))
                # 水平翻转
                equi_state = np.array([np.fliplr(s) for s in equi_state])
                equi_mcts_prob = np.fliplr(equi_mcts_prob)
                extend_data.append((equi_state, equi_mcts_prob, winner))
        return extend_data

    def collect_selfplay_data(self, n_games=1):
        '''
        收集自我对抗数据
        '''
        for i in range(n_games):
            game = Game(AIPlayerplus(self.policy_value_net.policy_value_fn,self.AIPlayerplus_num), 
                        AIPlayerplus(self.policy_value_net.policy_value_fn,self.AIPlayerplus_num))
            game.selfplay_run_plus()
            play_data = game.playdata
            self.episode_len = len(play_data)
            # 增添额外数据
            play_data = self.get_equi_data(play_data)
            self.data_buffer.extend(play_data)

    def policy_update(self):
        '''
        更新策略
        '''
        mini_batch = random.sample(self.data_buffer, self.batch_size)
        state_batch = [data[0] for data in mini_batch]
        mcts_probs_batch = [data[1] for data in mini_batch]
        winner_batch = [data[2] for data in mini_batch]
        old_probs, old_v = self.policy_value_net.policy_value(state_batch)
        for i in range(self.epochs):
            loss, entropy = self.policy_value_net.train_step(
                    state_batch,
                    mcts_probs_batch,
                    winner_batch,
                    self.learn_rate*self.lr_multiplier)
            new_probs, new_v = self.policy_value_net.policy_value(state_batch)
            kl = np.mean(np.sum(old_probs * (
                    np.log(old_probs + 1e-10) - np.log(new_probs + 1e-10)),
                    axis=1))
            if kl > self.kl_targ * 4:  # 如果严重发散及时停止学习
                break
        # 用kl散度调节学习率
        if kl > self.kl_targ * 2 and self.lr_multiplier > 0.1:
            self.lr_multiplier /= 1.5
        elif kl < self.kl_targ / 2 and self.lr_multiplier < 10:
            self.lr_multiplier *= 1.5

        # print((
                
        #         "loss:{},"
        #         "entropy:{},"
        #         ).format(

        #                 loss,
        #                 entropy))
        print(("kl:{:.5f},"
                "lr_multiplier:{:.3f},"
                "loss:{},"
                "entropy:{},"
                ).format(kl,
                        self.lr_multiplier,
                        loss,
                        entropy))
        return loss, entropy

    def policy_evaluate(self, n_games=10):
        '''
        评估策略
        注：这只是为了了解训练过程
        '''
        win_cnt = defaultdict(int)
        for i in range(n_games):
            game = Game(AIPlayerplus(self.policy_value_net.policy_value_fn), AIPlayer(self.AIPlayer_num))
            game.selfplay_run()
            winner = game.board.win()
            win_cnt[winner] += 1
        win_ratio = (1.0*win_cnt[1]+0.5*win_cnt[0]) / n_games
        print("num_playouts:{}, win: {}, lose: {}, tie:{}".format(
                self.AIPlayer_num,
                win_cnt[1], win_cnt[-1], win_cnt[0]))
        return win_ratio

    def run(self):
        '''
        开始训练
        '''
        try:
            for i in range(self.game_batch_num):
                self.collect_selfplay_data(self.play_batch_size)
                print("batch i:{}, episode_len:{}".format(
                        i+1, self.episode_len))
                loss, entropy = self.policy_update()
                # 检查当前模型表现并保存参数
                if (i+1) % self.check_freq == 0:
                    print("current self-play batch: {}".format(i+1))
                    win_ratio = self.policy_evaluate()
                    self.policy_value_net.save_model('./current_policy.model')
                    if win_ratio > self.best_win_ratio:
                        print("New best policy!!!!!!!!")
                        self.best_win_ratio = win_ratio
                        # 更新最佳策略
                        self.policy_value_net.save_model('./best_policy.model')
                        if (self.best_win_ratio == 1.0 and self.mcts_player_num < 500):
                            self.AIPlayer_num += 100
                            self.best_win_ratio = 0.0
        except KeyboardInterrupt:
            print('\n\rquit')


if __name__ == '__main__':
    training_pipeline = TrainPipeline(init_model='./current_policy.model')
    training_pipeline.run()