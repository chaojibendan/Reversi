# Reversi
结合神经网络与强化学习的黑白棋

## 环境配置

- python
- pytorch

## 文件说明

- board.py 棋盘的状态信息
- game.py 游戏规范
- player.py 玩家信息
- mcts.py 蒙特卡洛树搜索
- mcts_plus.py 采用神经网络改进探索策略的蒙特卡洛树搜索
- policy_value_net.py 神经网络模型
- train.py 训练控制
- selfplay.py 实现快速自我对战查看结果

## 使用说明

- 运行`train.py`进行训练，会保存当前模型信息和最优模型信息
- 运行`main.py`进行单局对战，可以根据需求设定黑白玩家的玩家信息
- 运行`selfplay.py`进行多局自我对抗方便查看胜率（默认为速度最快的多进程队列）
- 文件中的`current_policy.model`和`best_policy.model`均为模拟1000次，训练50次得出的模型

## 项目介绍

### 神经网络
神经网络基础原理参考于https://zhuanlan.zhihu.com/p/32089487 具体实现有较多不同

- 这里的神经网络使用的是策略与价值网络。神经网络获取从自我对抗中得到的棋盘状态、蒙特卡洛树搜索（此处已经应用了神经网络）生成的行动概率和最终赢家三种数据，并根据棋盘状态由神经网络生成当前的行动概率和局面评估，使得根据棋盘状态输出生成的行动概率和局面评估不断接近蒙特卡洛树搜索生成的行动概率和最终赢家。
- 输入：当前选手局面（是己方棋子为1，其余全为0），对方选手局面。
- 输出：当前选手下棋位置的概率以及当前选手局面的评估（越好越偏向1，越差越偏向0）

### 样本多样性

- 自对抗生成训练样本时，行动概率正比于基于神经网络的mcts输出概率，且加入了迪利克雷噪声，以此来增加样本多样性。同时我们还对棋盘进行了翻转与镜像来增加样本数目。

### 与mcts的差别

- 将ucb公式进行了改写，探索部分加入了先验概率。
- 神经网络获取行动概率与局面评估，以此来替代选择结点的随机扩展和扩展结点的模拟评估（注意此处如果为末结点不替代评估）。好处：一方面进行更有价值探索，另一方面大大节省了模拟的时间。

### 结果
（测试模型：使用模拟次数为1000次，训练了50次的模型）

- 同样模拟400次时以轻微优势战胜纯mcts（100局赢51输48平1）
- 同样模拟100次时完全碾压纯mcts（10局赢8负1平1）

### 结论
- 同样模拟400次 ，基于神经网络的mcts每步只需要2s，而纯mcts需要10s以上，这大大节省了AI进行决策的时间。
- 当训练时模拟次数越多，实际应用时模型使用低模拟次数的效果便越好，这也与我们的常识相符。而当使用较高模拟次数时对战纯mcts胜率不够高，猜测一方面是由于训练次数较少（我的笔记本太垃圾了），导致神经网络输出的结果不够准确，另一方面是我自己的模拟次数不够高，导致局面评估准确率不够。因此训练模型时建议增大模拟次数以及找到较为合适的训练次数。
