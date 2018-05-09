import numpy as np
import matplotlib.pyplot as plt
import psyneulink as pnl

# Define Variables ----------------------------------------------------------------------------------------------------
rate = 0.01
inhibition = -2.0
bias = 4.0
threshold = 0.55
settle_trials = 50
prior120 = 120
terminate2 = 180
terminate3 = 200
terminate4 = 220
terminate5 = 240
terminate6 = 260
terminate7 = 280
# Create mechanisms ---------------------------------------------------------------------------------------------------
#   Linear input units, colors: ('red', 'green'), words: ('RED','GREEN')
colors_input_layer = pnl.TransferMechanism(size=3,
                                           function=pnl.Linear,
                                           name='COLORS_INPUT')

words_input_layer = pnl.TransferMechanism(size=3,
                                          function=pnl.Linear,
                                          name='WORDS_INPUT')

task_input_layer = pnl.TransferMechanism(size=2,
                                          function=pnl.Linear,
                                          name='TASK_INPUT')

#   Task layer, tasks: ('name the color', 'read the word')
task_layer = pnl.RecurrentTransferMechanism(size=2,
                                            function=pnl.Logistic(),
                                            hetero=-2,
                                            integrator_mode=True,
                                            smoothing_factor=0.1,
                                            name='TASK')

#   Hidden layer units, colors: ('red','green') words: ('RED','GREEN')
colors_hidden_layer = pnl.RecurrentTransferMechanism(size=3,
                                            function=pnl.Logistic(bias=4.0),
                                            integrator_mode=True,
                                                     hetero=-2.0,
                                           # noise=pnl.NormalDist(mean=0.0, standard_dev=.0).function,
                                            smoothing_factor=0.1, # cohen-huston text says 0.01
                                            name='COLORS HIDDEN')

words_hidden_layer = pnl.RecurrentTransferMechanism(#default_variable=np.array([[1, 1, 1]]),
                                                    size=3,
                                           function=pnl.Logistic(bias=4.0),
                                                    hetero=-2,
                                           integrator_mode=True,
                                          # noise=pnl.NormalDist(mean=0.0, standard_dev=.05).function,
                                           smoothing_factor=0.1,
                                           name='WORDS HIDDEN')
#   Response layer, responses: ('red', 'green'): RecurrentTransferMechanism for self inhibition matrix
response_layer = pnl.RecurrentTransferMechanism(size=2,  #Recurrentdefault_variable=np.array([[3.1, 3.1]]),
                                                function=pnl.Logistic(),
                                                hetero=-2.0,
                                                integrator_mode=True,
                                                smoothing_factor=0.1,
                                                name='RESPONSE')

# Log mechanisms ------------------------------------------------------------------------------------------------------
#task_layer.set_log_conditions('gain')
task_layer.set_log_conditions('value')
task_layer.set_log_conditions('InputState-0')

colors_hidden_layer.set_log_conditions('value')
colors_hidden_layer.set_log_conditions('InputState-0')

words_hidden_layer.set_log_conditions('value')
words_hidden_layer.set_log_conditions('InputState-0')

response_layer.set_log_conditions('value')
response_layer.set_log_conditions('InputState-0')
# Connect mechanisms --------------------------------------------------------------------------------------------------
# (note that response layer projections are set to all zero first for initialization

color_input_weights = pnl.MappingProjection(matrix=np.array([[1.0, 0.0, 0.0],
                                                             [0.0, 1.0, 0.0],
                                                             [0.0, 0.0, 0.0]]))

word_input_weights = pnl.MappingProjection(matrix=np.array([[1.0, 0.0, 0.0],
                                                            [0.0, 1.0, 0.0],
                                                            [0.0, 0.0, 0.0]]))

task_input_weights = pnl.MappingProjection(matrix=np.array([[1.0, 0.0],
                                                            [0.0, 1.0]]))

color_task_weights  = pnl.MappingProjection(matrix=np.array([[4.0, 0.0],
                                                             [4.0, 0.0],
                                                             [4.0, 0.0]]))

task_color_weights  = pnl.MappingProjection(matrix=np.array([[4.0, 4.0, 4.0],
                                                             [0.0, 0.0, 0.0]]))

