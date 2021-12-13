# Princeton University licenses this file to You under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.  You may obtain a copy of the License at:
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.


# **************************************  CompositionInterfaceMechanism *************************************************

"""

Contents
--------

  * `CompositionInterfaceMechanism_Overview`
  * `CompositionInterfaceMechanism_Creation`
  * `CompositionInterfaceMechanism_Structure`
  * `CompositionInterfaceMechanism_Execution`
  * `CompositionInterfaceMechanism_Class_Reference`


.. _CompositionInterfaceMechanism_Overview:

Overview
--------

CompositionInterfaceMechanisms act as interfaces between a `Composition` and its inputs from and outputs to the
environment, or the Components of another Composition within which it is `nested <Composition_Nested>`. They are
created automatically for a Composition when it is constructed and executed when it is run.  They should never be
constructed or executed manually.  They can be seen graphically using the `show_cim <ShowGraph.show_cim>` option of
the Composition's `show_graph <ShowGraph_show_graph_Method>` method.

.. _CompositionInterfaceMechanism_Creation:

Creation of CompositionInterfaceMechanisms
------------------------------------------

The following three CompositionInterfaceMechanisms are created automatically for a Composition when it is
constructed (and should never be constructed manually):

* `input_CIM <Composition.input_CIM>` - this is assigned an `InputPort` and `OutputPort` for every `INPUT
  <NodeRole.INPUT>` `Node <Composition_Nodes>` of the Composition to which it belongs. The InputPorts receive input
  from either the environment or a Composition within which it is nested. If the Composition is itself an
  `INPUT <NodeRole.INPUT>` Node of an enclosing Composition, then its input must be included in the `inputs
  <Composition_Execution_Inputs>` to that Composition when it is `executed <Composition_Execution>`. Every InputPort
  of an input_CIM is associated with an OutputPort that projects to a corresponding `INPUT <NodeRole.INPUT>` Node
  of the Composition.

* `parameter_CIM <Composition.parameter_CIM>` - XXX

* `output_CIM <Composition.output_CIM>` - this is assigned an `InputPort` and `OutputPort` for every `OUTPUT
  <NodeRole.OUTPUT>` `Node <Composition_Nodes>` of the Composition to which it belongs. Each InputPort receives input
  from an `OUTPUT <NodeRole.OUTPUT>` Node of the Composition, and its `value <InputPort.value>` is assigned as the
  `value <OutputPort.value>` of a corresponding OutputPort.  The latter are assigned to the `output_values
  <Composition.output_values>` and `results <Composition.results>` attributes of the Composition.  If the Composition
  is `nested <Composition_Nested>` within another, then the output_CIM's `output_ports <Mechanism_Base.output_ports>`
  send Projections to Components of the Composition within which it is nested.  If it is an `OUTPUT <NodeRole.OUTPUT>`
  Node of the enclosing Composition, then its OutputPorts project the `output_CIM <Composition.output_CIM>` of the
  enclosing Composition, its `output_values <Composition.output_values>` are included in those of the enclosing
  Composition.
  COMMENT:
  **MENTION PROBES HERE**
  COMMENT

.. _CompositionInterfaceMechanism_Structure:

Structure
---------

[TBD]

.. _CompositionInterfaceMechanism_Execution:

Execution
---------

[TBD]

.. _CompositionInterfaceMechanism_Class_Reference:

Class Reference
---------------

"""

import warnings
import typecheck as tc

from collections.abc import Iterable

from psyneulink.core.components.functions.nonstateful.transferfunctions import Identity
from psyneulink.core.components.mechanisms.mechanism import Mechanism
from psyneulink.core.components.mechanisms.processing.processingmechanism import ProcessingMechanism_Base
from psyneulink.core.components.ports.inputport import InputPort
from psyneulink.core.components.ports.modulatorysignals.controlsignal import ControlSignal
from psyneulink.core.components.ports.outputport import OutputPort
from psyneulink.core.globals.context import ContextFlags, handle_external_context
from psyneulink.core.globals.keywords import COMPOSITION_INTERFACE_MECHANISM, INPUT_PORTS, OUTPUT_PORTS, PREFERENCE_SET_NAME
from psyneulink.core.globals.parameters import Parameter
from psyneulink.core.globals.preferences.basepreferenceset import is_pref_set, REPORT_OUTPUT_PREF
from psyneulink.core.globals.preferences.preferenceset import PreferenceEntry, PreferenceLevel

__all__ = ['CompositionInterfaceMechanism']


