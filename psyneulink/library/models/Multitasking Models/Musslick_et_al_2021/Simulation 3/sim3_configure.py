import numpy as np
from ...Base_Models import NNModel
from ...Tools import *

# Network parameters
num_hidden_units = 100  # number of hidden units
init_scale = 0.1        # scales for initialized random weights
learning_rate = 0.3     # learning rate
decay = 0               # weight penalization parameter
bias = -2               # weight from bias units to hidden & output units
thresh = 0.01           # mean-squared error stopping criterion
hidden_path_size = 1    # group size of hidden units that receive the same weights from the task layer
output_path_size = 1    # group size of output units that receive the same weights from the task layer
tau = 0.15

# Training environment parameters
n_pathways = 3          # number of pathways (i.e. number of feature dimensions % output dimensions)
n_features = 3          # number of feature units per stimulus input dimension
pathway_overlap = 2     # number of tasks per stimulus input dimension
num_sgl_tasks = pathway_overlap * n_pathways # total number of tasks sampled
sd_scale = 0                  # max. variance for around each stimulus input unit activation
same_stimuli_across_tasks = 1 # use same stimuli across tasks? (this parameter is only relevant if sdScale > 0)
samples_per_task_train = []   # stimuli per task for training (if samplesPerTask is empty then training patterns include entire space of stimuli per task)
samples_per_task_test = []    # stimuli per task for testing (if samplesPerTask is empty then training patterns include entire space of stimuli per task)


def config():
    # Generate task envirnonment
    tasks_to_perform = [1, 2, 4, 5, 9]
    create_task_patterns(n_pathways, n_features, samples_per_task_train, sd_scale,
        same_stimuli_across_tasks, tasks_to_perform)
    # TEMP: Read input/task/train/data
    input_data = np.loadtxt(open('input_sglt.csv', 'rb'), delimiter=',', skiprows=1)
    tasks_data = np.loadtxt(open('tasks_sglt.csv', 'rb'), delimiter=',', skiprows=1)
    train_data = np.loadtxt(open('train_sglt.csv', 'rb'), delimiter=',', skiprows=1)
    # Build network
    task_net = NNModel(num_hidden_units, learning_rate, bias, init_scale, thresh, decay,
        hidden_path_size, output_path_size)
    task_net.n_pathways = n_pathways
    # Initialize network according to bipartite graph
    task_net.set_data(input_data, tasks_data, train_data)
    task_net.configure()
    return task_net
