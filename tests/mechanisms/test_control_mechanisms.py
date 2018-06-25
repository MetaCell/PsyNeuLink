import numpy as np
import psyneulink as pnl
import pytest


class TestLCControlMechanism:

    @pytest.mark.mechanism
    @pytest.mark.control_mechanism
    @pytest.mark.benchmark(group="LCControlMechanism Default")
    @pytest.mark.parametrize("mode", ['Python'])
    def test_default_lc_control_mechanism(self, benchmark, mode):
        G = 1.0
        k = 0.5
        starting_value_LC = 2.0
        user_specified_gain = 1.0

        A = pnl.TransferMechanism(function=pnl.Logistic(gain=user_specified_gain))

        B = pnl.TransferMechanism(function=pnl.Logistic(gain=user_specified_gain))
        # B.output_states[0].value *= 0.0  # Reset after init | Doesn't matter here b/c default var = zero, no intercept

        P = pnl.Process(pathway=[A, B])

        LC = pnl.LCControlMechanism(
            modulated_mechanisms=[A, B],
            base_level_gain=G,
            scaling_factor_gain=k,
            objective_mechanism=pnl.ObjectiveMechanism(
                function=pnl.Linear,
                monitored_output_states=[B],
                name='LC ObjectiveMechanism'
            )
        )
        for output_state in LC.output_states:
            output_state.value *= starting_value_LC

        S = pnl.System(processes=[P])

        gain_created_by_LC_output_state_1 = []
        mod_gain_assigned_to_A = []
        base_gain_assigned_to_A = []
        mod_gain_assigned_to_B = []
        base_gain_assigned_to_B = []

        def report_trial():
            gain_created_by_LC_output_state_1.append(LC.output_states[0].value[0])
            mod_gain_assigned_to_A.append(A.mod_gain)
            mod_gain_assigned_to_B.append(B.mod_gain)
            base_gain_assigned_to_A.append(A.function_object.gain)
            base_gain_assigned_to_B.append(B.function_object.gain)

        benchmark(S.run, inputs={A: [[1.0], [1.0], [1.0], [1.0], [1.0]]},
              call_after_trial=report_trial)

        # (1) First value of gain in mechanisms A and B must be whatever we hardcoded for LC starting value
        assert mod_gain_assigned_to_A[0] == starting_value_LC

        # (2) _gain should always be set to user-specified value
        for i in range(5):
            assert base_gain_assigned_to_A[i] == user_specified_gain
            assert base_gain_assigned_to_B[i] == user_specified_gain

        # (3) LC output on trial n becomes gain of A and B on trial n + 1
        assert np.allclose(mod_gain_assigned_to_A[1:], gain_created_by_LC_output_state_1[0:-1])

        # (4) mechanisms A and B should always have the same gain values (b/c they are identical)
        assert np.allclose(mod_gain_assigned_to_A, mod_gain_assigned_to_B)


    @pytest.mark.mechanism
    @pytest.mark.control_mechanism
    @pytest.mark.benchmark(group="LCControlMechanism Basic")
    @pytest.mark.parametrize("mode", ['Python', 'LLVM'])
    def test_lc_control_mech_basic(self, benchmark, mode):

        LC = pnl.LCControlMechanism(
            base_level_gain=3.0,
            scaling_factor_gain=0.5,
            default_variable = 10.0
        )
        val = LC.execute([10.0], bin_execute=(mode=='LLVM'))
        # LLVM returns combination of all output states so let's do that for
        # Python as well
        if mode == 'Python':
            val = [s.value for s in LC.output_states]
        assert np.allclose(val, [3.00139776, 3.00139776, 3.00139776, 3.00139776])
        val = benchmark(LC.execute, [[10.0]], bin_execute=(mode=='LLVM'))