word_task_weights = pnl.MappingProjection(matrix=np.array([[0.0, 4.0],
                                                           [0.0, 4.0],
                                                           [0.0, 4.0]]))

task_word_weights = pnl.MappingProjection(matrix=np.array([[0.0, 0.0, 0.0],
                                                           [4.0, 4.0, 4.0]]))

response_color_weights = pnl.MappingProjection(matrix=np.array([[0.0, 0.0, 0.0],
                                                                [0.0, 0.0, 0.0]]))

response_word_weights  = pnl.MappingProjection(matrix=np.array([[0.0, 0.0, 0.0],
                                                                [0.0, 0.0, 0.0]]))

color_response_weights = pnl.MappingProjection(matrix=np.array([[1.5, 0.0],
                                                                [0.0, 1.5],
                                                                [0.0, 0.0]]))
word_response_weights  = pnl.MappingProjection(matrix=np.array([[2.5, 0.0],
                                                                [0.0, 2.5],
                                                                [0.0, 0.0]]))
#
# Create pathways -----------------------------------------------------------------------------------------------------
color_response_process = pnl.Process(pathway=[colors_input_layer,
                                              color_input_weights,
                                              colors_hidden_layer,
                                              color_response_weights,
                                              response_layer,
                                              response_color_weights,
                                              colors_hidden_layer],
                                     name='COLORS_RESPONSE_PROCESS')

word_response_process = pnl.Process(pathway=[words_input_layer,
                                             word_input_weights,
                                             words_hidden_layer,
                                             word_response_weights,
                                             response_layer,
                                             response_word_weights,
                                             words_hidden_layer],
                                     name='WORDS_RESPONSE_PROCESS')

task_color_response_process = pnl.Process(pathway=[task_input_layer,
                                                   task_input_weights,
                                                   task_layer,
                                                   task_color_weights,
                                                   colors_hidden_layer,
                                                   color_task_weights,
                                                   task_layer])

task_word_response_process = pnl.Process(pathway=[task_input_layer,
                                                  task_layer,
                                                  task_word_weights,
                                                  words_hidden_layer,
                                                  word_task_weights,
                                                  task_layer])

# Create system -------------------------------------------------------------------------------------------------------
Bidirectional_Stroop = pnl.System(processes=[color_response_process,
                                                   word_response_process,
                                                   task_color_response_process,
                                                   task_word_response_process],
                                        name='FEEDFORWARD_STROOP_SYSTEM')

# LOGGING:
colors_hidden_layer.set_log_conditions('value')
words_hidden_layer.set_log_conditions('value')

Bidirectional_Stroop.show()
# Bidirectional_Stroop.show_graph(show_dimensions=pnl.ALL)#,show_mechanism_structure=pnl.VALUES) # Uncomment to show graph of the system

# Create threshold function -------------------------------------------------------------------------------------------
def pass_threshold(response_layer, thresh):
    results1 = response_layer.output_states.values[0][0] #red response
    results2 = response_layer.output_states.values[0][1] #green response
    # print(results1)
    # print(results2)
    if results1  >= thresh or results2 >= thresh:
        return True
    return False

# 2nd threshold function
def pass_threshold2(response_layer, thresh, terminate):
    results1 = response_layer.output_states.values[0][0] #red response
    results2 = response_layer.output_states.values[0][1] #green response
    length = response_layer.log.nparray_dictionary()['value'].shape[0]
    # print(results1)
    # print(results2)
    if results1  >= thresh or results2 >= thresh:
        return True
    if length ==terminate:
        return True
    return False

terminate_trial = {
   pnl.TimeScale.TRIAL: pnl.While(pass_threshold, response_layer, threshold)
}
terminate_trial2 = {
   pnl.TimeScale.TRIAL: pnl.While(pass_threshold2, response_layer, threshold, terminate2)
}
terminate_trial3 = {
   pnl.TimeScale.TRIAL: pnl.While(pass_threshold2, response_layer, threshold, terminate3)
}
terminate_trial4 = {
   pnl.TimeScale.TRIAL: pnl.While(pass_threshold2, response_layer, threshold, terminate4)
}
terminate_trial5 = {
   pnl.TimeScale.TRIAL: pnl.While(pass_threshold2, response_layer, threshold, terminate5)
}
terminate_trial6 = {
   pnl.TimeScale.TRIAL: pnl.While(pass_threshold2, response_layer, threshold, terminate6)
}
terminate_trial7 = {
   pnl.TimeScale.TRIAL: pnl.While(pass_threshold2, response_layer, threshold, terminate7)
}
terminate_list = [terminate_trial2,
                  terminate_trial3,
                  terminate_trial4,
                  terminate_trial5,
                  terminate_trial6,
                  terminate_trial7]