class CompositionInterfaceMechanism(ProcessingMechanism_Base):
    """
    CompositionInterfaceMechanism(  \
        function=Identity())

    Subclass of `ProcessingMechanism <ProcessingMechanism>` that acts as interface between a Composition and its
    inputs from and outputs to the environment or other Mechanisms (if it is a nested Composition).

    See `Mechanism <Mechanism_Class_Reference>` for arguments and additional attributes.

    Attributes
    ----------

    function : InterfaceFunction : default Identity
        the function used to transform the variable before assigning it to the Mechanism's OutputPort(s)

    """

    componentType = COMPOSITION_INTERFACE_MECHANISM
    outputPortTypes = [OutputPort, ControlSignal]

    classPreferenceLevel = PreferenceLevel.TYPE
    # These will override those specified in TYPE_DEFAULT_PREFERENCES
    classPreferences = {
        PREFERENCE_SET_NAME: 'CompositionInterfaceMechanismCustomClassPreferences',
        REPORT_OUTPUT_PREF: PreferenceEntry(False, PreferenceLevel.INSTANCE)}

    class Parameters(ProcessingMechanism_Base.Parameters):
        """
            Attributes
            ----------

                function
                    see `function <CompositionInterfaceMechanism.function>`

                    :default value: `Identity`
                    :type: `Function`
        """
        function = Parameter(Identity, stateful=False, loggable=False)

    @tc.typecheck
    def __init__(self,
                 default_variable=None,
                 size=None,
                 input_ports: tc.optional(tc.optional(tc.any(Iterable, Mechanism, OutputPort, InputPort))) = None,
                 function=None,
                 composition=None,
                 port_map=None,
                 params=None,
                 name=None,
                 prefs:is_pref_set=None):

        if default_variable is None and size is None:
            default_variable = self.class_defaults.variable
        self.composition = composition
        self.port_map = port_map
        self.connected_to_composition = False
        self.user_added_ports = {
            INPUT_PORTS: set(),
            OUTPUT_PORTS: set()
        }
        super(CompositionInterfaceMechanism, self).__init__(default_variable=default_variable,
                                                            size=size,
                                                            input_ports=input_ports,
                                                            function=function,
                                                            params=params,
                                                            name=name,
                                                            prefs=prefs,
                                                            )

    @handle_external_context()
    def add_ports(self, ports, context=None):
        ports = super(CompositionInterfaceMechanism, self).add_ports(ports, context=context)
        if context.source == ContextFlags.COMMAND_LINE:
            warnings.warn(
                'You are attempting to add custom ports to a CIM, which can result in unpredictable behavior and '
                'is therefore recommended against. If suitable, you should instead add ports to the mechanism(s) '
                'that project to or are projected to from the CIM.')
            if ports[INPUT_PORTS]:
                self.user_added_ports[INPUT_PORTS].update([port for port in ports[INPUT_PORTS].data])
            if ports[OUTPUT_PORTS]:
                self.user_added_ports[OUTPUT_PORTS].update([port for port in ports[OUTPUT_PORTS].data])
        return ports

    @handle_external_context()
    def remove_ports(self, ports, context=None):
        super(CompositionInterfaceMechanism, self).remove_ports(ports, context)
        input_ports_marked_for_deletion = set()
        for port in self.user_added_ports[INPUT_PORTS]:
            if port not in self.input_ports:
                input_ports_marked_for_deletion.add(port)
        self.user_added_ports[INPUT_PORTS] = self.user_added_ports[INPUT_PORTS] - input_ports_marked_for_deletion
        output_ports_marked_for_deletion = set()
        for port in self.user_added_ports[OUTPUT_PORTS]:
            if port not in self.output_ports:
                output_ports_marked_for_deletion.add(port)
        self.user_added_ports[OUTPUT_PORTS] = self.user_added_ports[OUTPUT_PORTS] - output_ports_marked_for_deletion

    def _get_destination_node_for_input_port(self, input_port, comp):
        """Return Port, Node and Composition for destination of projection from input_CIM to (possibly nested) node"""
        #  CIM MAP ENTRIES:  [RECEIVER PORT,  [input_CIM InputPort,  input_CIM OutputPort]]
        from psyneulink.core.compositions.composition import NodeRole
        # Get sender to input_port of CIM for corresponding output_port
        port_map = input_port.owner.port_map
        output_port = [port_map[k][1] for k in port_map if port_map[k][0] is input_port]
        assert len(output_port)==1, f"PROGRAM ERROR: Expected only 1 output_port for {input_port.name} " \
                                   f"in port_map for {input_port.owner}; found {len(output_port)}."
        assert len(output_port[0].efferents)==1, f"PROGRAM ERROR: Port ({output_port.name}) expected to have " \
                                                 f"just one efferet; has {len(output_port.efferents)}."
        receiver = output_port[0].efferents[0].receiver
        if not isinstance(receiver.owner, CompositionInterfaceMechanism):
            return receiver, receiver.owner, comp
        return self._get_destination_node_for_input_port(receiver, receiver.owner.composition)

    def _get_source_node_for_output_port(self, output_port, comp):
        """Return Port, Node and Composition  for source of projection to output_CIM from (possibly nested) node"""
        #  CIM MAP ENTRIES:  [SENDER PORT,  [output_CIM InputPort,  output_CIM OutputPort]]
        from psyneulink.core.compositions.composition import NodeRole
        # Get sender to input_port of CIM for corresponding output_port
        port_map = output_port.owner.port_map
        input_port = [port_map[k][0] for k in port_map if port_map[k][1] is output_port]
        assert len(input_port)==1, f"PROGRAM ERROR: Expected only 1 input_port for {output_port.name} " \
                                   f"in port_map for {output_port.owner}; found {len(input_port)}."
        assert len(input_port[0].path_afferents)==1, f"PROGRAM ERROR: Port ({input_port.name}) expected to have " \
                                                     f"just one path_afferent; has {len(input_port.path_afferents)}."
        sender = input_port[0].path_afferents[0].sender
        if not isinstance(sender.owner, CompositionInterfaceMechanism):
            return sender, sender.owner, comp
        return self._get_source_node_for_output_port(sender, sender.owner.composition)

    def _sender_is_probe(self, output_port):
        """Return True if source of output_port is a PROBE Node of the Composition to which it belongs"""
        from psyneulink.core.compositions.composition import NodeRole
        port, node, comp = self._get_source_node_for_output_port(output_port, self.composition)
        return NodeRole.PROBE in comp.get_roles_by_node(node)
