# -----------------------------------------------------------------------------
# BSD 3-Clause License
#
# Copyright (c) 2019-2021, Science and Technology Facilities Council
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
# Author: R. W. Ford, STFC Daresbury Lab.
# Modified by: A. R. Porter, STFC Daresbury Lab.

'''SIR PSyIR backend. Generates SIR code from PSyIR nodes. Currently
limited to PSyIR Kernel schedules as PSy-layer PSyIR already has a
gen() method to generate Fortran.

'''
from __future__ import absolute_import

import six

from psyclone.nemo import NemoLoop, NemoKern
from psyclone.psyir.backend.visitor import PSyIRVisitor, VisitorError
from psyclone.psyir.nodes import ArrayReference, BinaryOperation, Literal, \
    Reference, UnaryOperation
from psyclone.psyir.symbols import ScalarType

# Mapping from PSyIR data types to SIR types.
# SIR does not seem to support the Character datatype. Boolean does
# seem to be supported but there are no examples with the data value
# so we don't include it here.
# We do not yet deal with precision e.g. the SIR supports a DOUBLE
# type which would probably be equivalent to PSyIR's
# Precision.DOUBLE. This is the subject of issue #741.

TYPE_MAP_TO_SIR = {ScalarType.Intrinsic.REAL: "BuiltinType.Float",
                   ScalarType.Intrinsic.INTEGER: "BuiltinType.Integer"}


def gen_stencil(node):
    '''Given an array access as input, determine the form of stencil
    access and return it in the form expected by the SIR as a
    string. Raise an exception if the array access is not a recognised
    stencil access.

    *** SIR ALWAYS EXPECTS 3 ARGS ***

    :param node: an array access.
    :type node: :py:class:`psyclone.psyir.nodes.ArrayReference`

    :returns: the SIR stencil access format for the array access.
    :rtype: str

    :raises VisitorError: if the node is not the expected type or the \
    array access is not in a recognised stencil form.

    '''
    if not isinstance(node, ArrayReference):
        raise VisitorError(
            "gen_stencil expected an ArrayReference as input but found '{0}'."
            "".format(type(node)))
    dims = ["0", "0", "0"]
    for idx, child in enumerate(node.children):
        if isinstance(child, Reference):
            dims[idx] = "0" # *** Not needed now!!!
        elif isinstance(child, BinaryOperation):
            if isinstance(child.children[0], Reference) and \
               isinstance(child.children[1], Literal):
                if child.operator == BinaryOperation.Operator.SUB:
                    dims[idx] = "-"+child.children[1].value
                elif child.operator == BinaryOperation.Operator.ADD:
                    dims[idx] = child.children[1].value
                else:
                    raise VisitorError(
                        "gen_stencil unsupported stencil operator found "
                        "'{0}'. Expecting '+' or '-'."
                        "".format(child.operator.name))
            else:
                raise VisitorError(
                    "gen_stencil unsupported stencil index found '{0}'."
                    "".format(str(child)))
        else:
            raise VisitorError(
                "gen_stencil unsupported (non-stencil) index found '{0}'."
                "".format(str(child)))
    return "[{0}]".format(", ".join(dims))


