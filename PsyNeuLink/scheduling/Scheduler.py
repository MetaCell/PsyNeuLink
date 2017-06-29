# Princeton University licenses this file to You under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.  You may obtain a copy of the License at:
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.


# ********************************************* Scheduler **************************************************************

"""

Overview
--------

A Scheduler is used to generate the order in which the `Mechanisms <Mechanism>` of a `Composition` are executed.
By default, Mechanisms are executed in an order determined by the pattern of `Projections <Projection>` among them
in the `Composition`, with each Mechanism executed once per `PASS` through the Composition.
For example, in a `System` in which a Mechanism A projects to a Mechanism B that projects to a Mechanism C,
then A will execute first followed by B, and then C in each `PASS` through the System.  However, a Scheduler can be
used to implement more complex patterns of execution, by specifying `Conditions <Condition>` that determine when and
how many times individual Mechanisms execute, and whether and how this depends on the execution of other Mechanisms.
Conditions can be combined in arbitrary ways to generate any pattern of execution of the Mechanisms in a `System`
that is logically possible.

Creating a Scheduler
--------------------

A Scheduler can be created explicitly using its constructor.  However, more commonly it is created automatically
for a `System` when the System is created.  When creating a Scheduler explicitly, the set of `Mechanisms <Mechanism>`
to be executed and their order must be specified in the Scheduler's constructor using one the following:

* a `System` in the **system** argument - if a System is specified,
  the schedule is created using the Mechanisms in the System's `executionList <System.exeuctionList>` and an order
  of execution specified by the dependencies among the Mechanisms in its `executionGraph <System.executionGraph>`.

* a *graph specification dictionary* in the **graph** argument -
  each entry of the dictionary must be a Mechanism, and the value of each entry must be one or a
  set of Mechanisms that project directly to the key.  The graph must be acyclic; an error is generated if any cycles
  (e.g., recurrent dependencies) are detected.  The Scheduler computes a `toposort` from the graph that is used as
  the default order of executions, subject to any `Conditions` that have been specified (see below).

If both a System and a graph are specified, the System takes precedence, and the graph is ignored.

Conditions can be added to a Scheduler when it is created by specifying a `ConditionSet` (a set of
`Condition <Condition>`) in the **condition_set** argument of its constructor.  Individual Conditions and/or
ConditionSets can also be added after the  Scheduler has been created, using its `add_condition` and
`add_condition_set` methods, respectively.

.. _Scheduler_Algorithm:

Algorithm
---------

When a Scheduler is created, it constructs a `consideration_queue`:  a list of `consideration_sets <consideration_set>`
that defines the order in which Mechanisms are eligible to be executed.  This is based on the pattern of projections
among them specified in the System, or on the dependencies specified in the graph specification dictionary, whichever
was provided in the Scheduler's constructor.  Each `consideration_set` is a set of Mechanisms that are eligible to
execute at the same time (i.e., that appear at the same "depth" in a sequence of dependencies, and
among which there are no dependencies).  The first `consideration_set` consists of only `ORIGIN` Mechanisms.
The second consists of all Mechanisms that receive `Projections <Projection>` from Mechanisms in the first
`consideration_set`. The third consists of Mechanisms that receive Projections from Mechanisms in the first two
`consideration_sets <consideration_set>`, and so forth.  When the Scheduler is run, it uses the
`consideration_queue` to determine which Mechanisms are eligible to execute in each `TIME_STEP` of a `PASS`
through the `consideration_queue`, and then evaluates the `Conditions <Condition>` associated with each Mechanism
in the current `consideration_set` to determine which should actually be assigned for execution.

.. _Scheduler_Execution:

Execution
---------

When a Scheduler is run, it provides a set of Mechanisms that should be run next, based on their dependencies in the
System or graph specification dictionary, and any `Conditions <Condition>`, specified in the Scheduler's constructor.
For each call to the `run <Scheduler.run>` method, the Scheduler sequentially evaluates its
`consideration_sets <consideration_set>` in their order in the `consideration_queue`.  For each set, it  determines
which Mechanisms in the set are allowed to execute, based on whether their associated `Condition(s) <Condition>` have
been met. Any Mechanism that does not have a `Condition` explicitly specified is assigned the Condition `Always`,
that allows it to execute any time it is under consideration. All of the Mechanisms within a `consideration_set` that
are allowed to execute comprise a `TIME_STEP` of execution.

COMMENT:
   JDC: STILL HAVING A HARD TIME IMAGINGING THIS;  EXAMPLE WOULD BE GOOD
so the execution of a Mechanism within a `time_step` may trigger the execution of another Mechanism within its
`consideration_set`.
COMMENT

The ordering of the  Mechanisms specified within a `TIME_STEP` is arbitrary (and is irrelevant, as there are no
sequential dependencies among Mechanisms within the same `consideration_set`). At the beginning of each
`TIME_STEP`, the Scheduler evaluates  whether any specified `termination conditions` have been met, and terminates
the run if so.  Otherwise, it returns a set of the Mechanisms that should be executed
in the current `TIME_STEP`.
EXPLAIN: EACH PASS TRHOUGH THE CONSID Q IS A PASS
IF NOT TERM COND, CONTINUES PASSES UNTIL EVERY MECH EXECUTE AT LEAST ONCE
If no termination Conditions
are specified, the Scheduler terminates a `P` when every Mechanism has been specified for execution at least once
(corresponding to the `AllHaveRun` Condition).
 For each call to its `run <Scheduler.run>` method, the Scheduler returns a list of
Mechanisms to execute from the next `consideration_set` in the `consideration_queue`.


A full pass through the `consideration_queue`
constitutes a `PASS` of execution, during which every Mechanism in the Composition is provided the opportunity to be
considered for execution.  The number of PASSes associated with a single `input <Composition.input>`
to the Composition constitutes a `TRIAL`, and the number of TRIALs executed constitutes a `RUN`.  The Scheduler
continues to make PASSes through the `consideration_queue` until a `Termination` Condition is satisfied.  By default,
this is determined by the number of inputs and/or number of runs specified in the call to the Composition's
`run <Composition.run>` method.  However, other `Termination` Conditions can be specified, that may cause the
Scheduler to terminate earlier (e.g., when a the Condition for a particular Mechanism is met).

**DOCUMENT TERMINATION CONDITIONS HERE


Examples
--------

Please see `Condition` for a list of all supported Conditions and their behavior.

* Basic phasing in a linear process::

    A = TransferMechanism(function = Linear(), name = 'A')
    B = TransferMechanism(function = Linear(), name = 'B')
    C = TransferMechanism(function = Linear(), name = 'C')

    p = process(
        pathway=[A, B, C],
        name = 'p')
    s = system(
        processes=[p],
        name='s')
    my_scheduler = Scheduler(system=s)

    #impicit condition of Always for A
    my_scheduler.add_condition(B, EveryNCalls(A, 2))
    my_scheduler.add_condition(C, EveryNCalls(B, 3))

    # implicit AllHaveRun Termination condition
    execution_sequence = list(my_scheduler.run())

``execution_sequence`` will be: [A, A, B, A, A, B, A, A, B, C].

* Alternate basic phasing in a linear process::

    A = TransferMechanism(function = Linear(), name = 'A')
    B = TransferMechanism(function = Linear(), name = 'B')

    p = process(
        pathway=[A, B],
        name = 'p')
    s = system(
        processes=[p],
        name='s')
    my_scheduler = Scheduler(system=s)

    my_scheduler.add_condition(A, Any(AtPass(0), EveryNCalls(B, 2)))
    my_scheduler.add_condition(B, Any(EveryNCalls(A, 1), EveryNCalls(B, 1)))

    termination_conds = {ts: None for ts in TimeScale}
    termination_conds[TimeScale.TRIAL] = AfterNCalls(B, 4, time_scale=TimeScale.TRIAL)
    execution_sequence = list(my_scheduler.run(termination_conds=termination_conds))

``execution_sequence`` will be: [A, B, B, A, B, B].

* Basic phasing in two processes::

    A = TransferMechanism(function = Linear(), name = 'A')
    B = TransferMechanism(function = Linear(), name = 'B')
    C = TransferMechanism(function = Linear(), name = 'C')

    p = process(
        pathway=[A, C],
        name = 'p')
    q = process(
        pathway=[B, C],
        name = 'q')
    s = system(
        processes=[p, q],
        name='s')
    my_scheduler = Scheduler(system=s)

    my_scheduler.add_condition(A, EveryNPasses(1))
    my_scheduler.add_condition(B, EveryNCalls(A, 2))
    my_scheduler.add_condition(C, Any(AfterNCalls(A, 3), AfterNCalls(B, 3)))

    termination_conds = {ts: None for ts in TimeScale}
    termination_conds[TimeScale.TRIAL] = AfterNCalls(C, 4, time_scale=TimeScale.TRIAL)
    execution_sequence = list(my_scheduler.run(termination_conds=termination_conds))

``execution_sequence`` will be: [A, set([A,B]), A, C, set([A,B]), C, A, C, set([A,B]), C].

.. _Scheduler_Class_Reference

Class Reference
===============

"""