# Create test trials function -----------------------------------------------------------------------------------------
# a BLUE word input is [1,0] to words_input_layer and GREEN word is [0,1]
# a blue color input is [1,0] to colors_input_layer and green color is [0,1]
# a color-naming trial is [1,0] to task_layer and a word-reading trial is [0,1]
def trial_dict(red_color, green_color, neutral_color, red_word, green_word, neutral_word, CN, WR):

    trialdict = {
    colors_input_layer: [red_color, green_color, neutral_color],
    words_input_layer: [red_word, green_word, neutral_word],
    task_input_layer: [CN, WR]
    }
    return trialdict

# Define initialization trials separately
WR_initialize_input = trial_dict(0, 0, 0, 0, 0, 0, 0, 1)
CN_initialize_input = trial_dict(0, 0, 0, 0, 0, 0, 1, 0)

CN_incongruent_trial_input = trial_dict(1, 0, 0, 0, 1, 0, 1, 0) #red_color, green color, red_word, green word, CN, WR
CN_congruent_trial_input = trial_dict(1, 0, 0, 1, 0, 0, 1, 0) #red_color, green color, red_word, green word, CN, WR
CN_control_trial_input = trial_dict(1, 0, 0, 0, 0, 0, 1, 0) #red_color, green color, red_word, green word, CN, WR
CN_control_word_trial_input = trial_dict(0, 0, 0, 1, 0, 0, 1, 0) #red_color, green color, red_word, green word, CN, WR

CN_congruent_word_first_input = trial_dict(0, 0, 0, 1, 0, 0, 1, 0) #red_color, green color, red_word, green word, CN, WR
CN_incongruent_word_first_input = trial_dict(0, 0, 0, 0, 1, 0, 1, 0) #red_color, green color, red_word, green word, CN, WR

WR_congruent_trial_input = trial_dict(1, 0, 0, 1, 0, 0, 0, 1) #red_color, green color, red_word, green word, CN, WR
WR_incongruent_trial_input = trial_dict(1, 0, 0, 0, 1, 0, 0, 1) #red_color, green color, red_word, green word, CN, WR
WR_control_trial_input = trial_dict(1, 0, 0, 0, 0, 0, 0, 1) #red_color, green color, red_word, green word, CN, WR

conditions = 3
runs = 6
runs2 = 6
response_all = []
response_all2 = []

Stimulus = [[CN_initialize_input, CN_congruent_word_first_input, CN_congruent_trial_input, CN_control_trial_input],
            [CN_initialize_input, CN_incongruent_word_first_input, CN_incongruent_trial_input, CN_control_trial_input],
            [CN_initialize_input, CN_control_word_trial_input, CN_control_trial_input, CN_control_trial_input]]