class SIRWriter(PSyIRVisitor):
    '''Implements a PSyIR-to-SIR back end for PSyIR kernel code (not
    currently PSyIR PSy-layer code which has its own gen method for
    generating Fortran).

    :param bool skip_nodes: if skip_nodes is False then an exception \
    is raised if a visitor method for a PSyIR node has not been \
    implemented, otherwise the visitor continues, printing out a \
    representation of the unsupported node. This is an optional \
    argument which defaults to False.
    :param str indent_string: specifies what to use for indentation. This \
    is an optional argument that defaults to two spaces.
    :param int initial_indent_depth: Specifies how much indentation to \
    start with. This is an optional argument that defaults to 0.

    '''
    def __init__(self, skip_nodes=False, indent_string="  ",
                 initial_indent_depth=0):
        super(SIRWriter, self).__init__(skip_nodes, indent_string,
                                        initial_indent_depth)
        # The _field_names variable stores the unique field names
        # found in the PSyIR. This is required as the SIR declares
        # field names after the computation.
        self._field_names = set()
        self._fields = {}
        # The _scalar_names variable stores the unique scalar names
        # found in the PSyIR. The current assumption is that scalars
        # are temporaries. This is not necessarily correct and this
        # problem is captured in issue #521. Scalar temporaries can be
        # declared as field temporaries as the Dawn backend works out
        # what is required.
        self._scalar_names = set()
        self._scalars = {}

    def node_node(self, node):
        '''Catch any unsupported nodes, output their class names and continue
        down the node hierarchy (if skip_node is set to True). This is
        useful for debugging and differs from the base class
        implementation of skip_nodes which silently continues. If
        skip_nodes is set to False then raise an exception if an
        unsupported node is found.

        :param node: an unsupported PSyIR node.
        :type node: subclass of :py:class:`psyclone.psyir.nodes.Node`

        :returns: the SIR Python code.
        :rtype: str

        :raises VisitorError: if skip_nodes is set to False.

        '''
        if not self._skip_nodes:
            raise VisitorError(
                "Class SIRWriter method node_node(), unsupported node "
                "found '{0}'".format(type(node)))
        result = "{0}[ {1} start ]\n".format(self._nindent,
                                             type(node).__name__)
        self._depth += 1
        for child in node.children:
            result += self._visit(child)
        self._depth -= 1
        result += "{0}[ {1} end ]\n".format(self._nindent, type(node).__name__)
        return result

    def nemoloop_node(self, loop_node):
        '''Supported NEMO loops are triply nested with particular indices (not
        yet checked) and should contain a NemoKern. If this is not the
        case then it is not possible to translate so an exception is
        raised.

        :param loop_node: a NemoLoop PSyIR node.
        :type loop_node: subclass of :py:class:`psyclone.nemo.NemoLoop`

        :returns: the SIR Python code.
        :rtype: str

        :raises VisitorError: if the loop is not triply nested with \
        computation within the triply nested loop.

        '''
        def create_make_interval(loop, upper_bound_name):
            ''' xxx '''
            def bound_value(expr):
                if isinstance(expr, Literal):
                    return int(expr.value)
                else:
                    raise TypeError()

            def bound_name_offset(expr, name):
                ''' xxx '''
                if isinstance(expr, Reference) and expr.name == name:
                    return 0
                elif isinstance(expr, BinaryOperation) and isinstance(expr.children[0], Reference) and expr.children[0].name == name:
                    if expr.operator == BinaryOperation.Operator.SUB:
                        value = bound_value(expr.children[1])
                        return value * -1
                    else:
                        print ("Operator not supported {0}".format(type(expr.children[1])))
                        exit(1)
                else:
                    print ("bounds not supported", expr, name)
                    exit(1)

            # Lower bound
            try:
                value = bound_value(loop.start_expr)
                lower_bound_offset = value - 1
                lower_bound_str = "Interval.Start"
            except TypeError:
                try:
                    lower_bound_offset = bound_name_offset(loop.start_expr, upper_bound_name)
                    lower_bound_str = "Interval.End"
                except TypeError:
                    print ("Unsupported lower bound found".format(loop.start_expr))
                    exit(1)
            # Upper bound
            try:
                value = bound_value(loop.stop_expr)
                upper_bound_offset = 0
                upper_bound_str = str(value)
            except TypeError:
                try:
                    upper_bound_offset = bound_name_offset(loop.stop_expr, upper_bound_name)
                    upper_bound_str = "Interval.End"
                except TypeError:
                    print ("Unsupported upper bound found {0}".format(loop.stop_expr))
                    exit(1)
            # print ("upper bound is {0}".format(loop.stop_expr))
            # print ("step is {0}".format(loop.step_expr))
            # print ("lower", loop.start_expr, lower_bound_str, str(lower_bound_offset))
            # print ("upper", loop.stop_expr, upper_bound_str, str(upper_bound_offset))
            return "make_interval({0}, {1}, {2}, {3})".format(
                lower_bound_str, upper_bound_str, lower_bound_offset, upper_bound_offset)

        # Check first loop has a single loop as a child.
        k_loop = loop_node
        loop_content = k_loop.loop_body.children
        if not (len(loop_content) == 1 and
                isinstance(loop_content[0], NemoLoop)):
            raise VisitorError("Child of loop should be a single loop.")

        # Check second loop has a single loop as a child.
        j_loop = loop_content[0]
        loop_content = j_loop.loop_body.children
        if not (len(loop_content) == 1 and
                isinstance(loop_content[0], NemoLoop)):
            raise VisitorError(
                "Child of child of loop should be a single loop.")

        # Check third loop has a single NemoKern as a child.
        i_loop = loop_content[0]
        loop_content = i_loop.loop_body.children
        if not (len(loop_content) == 1 and
                isinstance(loop_content[0], NemoKern)):
            raise VisitorError(
                "Child of child of child of loop should be a NemoKern.")

        # Create the intervals
        make_k_interval_str = create_make_interval(k_loop, "jpk")
        make_j_interval_str = create_make_interval(j_loop, "jpj")
        make_i_interval_str = create_make_interval(i_loop, "jpi")

        result = ("{0}k_interval = {1}\n".format(
            self._nindent, make_k_interval_str))
        result += ("{0}body_ast = make_ast([\n".format(self._nindent))
        self._depth += 1
        result += self.nemokern_node(loop_content[0])
        self._depth -= 1
        # Remove the trailing comma if there is one as this is the
        # last entry in make_ast.
        result = result.rstrip(",\n") + "\n"
        result += "{0}])\n".format(self._nindent)
        # For the moment there is a hard coded assumption that the
        # vertical looping is in the forward (1..n) direction (see
        # #470).
        result += (
            "{0}vertical_region_fns.append(make_vertical_region_decl_stmt("
            "body_ast, k_interval, VerticalRegion.Forward, IRange={1}, JRange={2}))\n"
            "".format(self._nindent, make_i_interval_str, make_j_interval_str))
        return result

    def nemokern_node(self, node):
        '''NEMO kernels are a group of nodes collected into a schedule
        so simply visit the nodes in the schedule.

        :param node: a NemoKern PSyIR node.
        :type node: :py:class:`psyclone.nemo.NemoKern`

        :returns: the SIR Python code.
        :rtype: str

        '''
        result = ""
        schedule = node.get_kernel_schedule()
        for child in schedule.children:
            result += self._visit(child)
        return result

    def nemoinvokeschedule_node(self, node):
        '''This method is called when a NemoInvokeSchedule instance is found
        in the PSyIR tree.

        :param node: a KernelSchedule PSyIR node.
        :type node: :py:class:`psyclone.psyir.nodes.KernelSchedule`

        :returns: the SIR Python code.
        :rtype: str

        '''
        result = "# PSyclone autogenerated SIR Python\n\n"
        result += "from dawn4py.serialization.utils import *\n"
        result += ("from dawn4py.serialization.AST import Interval, "
                   "VerticalRegion, BuiltinType\n")
        result += "from dawn4py.serialization import AST\n"
        result += "import dawn4py\n\n"
        result += "vertical_region_fns = []\n"
        # The stencil name is currently hardcoded.
        result += "stencil_name = \"psyclone\"\n"

        exec_statements = ""
        for child in node.children:
            exec_statements += self._visit(child)
        result += "{0}\n".format(exec_statements)
        # The file name is hard coded at the moment.
        result += (
            "{0}sir = make_sir(stencil_name+\".cpp\", "
            "AST.GridType.Value(\"Cartesian\"), [\n"
            "{0}{1}make_stencil(\n"
            "{0}{1}{1}stencil_name,\n"
            "{0}{1}{1}make_ast(vertical_region_fns),\n"
            "{0}{1}{1}[".format(self._nindent, self._indent))
        functions = []
        for name in self._field_names:
            # field reference is ArrayReference
            field_ref = self._fields[name]
            # symbol is DataSymbol
            data_symbol = field_ref.symbol
            # symbol is an array
            assert data_symbol.is_array
            # symbol dimensions ...
            shape = data_symbol.shape
            number_of_dims = len(shape)
            # Hack for the moment
            if number_of_dims == 3:
                dims = "[1, 1, 1]"
            elif number_of_dims == 2:
                dims = "[1, 1, 0]"
            elif number_of_dims == 1:
                dims = "[0, 0, 1]"
            else:
                raise Exception("Unexpected number of dimensions")
            temporary_text = ""
            if data_symbol.is_local:
                temporary_text = ", is_temporary=True"
            functions.append(
                "make_field(\"{0}\", make_field_dimensions_cartesian({1}){2})"
                "".format(name, dims, temporary_text))
        # Scalar temporaries can be declared as field temporaries as
        # the Dawn backend works out what is required.
        for name in self._scalar_names:
            # scalar_ref is Reference
            scalar_ref = self._scalars[name]
            # symbol is DataSymbol
            data_symbol = scalar_ref.symbol
            # symbol is a scalar
            assert data_symbol.is_scalar
            temporary_text = ""
            if data_symbol.is_local:
                temporary_text = ", is_temporary=True"
            functions.append(
                "make_field(\"{0}\", make_field_dimensions_cartesian([1, 0, 0]){1})"
                "".format(name, temporary_text))
        result += ", ".join(functions)
        result += "]\n"
        result += (
            "{0}{1})\n"
            "{0}])\n".format(self._nindent, self._indent))

        result += (
            "# code = dawn4py.compile(sir, "
            "backend=dawn4py.CodeGenBackend.CXXNaive)\n"
            "code = dawn4py.compile(sir, "
            "backend=dawn4py.CodeGenBackend.CUDA)\n"
            "# code = dawn4py.compile(sir, "
            "backend=dawn4py.CodeGenBackend.GridTools)\n")
        result += "print (code)"

        return result

    def assignment_node(self, node):
        '''This method is called when an Assignment instance is found in the
        PSyIR tree.

        :param node: an Assignment PSyIR node.
        :type node: :py:class:`psyclone.psyir.nodes.Assignment``

        :returns: the SIR Python code.
        :rtype: str

        '''
        self._depth += 1
        lhs = self._visit(node.lhs)
        rhs = self._visit(node.rhs)
        self._depth -= 1
        result = ("{0}make_assignment_stmt(\n{1},\n{2}"
                  "".format(self._nindent, lhs, rhs))
        # For better formatting, remove the newline if one exists.
        result = result.rstrip("\n")
        result += ",\n"
        result += "{0}{1}\"=\"),\n".format(self._nindent, self._indent)
        return result

    def binaryoperation_node(self, node):
        '''This method is called when a BinaryOperation instance is found in
        the PSyIR tree.

        :param node: a BinaryOperation PSyIR node.
        :type node: :py:class:`psyclone.psyir.nodes.BinaryOperation`

        :returns: the SIR Python code.
        :rtype: str

        :raises VisitorError: if there is no mapping from the PSyIR \
        operator to SIR.

        '''
        binary_operators = {
            BinaryOperation.Operator.ADD: '+',
            BinaryOperation.Operator.SUB: '-',
            BinaryOperation.Operator.MUL: '*',
            BinaryOperation.Operator.DIV: '/',
            BinaryOperation.Operator.POW: '**',
            BinaryOperation.Operator.EQ: '==',
            BinaryOperation.Operator.NE: '!=',
            BinaryOperation.Operator.LE: '<=',
            BinaryOperation.Operator.LT: '<',
            BinaryOperation.Operator.GE: '>=',
            BinaryOperation.Operator.GT: '>',
            BinaryOperation.Operator.AND: '&&',
            BinaryOperation.Operator.OR: '||'}

        self._depth += 1
        lhs = self._visit(node.children[0])
        try:
            oper = binary_operators[node.operator]
        except KeyError as err:
            six.raise_from(VisitorError(
                "Method binaryoperation_node in class SIRWriter, unsupported "
                "operator '{0}' found.".format(str(node.operator))),
                err)
        rhs = self._visit(node.children[1])
        self._depth -= 1
        result = "{0}make_binary_operator(\n{1}".format(self._nindent, lhs)
        # For better formatting, remove the newline if one exists.
        result = result.rstrip("\n")
        result += ",\n"
        result += ("{0}{1}\"{2}\",\n{3}\n{0}{1})\n"
                   "".format(self._nindent, self._indent, oper, rhs))
        return result

    def reference_node(self, node):
        '''This method is called when a Reference instance is found in the
        PSyIR tree.

        :param node: a Reference PSyIR node.
        :type node: :py:class:`psyclone.psyir.nodes.Reference`

        :returns: the SIR Python code.
        :rtype: str

        :raises VisitorError: if this node has children.

        '''
        if node.children:
            raise VisitorError(
                "Method reference_node in class SIRWriter: SIR Reference "
                "node is not expected to have any children.")
        # _scalar_names is a set so duplicates will be ignored. It
        # captures all unique scalar names as scalars are currently
        # treated as temporaries (#521 captures this). The simplest
        # way to declare a scalar temporary in Dawn is to treat it as
        # a field temporary (as the Dawn backend works out if a scalar
        # is required).
        self._scalar_names.add(node.name)
        self._scalars[node.name] = node

        return "{0}make_field_access_expr(\"{1}\")".format(self._nindent,
                                                           node.name)

    def arrayreference_node(self, node):
        '''This method is called when an ArrayReference instance is found in
        the PSyIR tree.

        :param node: an ArrayReference PSyIR node.
        :type node: :py:class:`psyclone.psyir.nodes.ArrayReference`

        :returns: the SIR Python code.
        :rtype: str

        '''
        stencil = gen_stencil(node)
        result = ("{0}make_field_access_expr(\"{1}\", {2})"
                  "".format(self._nindent, node.name, stencil))
        # _field_names is a set so duplicates will be ignored. It
        # captures all unique field names as the SIR declares field
        # names after the computation.
        self._field_names.add(node.name)
        self._fields[node.name] = node
        return result

    def literal_node(self, node):
        '''This method is called when a Literal instance is found in the PSyIR
        tree.

        :param node: a Literal PSyIR node.
        :type node: :py:class:`psyclone.psyir.nodes.Literal`

        :returns: the SIR Python code.
        :rtype: str

        '''
        result = node.value
        try:
            datatype = TYPE_MAP_TO_SIR[node.datatype.intrinsic]
        except KeyError as err:
            six.raise_from(VisitorError(
                "PSyIR type '{0}' has no representation in the SIR backend."
                "".format(str(node.datatype))),
                err)

        return ("{0}make_literal_access_expr(\"{1}\", {2})"
                "".format(self._nindent, result, datatype))

    def unaryoperation_node(self, node):
        '''This method is called when a UnaryOperation instance is found in
        the PSyIR tree.

        :param node: a UnaryOperation PSyIR node.
        :type node: :py:class:`psyclone.psyir.nodes.UnaryOperation`

        :returns: the SIR Python code.
        :rtype: str

        :raises VisitorError: if there is no mapping from the PSyIR \
        operator to SIR, or if the child of the PSyIR operator is not \
        a literal (as only -<literal> is currently supported).

        '''
        # Currently only '-' is supported in the SIR mapping.
        unary_operators = {
            UnaryOperation.Operator.MINUS: '-'}
        try:
            oper = unary_operators[node.operator]
        except KeyError as err:
            six.raise_from(VisitorError(
                "Method unaryoperation_node in class SIRWriter, unsupported "
                "operator '{0}' found.".format(str(node.operator))),
                err)
        if isinstance(node.children[0], Literal):
            # The unary minus operator is being applied to a
            # literal. This is a special case as the literal value can
            # be negative in SIR.
            literal = node.children[0]
            if literal.datatype.intrinsic not in [
                    ScalarType.Intrinsic.REAL, ScalarType.Intrinsic.INTEGER]:
                # The '-' operator can only be applied to REAL and INTEGER
                # datatypes.
                raise VisitorError(
                    "PSyIR type '{0}' does not work with the '-' operator."
                    "".format(str(literal.datatype)))
            result = literal.value
            datatype = TYPE_MAP_TO_SIR[literal.datatype.intrinsic]
            return ("{0}make_literal_access_expr(\"{1}{2}\", {3})"
                    "".format(self._nindent, oper, result, datatype))

        # The unary minus operator is being applied to something that
        # is not a literal. Default to REAL as we currently have no
        # way of finding out the type, see issue #658. Replace -x with
        # -1.0 * x.
        datatype = TYPE_MAP_TO_SIR[ScalarType.Intrinsic.REAL]
        self._depth += 1
        lhs = "{0}make_literal_access_expr(\"-1.0\", {1})".format(
            self._nindent, datatype)
        operator = "{0}\"*\"".format(self._nindent)
        rhs = self._visit(node.children[0])
        self._depth -= 1
        result = "{0}make_binary_operator(\n{1},\n{2},\n{3})\n".format(
            self._nindent, lhs, operator, rhs)
        return result

    def ifblock_node(self, node):
        '''This method is called when an IfBlock instance is found in
        the PSyIR tree.

        :param node: an IfBlock PSyIR node.
        :type node: :py:class:`psyclone.psyir.nodes.IfBlock`

        :returns: SIR Python code.
        :rtype: str

        '''
        cond_expr = self._visit(node.condition)
        cond_part = ("make_expr_stmt({0})"
                     "".format(cond_expr.lstrip().rstrip(",\n")))

        then_statements = self._visit(node.if_body).lstrip().rstrip(",\n")
        then_part = "make_block_stmt([{0}])".format(then_statements)

        if node.else_body:
            else_statements = self._visit(node.else_body)
            else_part = ("make_block_stmt([{0}])"
                         "".format(else_statements.lstrip().rstrip(",\n")))
        else:
            else_part = "None"

        return ("{0}make_if_stmt({1}, {2}, {3}),\n"
                "".format(self._nindent, cond_part, then_part, else_part))

    def schedule_node(self, node):
        '''This method is called when a Schedule instance is found in the
        PSyIR tree. A Schedule instance captures an ordered sequence
        of PSyIR nodes and is therefore found in places such as the
        contents of the 'then' part of an 'if' statement and the
        contents of the 'else' part of an 'if' statement. The schedule
        has no content so simply calls its children and returns the
        agregated result.

        :param node: a Schedule PSyIR node.
        :type node: :py:class:`psyclone.psyir.nodes.Schedule`

        :returns: the SIR Python code.
        :rtype: str

        '''
        result = ""
        for child in node.children:
            result += self._visit(child)
        return result
