# -----------------------------------------------------------------------------
# BSD 3-Clause License
#
# Copyright (c) 2021, Science and Technology Facilities Council.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# -----------------------------------------------------------------------------
# Author: A. R. Porter, STFC Daresbury Lab

'''
This module provides the ACCUpdateTrans transformation that ensures that
data is kept up-to-date on the host.
'''

from __future__ import absolute_import
from psyclone.configuration import Config
from psyclone.psyir.nodes import (Call, IfBlock, Loop, Schedule, Operation,
                                  BinaryOperation, ACCKernelsDirective,
                                  ACCParallelDirective, ACCUpdateDirective,
                                  ACCEnterDataDirective)
from psyclone.psyir.tools import DependencyTools
from psyclone.psyGen import Transformation


class ACCUpdateTrans(Transformation):
    '''
    Examines the supplied Schedule and adds "acc update" directives
    for any data accessed outside of a kernels or parallel region.

    '''
    def __init__(self):
        # Perform some set-up required by the recursive routine.
        self._dep_tools = DependencyTools()
        # We treat a Call as being a (potential) ACC region because we
        # don't know what happens within it.
        self._acc_region_nodes = (ACCParallelDirective, ACCKernelsDirective,
                                  Call)
        loop_type_mapping = Config.get().api_conf("nemo") \
                                        .get_loop_type_mapping()
        self._loop_vars = loop_type_mapping.keys()

        super().__init__()

    def validate(self, node, options=None):
        '''
        Checks that it is valid to apply this transformation to the supplied
        schedule.

        :param node: the Schedule that is to be transformed.
        :type node: :py:class:`psyclone.psyir.nodes.Schedule`
        :param options: any options to this transformation.
        :type options: dict

        :raises TransformationError: if the supplied node is not a Schedule.

        '''
        if not isinstance(node, Schedule):
            # transformations module file needs moving into the psyir
            # hierarchy.
            # pylint: disable=import-outside-toplevel
            from psyclone.transformations import TransformationError
            raise TransformationError(f"Expected a Schedule but got a node of "
                                      f"type '{type(node).__name__}'")
        super().validate(node, options)

    def apply(self, node, options=None):
        '''
        Applies this transformation to the supplied Schedule. Identifies any
        regions of code outside of ACC regions and adds the necessary ACC
        update directives to ensure that the host and device copies of any
        variables are kept up-to-date.

        :param node: the Schedule that is to be transformed.
        :type node: :py:class:`psyclone.psyir.nodes.Schedule`
        :param options: any options to this transformation.
        :type options: dict

        '''
        self.validate(node, options)
        # Call the routine that recursively adds updates to all Schedules
        # within the supplied Schedule.
        self.add_updates(node)

    def add_updates(self, sched):
        '''
        Recursively identify those statements that are not being executed
        on the GPU and add any required OpenACC update directives.

        :param sched: the schedule of statements to process.
        :type sched: :py:class:`psyclone.psyir.nodes.Schedule`

        '''
        # We must walk through the Schedule and find those nodes that are
        # not within a kernels or parallel region.
        node_list = []
        for child in sched.children[:]:
            if isinstance(child, ACCEnterDataDirective):
                continue
            if not child.walk(self._acc_region_nodes):
                node_list.append(child)
            else:
                if node_list:
                    self._add_update_directives(sched, node_list)
                    node_list = []
                if isinstance(child, Call):
                    ops = child.walk(Operation)
                    if any(op.operator not in [BinaryOperation.Operator.LBOUND,
                                               BinaryOperation.Operator.UBOUND]
                           for op in ops):
                        raise NotImplementedError("ARPDBG4")
                if isinstance(child, (IfBlock, Loop)):
                    # TODO: Update node_list with nodes from IfBlock condition
                    # or Loop bounds/step
                    if isinstance(child, IfBlock):
                        self._add_update_directives(sched, [child.condition])
                        # Recurse down
                        self.add_updates(child.if_body)
                        if child.else_body:
                            self.add_updates(child.else_body)
        # We've reached the end of the list of children - are there any
        # last nodes that represent computation on the CPU?
        if node_list:
            self._add_update_directives(sched, node_list)

    def _add_update_directives(self, sched, node_list):
        '''
        Adds the required update directives before and after the nodes in
        the supplied list.

        :param sched: the schedule which contains the nodes in node_list.
        :type sched: :py:class:`psyclone.psyir.nodes.Schedule`
        :param node_list: the PSyIR nodes representing code executed on the \
                          CPU rather than the GPU.
        :type node_list: list of :py:class:`psyclone.psyir.nodes.Node`

        '''
        inputs, outputs = self._dep_tools.get_in_out_parameters(node_list)
        parent = sched
        # Copy any data that is read by this region to the host if it is
        # on the GPU.
        if inputs:
            first_child = node_list[0]
            while first_child not in parent.children:
                first_child = first_child.parent
            for sig in inputs:
                if sig.is_structure:
                    raise NotImplementedError("ARPDBG2")
                if sig.var_name in self._loop_vars:
                    continue
                sym = sched.symbol_table.lookup(sig.var_name)
                update_dir = ACCUpdateDirective(sym, "host")
                parent.addchild(update_dir,
                                parent.children.index(first_child))
        # Copy any data that is written by this region back to the GPU.
        if outputs:
            last_child = node_list[-1]
            while last_child not in parent.children:
                last_child = last_child.parent
            for sig in outputs:
                if sig.is_structure:
                    raise NotImplementedError("ARPDBG3")
                sym = sched.symbol_table.lookup(sig.var_name)
                if sig.var_name in self._loop_vars:
                    continue
                update_dir = ACCUpdateDirective(sym, "device")
                parent.addchild(update_dir,
                                parent.children.index(last_child)+1)