import logging

from toposort import toposort

from PsyNeuLink.Globals.TimeScale import TimeScale
from PsyNeuLink.scheduling.condition import AllHaveRun, Always, ConditionSet

logger = logging.getLogger(__name__)


class SchedulerError(Exception):
    def __init__(self, error_value):
        self.error_value = error_value

    def __str__(self):
        return repr(self.error_value)


class Scheduler(object):
    """Generates an order of execution for `Mechanisms <Mechanism>` in a `Composition` or graph specification
    dictionary, possibly determined by a set of `Conditions <Condition>`.

    Arguments
    ---------

    system : System
        specifies the Mechanisms to be ordered for execution, and any dependencies among them, based on the
        System's `executionGraph <System.executionGraph>` and `executionList <System.executionList>`.

    COMMENT:
        [**??IS THE FOLLOWING CORRECT]:
        K: not correct, there are no implicit System Conditions
        JDC: I WAS REFERRING TO THE DEPENDENCIES IN THE SYSTEM'S GRAPH.  THE FACT THAT conditions IS AN
             OPTIONAL ARG FOR SCHEDULER, AND THAT PROVIDING A system IS SUFFICIENT TO GENERATE A SCHEDULE,
             MEANS THAT THERE MUST BE CONDITIONS IMPLICIT IN THE system.
    COMMENT

    condition  : ConditionSet
        set of `Conditions <Condition>` that specify when individual Mechanisms in **system**
        execute and any dependencies among them, that complements any that are implicit in the System,
        and supercede those where they are in conflict.

    graph : Dict[Mechanism: Mechanism or Set[Mechanism]
        one or a set of `Mechanisms <Mechanism>` to be ordered for execution

    Attributes
    ----------

    condition_set : ConditionSet
        the set of Conditions the Scheduler uses when running

    execution_list : list
        the full history of time steps the Scheduler has produced

    consideration_queue: list
        a list form of the Scheduler's toposort ordering of its nodes

    termination_conds : dict[TimeScale:Condition]
        a mapping from `TimeScales <TimeScale>` to `Conditions <Condition>` that, when met, terminate the execution
        of the specified `TimeScale`.
    """

    def __init__(self, system=None, condition_set=None, nodes=None, toposort_ordering=None):
        '''
        :param self:
        :param condition_set: (ConditionSet) - a :keyword:`ConditionSet` to be scheduled
        '''
        self.condition_set = condition_set if condition_set is not None else ConditionSet(scheduler=self)
        # stores the in order list of self.run's yielded outputs
        self.execution_list = []
        self.consideration_queue = []
        self.termination_conds = None

        if system is not None:
            self.nodes = [m for m in system.executionList]
            self._init_consideration_queue_from_system(system)
        elif nodes is not None:
            self.nodes = nodes
            if toposort_ordering is None:
                raise SchedulerError('Instantiating Scheduler by list of nodes requires a toposort ordering '
                                     '(kwarg toposort_ordering)')
            self.consideration_queue = list(toposort_ordering)
        else:
            raise SchedulerError('Must instantiate a Scheduler with either a System (kwarg system), '
                                 'or a list of Mechanisms (kwarg nodes) and a toposort ordering over them '
                                 '(kwarg toposort_ordering)')

        self._init_counts()

    # the consideration queue is the ordered list of sets of nodes in the composition graph, by the
    # order in which they should be checked to ensure that all parents have a chance to run before their children
    def _init_consideration_queue_from_system(self, system):
        dependencies = []
        for dependency_set in list(toposort(system.executionGraph)):
            new_set = set()
            for d in dependency_set:
                new_set.add(d)
            dependencies.append(new_set)
        self.consideration_queue = dependencies
        logger.debug('Consideration queue: {0}'.format(self.consideration_queue))

    def _init_counts(self):
        # self.times[p][q] stores the number of TimeScale q ticks that have happened in the current TimeScale p
        self.times = {ts: {ts: 0 for ts in TimeScale} for ts in TimeScale}
        # stores total the number of occurrences of a node through the time scale
        # i.e. the number of times node has ran/been queued to run in a trial
        self.counts_total = {ts: None for ts in TimeScale}
        # counts_useable is a dictionary intended to store the number of available "instances" of a certain node that
        # are available to expend in order to satisfy conditions such as "run B every two times A runs"
        # specifically, counts_useable[a][b] = n indicates that there are n uses of a that are available for b to expend
        # so, in the previous example B would check to see if counts_useable[A][B] is 2, in which case B can run
        self.counts_useable = {node: {n: 0 for n in self.nodes} for node in self.nodes}

        for ts in TimeScale:
            self.counts_total[ts] = {n: 0 for n in self.nodes}

    def _reset_count(self, count, time_scale):
        for c in count[time_scale]:
            count[time_scale][c] = 0

    def _increment_time(self, time_scale):
        for ts in TimeScale:
            self.times[ts][time_scale] += 1

    def _reset_time(self, time_scale):
        for ts in TimeScale:
            self.times[time_scale][ts] = 0

    ################################################################################
    # Wrapper methods
    #   to allow the user to ignore the ConditionSet internals
    ################################################################################
    def __contains__(self, item):
        return self.condition_set.__contains__(item)

    def add_condition(self, owner, condition):
        '''
        :param: self:
        :param owner: the :keyword:`Component` that is dependent on the :param conditions:
        :param conditions: a :keyword:`Condition` (including All or Any)
        '''
        self.condition_set.add_condition(owner, condition)

    def add_condition_set(self, conditions):
        '''
        :param: self:
        :param conditions: a :keyword:`dict` mapping :keyword:`Component`s to :keyword:`Condition`s,
               can be added later with :keyword:`add_condition`
        '''
        self.condition_set.add_condition_set(conditions)

    ################################################################################
    # Validation methods
    #   to provide the user with info if they do something odd
    ################################################################################
    def _validate_run_state(self):
        self._validate_condition_set()
        self._validate_termination()

    def _validate_condition_set(self):
        unspecified_nodes = []
        for node in self.nodes:
            if node not in self.condition_set:
                self.condition_set.add_condition(node, Always())
                unspecified_nodes.append(node)
        if len(unspecified_nodes) > 0:
            logger.warning('These nodes have no Conditions specified, and will be scheduled with condition Always: {0}'.
                           format(unspecified_nodes))

    def _validate_termination(self):
        if self.termination_conds is None:
            logger.warning('A termination Condition dict (termination_conds[<time_step>]: Condition) was not specified,'
                           ' and so the termination conditions for all TimeScale will be set to AllHaveRun()')
            self.termination_conds = {ts: AllHaveRun() for ts in TimeScale}
        for tc in self.termination_conds:
            if self.termination_conds[tc] is None:
                if tc in [TimeScale.TRIAL]:
                    raise SchedulerError('Must specify a {0} termination Condition (termination_conds[{0}]'.format(tc))
            else:
                if self.termination_conds[tc].scheduler is None:
                    logger.debug('Setting scheduler of {0} to self ({1})'.format(self.termination_conds[tc], self))
                    self.termination_conds[tc].scheduler = self

    ################################################################################
    # Run methods
    ################################################################################

    def run(self, termination_conds=None):
        '''
        :param self:
        :param termination_conds: (dict) - a mapping from :keyword:`TimeScale`s to :keyword:`Condition`s that when met
               terminate the execution of the specified :keyword:`TimeScale`
        '''
        self.termination_conds = termination_conds
        self._validate_run_state()

        logger.info('termination_conds: {0}, self.termination_conds: {1}'.
                    format(termination_conds, self.termination_conds))

        def has_reached_termination(self, time_scale=None):
            term = True
            if time_scale is None:
                for ts in self.termination_conds:
                    term = term and self.termination_conds[ts].is_satisfied()
            else:
                term = term and self.termination_conds[time_scale].is_satisfied()

            return term

        self.counts_useable = {node: {n: 0 for n in self.nodes} for node in self.nodes}
        self._reset_count(self.counts_total, TimeScale.TRIAL)
        self._reset_time(TimeScale.TRIAL)

        while not self.termination_conds[TimeScale.TRIAL].is_satisfied():
            self._reset_count(self.counts_total, TimeScale.PASS)
            self._reset_time(TimeScale.PASS)

            execution_list_has_changed = False
            cur_index_consideration_queue = 0

            while (
                cur_index_consideration_queue < len(self.consideration_queue)
                and not self.termination_conds[TimeScale.TRIAL].is_satisfied()
            ):
                # all nodes to be added during this time step
                cur_time_step_exec = set()
                # the current "layer/group" of nodes that MIGHT be added during this time step
                cur_consideration_set = self.consideration_queue[cur_index_consideration_queue]
                try:
                    iter(cur_consideration_set)
                except TypeError as e:
                    raise SchedulerError('cur_consideration_set is not iterable, did you ensure that this Scheduler was'
                                         ' instantiated with an actual toposort output for param toposort_ordering? '
                                         'err: {0}'.format(e))
                logger.debug('trial, num passes in trial {0}, consideration_queue {1}'.
                             format(self.times[TimeScale.TRIAL][TimeScale.PASS], ' '.
                                    join([str(x) for x in cur_consideration_set])))

                # do-while, on cur_consideration_set_has_changed
                # we check whether each node in the current consideration set is allowed to run,
                # and nodes can cause cascading adds within this set
                while True:
                    cur_consideration_set_has_changed = False
                    for current_node in cur_consideration_set:
                        logger.debug('cur time_step exec: {0}'.format(cur_time_step_exec))
                        for n in self.counts_useable:
                            logger.debug('Counts of {0} useable by'.format(n))
                            for n2 in self.counts_useable[n]:
                                logger.debug('\t{0}: {1}'.format(n2, self.counts_useable[n][n2]))

                        # only add each node once during a single time step, this also serves
                        # to prevent infinitely cascading adds
                        if current_node not in cur_time_step_exec:
                            if self.condition_set.conditions[current_node].is_satisfied():
                                logger.debug('adding {0} to execution list'.format(current_node))
                                logger.debug('cur time_step exec pre add: {0}'.format(cur_time_step_exec))
                                cur_time_step_exec.add(current_node)
                                logger.debug('cur time_step exec post add: {0}'.format(cur_time_step_exec))
                                execution_list_has_changed = True
                                cur_consideration_set_has_changed = True

                                for ts in TimeScale:
                                    self.counts_total[ts][current_node] += 1
                                # current_node's node is added to the execution queue, so we now need to
                                # reset all of the counts useable by current_node's node to 0
                                for n in self.counts_useable:
                                    self.counts_useable[n][current_node] = 0
                                # and increment all of the counts of current_node's node useable by other
                                # nodes by 1
                                for n in self.counts_useable:
                                    self.counts_useable[current_node][n] += 1
                    # do-while condition
                    if not cur_consideration_set_has_changed:
                        break

                # add a new time step at each step in a pass, if the time step would not be empty
                if len(cur_time_step_exec) >= 1:
                    self.execution_list.append(cur_time_step_exec)
                    yield self.execution_list[-1]

                    self._increment_time(TimeScale.TIME_STEP)

                cur_index_consideration_queue += 1

            # if an entire pass occurs with nothing running, add an empty time step
            if not execution_list_has_changed:
                self.execution_list.append(set())
                yield self.execution_list[-1]

                self._increment_time(TimeScale.TIME_STEP)

            # can execute the execution_list here
            logger.info(self.execution_list)
            logger.debug('Execution list: [{0}]'.format(' '.join([str(x) for x in self.execution_list])))
            self._increment_time(TimeScale.PASS)

        self._increment_time(TimeScale.TRIAL)

        return self.execution_list
