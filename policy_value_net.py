import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np

def set_learning_rate(optimizer, lr):
    '''
    设置学习率
    '''
    for param_group in optimizer.param_groups:
        param_group['lr'] = lr
        
class Net(nn.Module):
    '''
    神经网络模型
    '''
    def __init__(self):
        super().__init__()         
        # 公共层
        self.conv1 = nn.Conv2d(2, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        # 行动策略层
        self.act_conv1 = nn.Conv2d(128, 2, kernel_size=1)
        self.act_fc1 = nn.Linear(2*8*8, 8*8)
        # 价值层
        self.val_conv1 = nn.Conv2d(128, 2, kernel_size=1)
        self.val_fc1 = nn.Linear(2*8*8, 64)
        self.val_fc2 = nn.Linear(64, 1)
        
    def forward(self, state_input):
        # 公共层
        x = F.relu(self.conv1(state_input))
        x = F.relu(self.conv2(x))
        x = F.relu(self.conv3(x))
        # 行动策略层
        x_act = F.relu(self.act_conv1(x))
        x_act = x_act.view(-1, 2*8*8)
        x_act = F.log_softmax(self.act_fc1(x_act),dim=1)
        # 价值层
        x_val = F.relu(self.val_conv1(x))
        x_val = x_val.view(-1, 2*8*8)
        x_val = F.relu(self.val_fc1(x_val))
        x_val = F.tanh(self.val_fc2(x_val))
        return x_act, x_val
        
class PolicyValueNet():
    '''
    策略价值网络
    '''
    def __init__(self, model_file=None, use_gpu=False):
        self.use_gpu = use_gpu
        self.l2_const = 1e-4   # l2正则化系数
        # 策略网络模型
        if self.use_gpu:
            self.policy_value_net = Net().cuda()
        else:
            self.policy_value_net = Net()
        self.optimizer = optim.Adam(self.policy_value_net.parameters(), weight_decay=self.l2_const)
        if model_file:
            net_params = torch.load(model_file)
            self.policy_value_net.load_state_dict(net_params)
            
    def policy_value(self, state_batch):
        '''
        训练用
        '''
        if self.use_gpu:
            state_batch = torch.FloatTensor(np.array(state_batch)).cuda()
            log_act_probs, value = self.policy_value_net(state_batch)
            act_probs = np.exp(log_act_probs.detach().cpu().numpy())
            return act_probs, value.detach().cpu().numpy()
        else:
            state_batch = torch.FloatTensor(np.array(state_batch))
            log_act_probs, value = self.policy_value_net(state_batch)
            act_probs = np.exp(log_act_probs.detach().numpy())
            return act_probs, value.detach().numpy()
        
    def policy_value_fn(self, board):
        '''
        input:棋盘
        output：需要值
        实战用
        '''
        current_state = np.expand_dims(board.current_state(), axis=0)
        current_state = np.ascontiguousarray(current_state)
        if self.use_gpu:
            log_act_probs, value = self.policy_value_net(torch.from_numpy(current_state).cuda().float())
            act_probs = np.exp(log_act_probs.detach().cpu().numpy())
            act_probs = np.reshape(act_probs,(8, 8))
        else:
            log_act_probs, value = self.policy_value_net(torch.from_numpy(current_state).float())
            act_probs = np.exp(log_act_probs.detach().numpy())  
            act_probs = np.reshape(act_probs,(8, 8))
        value = value[0][0]
        return act_probs, value
    
    def train_step(self, state_batch, mcts_probs, winner_batch, lr):
        '''
        进行一次训练
        '''
        if self.use_gpu:
            state_batch = torch.FloatTensor(state_batch).cuda()
            mcts_probs = torch.FloatTensor(mcts_probs).cuda()
            winner_batch = torch.FloatTensor(winner_batch).cuda()
        else:
            state_batch = torch.FloatTensor(state_batch)
            mcts_probs = torch.FloatTensor(mcts_probs)
            winner_batch = torch.FloatTensor(winner_batch)
        
        mcts_probs = mcts_probs.view(-1, 64)
        # 使参数梯度归0
        self.optimizer.zero_grad()
        # 设置学习率
        set_learning_rate(self.optimizer, lr)

        # 向前
        log_act_probs, value = self.policy_value_net(state_batch)
        # 定义损失函数 loss = (z - v)^2 - pi^T * log(p) + c||theta||^2
        # 注意：L2正则化已经被加入优化器中
        value_loss = F.mse_loss(value.view(-1), winner_batch)
        policy_loss = -torch.mean(torch.sum(mcts_probs*log_act_probs,1))
        loss = value_loss + policy_loss
        # 反向传播并优化
        loss.backward()
        self.optimizer.step()
        # 通过落子熵观察情况
        entropy = -torch.mean(torch.sum(torch.exp(log_act_probs) * log_act_probs,1))
       
        return loss.item(), entropy.item()

    def get_policy_param(self):
        net_params = self.policy_value_net.state_dict()
        return net_params

    def save_model(self, model_file):
        '''
        保存模型参数
        '''
        net_params = self.get_policy_param()
        torch.save(net_params, model_file)