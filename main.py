from player import HumanPlayer,  RandomPlayer, AIPlayer, AIPlayerplus
from game import Game
from policy_value_net import PolicyValueNet

policy_value_net = PolicyValueNet(model_file='./current_policy.model')

black_player = AIPlayerplus(policy_value_net.policy_value_fn,1000)
white_player = AIPlayer(400)
# black_player = RandomPlayer()
# white_player = RandomPlayer()
game = Game(black_player, white_player)
game.run()