# First "for loop" over conditions
# Second "for loop" over runs
for cond in range(conditions):
# ---------------------------------------------------------------------------------------------------------------------
    # Run congruent trial with word presented 1200 trials prior ------------------------------------------------------------
    for run in range(runs):
        response_color_weights = pnl.MappingProjection(matrix=np.array([[0.0, 0.0, 0.0],
                                                                        [0.0, 0.0, 0.0]]))

        response_word_weights = pnl.MappingProjection(matrix=np.array([[0.0, 0.0, 0.0],
                                                                       [0.0, 0.0, 0.0]]))
        Bidirectional_Stroop.run(inputs=Stimulus[cond][0], num_trials=settle_trials)    # run system to settle for 200 trials with congruent stimuli input
        Bidirectional_Stroop.run(inputs=Stimulus[cond][0], num_trials=20*(run))  # run system to settle for 200 trials with congruent stimuli input

        response_color_weights = pnl.MappingProjection(matrix=np.array([[1.5, 0.0, 0.0],
                                                                        [0.0, 1.5, 0.0]]))

        response_word_weights  = pnl.MappingProjection(matrix=np.array([[2.5, 0.0, 0.0],
                                                                        [0.0, 2.5, 0.0]]))

        Bidirectional_Stroop.run(inputs=Stimulus[cond][1],num_trials=prior120 - (run*20))# termination_processing=terminate_trial) # run system with congruent stimulus input until
        Bidirectional_Stroop.run(inputs=Stimulus[cond][2], termination_processing=terminate_trial) # run system with congruent stimulus input until
                                                                    # threshold in of of the response layer units is reached

    # Store values from run -----------------------------------------------------------------------------------------------
        r = response_layer.log.nparray_dictionary('value')       # Log response output from special logistic function
        rr = r['value']
        n_r = rr.shape[0]
        rrr = rr.reshape(n_r,2)

        response_all.append(rrr.shape[0])

        # Clear log & reinitialize ----------------------------------------------------------------------------------------
        response_layer.log.clear_entries(delete_entry=False)
        colors_hidden_layer.log.clear_entries(delete_entry=False)
        words_hidden_layer.log.clear_entries(delete_entry=False)
        task_layer.log.clear_entries(delete_entry=False)

        colors_hidden_layer.reinitialize([[0,0,0]])
        words_hidden_layer.reinitialize([[0,0,0]])
        response_layer.reinitialize([[0,0]])
        task_layer.reinitialize([[0,0]])

    print('response_all: ', response_all)

    # Run trials after congruent color was presented ----------------------------------------------------------------------
    for run2 in range(runs2):
        response_color_weights = pnl.MappingProjection(matrix=np.array([[0.0, 0.0, 0.0],
                                                                        [0.0, 0.0, 0.0]]))
        response_word_weights = pnl.MappingProjection(matrix=np.array([[0.0, 0.0, 0.0],
                                                                       [0.0, 0.0, 0.0]]))
        Bidirectional_Stroop.run(inputs=Stimulus[cond][0], num_trials = settle_trials)  # run system to settle for 200 trials with congruent stimuli input
        Bidirectional_Stroop.run(inputs=Stimulus[cond][0], num_trials = prior120)  # run system to settle for 200 trials with congruent stimuli input
        response_color_weights = pnl.MappingProjection(matrix=np.array([[1.5, 0.0, 0.0],
                                                                        [0.0, 1.5, 0.0]]))
        response_word_weights = pnl.MappingProjection(matrix=np.array([[2.5, 0.0, 0.0],
                                                                       [0.0, 2.5, 0.0]]))
        Bidirectional_Stroop.run(inputs=Stimulus[cond][3], termination_processing=terminate_list[run2])#terminate_list[run2])  # termination_processing=terminate_trial) # run system with congruent stimulus input until

        Bidirectional_Stroop.run(inputs=Stimulus[cond][2], termination_processing=terminate_trial)  # run system with congruent stimulus input until
        # threshold in of of the response layer units is reached
        # Store values from run -----------------------------------------------------------------------------------------------
        r = response_layer.log.nparray_dictionary('value')       # Log response output from special logistic function
        rr = r['value']
        n_r = rr.shape[0]
        rrr = rr.reshape(n_r,2)
        response_all.append(rrr.shape[0])
        # Clear log & reinitialize ----------------------------------------------------------------------------------------
        response_layer.log.clear_entries(delete_entry=False)
        colors_hidden_layer.log.clear_entries(delete_entry=False)
        words_hidden_layer.log.clear_entries(delete_entry=False)
        task_layer.log.clear_entries(delete_entry=False)
        colors_hidden_layer.reinitialize([[0,0,0]])
        words_hidden_layer.reinitialize([[0,0,0]])
        response_layer.reinitialize([[0,0]])
        task_layer.reinitialize([[0,0]])

# print('response_all: ', response_all)
plt.plot(response_all[0:13])
plt.plot(response_all[13:26])
plt.plot(response_all[26:39])

# stimulus_onset_asynchrony = np.linspace(-400,400,13)
# plt.plot(stimulus_onset_asynchrony, response_all[0:13])
# plt.plot(stimulus_onset_asynchrony, response_all[13:26])
# plt.plot(stimulus_onset_asynchrony, response_all[26:39])
