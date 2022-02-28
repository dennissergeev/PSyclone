# -----------------------------------------------------------------------------
# BSD 3-Clause License
#
# Copyright (c) 2021, Science and Technology Facilities Council
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
# Author R. W. Ford, STFC Daresbury Lab
# Modified by S. Siso, STFC Daresbury Lab

'''Module containing tests for the translation of PSyIR to PSyclone
Algorithm PSyIR.

'''
from __future__ import absolute_import
import pytest

from psyclone.psyir.frontend.fortran import FortranReader
from psyclone.psyir.transformations import TransformationError
from psyclone.psyir.nodes import Call, CodeBlock, Reference, \
    ArrayReference, Literal, BinaryOperation
from psyclone.psyir.symbols import RoutineSymbol, DataTypeSymbol, Symbol, \
    StructureType

from psyclone.domain.common.algorithm import \
    AlgorithmInvokeCall, KernelFunctor
from psyclone.domain.common.transformations import InvokeCallTrans


def check_reference(klr, name, arg_name):
    '''Utility routine that checks that the kernel layer metadata
    reference argument has the expected structure if its argument is a
    reference.

    :param klr: the KernelFunctor node being tested.
    :type klr: :py:class:`psyclone.domain.common.algorithm.KernelFunctor`
    :param str name: the name of the symbol within a reference that is \
        an argument to klr.
    :param str arg_name: the name of the argument passed to the ..
        an argument to klr.

    '''
    assert isinstance(klr, KernelFunctor)
    assert klr.symbol.name == name
    assert len(klr.children) == 1
    arg = klr.children[0]
    assert isinstance(arg, Reference)
    assert arg.symbol.name == arg_name


def check_literal(klr, name, arg_value):
    '''Utility routine that checks that the kernel layer metadata
    reference argument has the expected structure if its argument is a
    literal.

    :param klr: the KernelFunctor node being tested.
    :type klr: :py:class:`psyclone.domain.common.algorithm.KernelFunctor`

    :param str value: the value of the literal that is an argument to klr.

    '''
    assert isinstance(klr, KernelFunctor)
    assert klr.symbol.name == name
    assert len(klr.children) == 1
    arg = klr.children[0]
    assert isinstance(arg, Literal)
    assert arg.value == arg_value


def test_init():
    '''Check that an InvokeCallTrans instance can be created correctly,
    has the expected defaults, deals with any __init__ arguments and
    its name method returns the expected value.

    '''
    invoke_trans = InvokeCallTrans()
    assert invoke_trans.name == "InvokeCallTrans"
    assert isinstance(invoke_trans, InvokeCallTrans)
    assert invoke_trans._call_name is None


def test_parse_args_get_symbol(fortran_reader):
    '''Test that the parse_args and get_symbol methods work as
    expected.

    '''
    code = (
        "subroutine alg()\n"
        "  use kern_mod\n"
        "  call invoke(kern(1.0))\n"
        "end subroutine alg\n")

    psyir = fortran_reader.psyir_from_source(code)
    subroutine = psyir.children[0]
    code_block = subroutine[0].children[0]
    assert isinstance(code_block, CodeBlock)

    # Check expected output from parse_args
    nodes = InvokeCallTrans._parse_args(code_block, code_block._fp2_nodes[0])
    assert isinstance(nodes, list)
    assert len(nodes) == 1
    assert isinstance(nodes[0], Literal)
    assert nodes[0].value == "1.0"

    # Check expected output from get_symbol when no symbol exists
    with pytest.raises(KeyError):
        _ = code_block.scope.symbol_table.lookup("kern")
    symbol = InvokeCallTrans._get_symbol(code_block, code_block._fp2_nodes[0])
    assert isinstance(symbol, DataTypeSymbol)
    assert symbol.name == "kern"
    symbol2 = code_block.scope.symbol_table.lookup("kern")
    assert symbol2 is symbol

    # Check expected output from get_symbol when symbol already exists
    symbol3 = InvokeCallTrans._get_symbol(code_block, code_block._fp2_nodes[0])
    assert symbol3 is symbol


def test_specialise_symbol():
    '''Test that the specialise_symbol method work as expected.

    '''
    symbol = Symbol("hello")

    # Check that a Symbol is specialised
    InvokeCallTrans._specialise_symbol(symbol)
    assert isinstance(symbol, DataTypeSymbol)
    # pylint: disable=no-member
    assert isinstance(symbol.datatype, StructureType)

    # Check that something that is not a symbol is ignored
    test = "hello"
    InvokeCallTrans._specialise_symbol(test)
    assert isinstance(test, str)
    assert test == "hello"


def test_structure_constructor():
    '''Test that validation does not raise an exception if the fparser2
    node is a structure constructor.

    '''
    code = (
        "subroutine alg()\n"
        "  use kern_mod\n"
        "  call invoke(kern(1.0))\n"
        "end subroutine alg\n")

    reader = FortranReader()
    psyir = reader.psyir_from_source(code)
    invoke_trans = InvokeCallTrans()

    invoke = psyir.children[0][0]
    invoke_trans.validate(invoke)
    invoke_trans._validate_fp2_node(invoke.children[0]._fp2_nodes[0])


@pytest.mark.parametrize("string", ["error = 'hello'", "name = 0"])
def test_named_arg_error(string):
    '''Test that the validation method raises an exception if a named
    argument has an unsupported format.

    '''
    code = (
        f"subroutine alg()\n"
        f"  use kern_mod\n"
        f"  call invoke({string})\n"
        f"end subroutine alg\n")

    reader = FortranReader()
    psyir = reader.psyir_from_source(code)
    invoke_trans = InvokeCallTrans()

    invoke = psyir.children[0][0]
    with pytest.raises(TransformationError) as info:
        invoke_trans.validate(invoke)
    assert (f"Error in InvokeCallTrans transformation. If there is a "
            f"named argument, it must take the form name='str', but found "
            f"'{string}'." in str(info.value))

    with pytest.raises(TransformationError) as info:
        invoke_trans._validate_fp2_node(
            invoke.children[0]._fp2_nodes[0])
    assert (f"Error in InvokeCallTrans transformation. If there is a "
            f"named argument, it must take the form name='str', but found "
            f"'{string}'." in str(info.value))


def test_multi_named_arg_error():
    '''Test that the validation method raises an exception if more than
    one named argument is specified in an invoke call. Also check that
    the apply method calls the validate method.

    '''
    code = (
        "subroutine alg()\n"
        "  use kern_mod\n"
        "  call invoke(name='first', name='second')\n"
        "end subroutine alg\n")

    reader = FortranReader()
    psyir = reader.psyir_from_source(code)
    invoke_trans = InvokeCallTrans()
    invoke = psyir.children[0][0]

    with pytest.raises(TransformationError) as info:
        invoke_trans.validate(invoke)
    assert ("Error in InvokeCallTrans transformation. There should be at "
            "most one named argument in an invoke, but there are at least "
            "two: 'first' and 'second'." in str(info.value))

    invoke_trans._call_name = None
    with pytest.raises(TransformationError) as info:
        invoke_trans.apply(invoke, 0)
    assert ("Error in InvokeCallTrans transformation. There should be at "
            "most one named argument in an invoke, but there are at least "
            "two: 'first' and 'second'." in str(info.value))


def test_codeblock_invalid(monkeypatch):
    '''Test that the expected exception is raised if unsupported content
    is found within a codeblock. Use monkeypatch to sabotage the
    codeblock to cause the exception.

    '''
    code = (
        "subroutine alg()\n"
        "  use kern_mod\n"
        "  call invoke(name='tallulah')\n"
        "end subroutine alg\n")

    reader = FortranReader()
    psyir = reader.psyir_from_source(code)
    invoke = psyir.children[0][0]
    code_block = invoke.children[0]
    assert isinstance(code_block, CodeBlock)
    monkeypatch.setattr(code_block, "_fp2_nodes", [None])

    invoke_trans = InvokeCallTrans()

    with pytest.raises(TransformationError) as info:
        invoke_trans.validate(invoke)
    assert ("Expecting an algorithm invoke codeblock to contain either "
            "Structure-Constructor or actual-arg-spec, but found "
            "'NoneType'." in str(info.value))


def test_call_error():
    '''Test that the expected exception is raised in the validate method
    when the supplied node is the wrong type. Also check that the
    validate method from within the apply method.

    '''
    invoke_trans = InvokeCallTrans()
    with pytest.raises(TransformationError) as info:
        invoke_trans.validate("hello")
    assert ("Error in InvokeCallTrans transformation. The supplied call "
            "argument should be a `Call` node but found 'str'."
            in str(info.value))

    # Check that validate is called via the apply method
    with pytest.raises(TransformationError) as info:
        invoke_trans.apply("hello", 0)
    assert ("Error in InvokeCallTrans transformation. The supplied call "
            "argument should be a `Call` node but found 'str'."
            in str(info.value))


def test_invoke_error():
    '''Test that the expected exception is raised in the validate method
    when the supplied node is a call but its name is not the expected
    'invoke' name.

    '''
    invoke_trans = InvokeCallTrans()
    with pytest.raises(TransformationError) as info:
        invoke_trans.validate(Call(RoutineSymbol("hello")))
    assert ("Error in InvokeCallTrans transformation. The supplied call "
            "argument should be a `Call` node with name 'invoke' but "
            "found 'hello'." in str(info.value))


def test_array_reference(fortran_reader):
    '''Test that the validate method does not raise an exception if a
    PSyIR ArrayReference is found.

    '''
    code = (
        "subroutine alg()\n"
        "  use kern_mod\n"
        "  use field_mod, only : r2d_field\n"
        "  type(r2d_field) :: field\n"
        "  call invoke(kern(field))\n"
        "end subroutine alg\n")

    psyir = fortran_reader.psyir_from_source(code)
    subroutine = psyir.children[0]
    assert isinstance(subroutine[0].children[0], ArrayReference)
    invoke_trans = InvokeCallTrans()
    invoke_trans.validate(subroutine[0])


def test_arg_error(fortran_reader):
    '''Test that the validate method raises an exception if unexpected
    content is found as an argument to an invoke.

    '''
    code = (
        "subroutine alg()\n"
        "  use kern_mod\n"
        "  use field_mod, only : r2d_field\n"
        "  type(r2d_field) :: field\n"
        "  call invoke('hello')\n"
        "end subroutine alg\n")

    psyir = fortran_reader.psyir_from_source(code)
    invoke_trans = InvokeCallTrans()
    with pytest.raises(TransformationError) as info:
        invoke_trans.validate(psyir.children[0][0])
    assert ("The arguments to this invoke call are expected to be a "
            "CodeBlock or an ArrayReference, but found 'Literal'."
            in str(info.value))


def test_apply_arrayref(fortran_reader):
    '''Test that an invoke with an array reference argument is transformed
    into PSyclone-specific AlgorithmInvokeCall and KernelFunctor
    classes.

    '''
    code = (
        "subroutine alg()\n"
        "  use kern_mod, only: kern\n"
        "  use field_mod, only: r2d_field\n"
        "  type(r2d_field) :: field\n"
        "  call invoke(kern(field))\n"
        "end subroutine alg\n")

    psyir = fortran_reader.psyir_from_source(code)
    subroutine = psyir.children[0]
    assert len(subroutine[0].children) == 1
    assert isinstance(subroutine[0].children[0], ArrayReference)

    invoke_trans = InvokeCallTrans()
    invoke_trans.apply(subroutine[0], 1)

    invoke = subroutine[0]
    assert isinstance(invoke, AlgorithmInvokeCall)
    assert invoke._index == 1
    assert len(invoke.children) == 1
    check_reference(invoke.children[0], "kern", "field")


def test_apply_codeblock(fortran_reader):
    '''Test that an invoke with a code block argument is transformed
    into PSyclone-specific AlgorithmInvokeCall and KernelFunctor
    classes.

    '''
    code = (
        "subroutine alg()\n"
        "  use kern_mod, only: kern\n"
        "  call invoke(kern(0.0))\n"
        "end subroutine alg\n")

    psyir = fortran_reader.psyir_from_source(code)
    subroutine = psyir.children[0]
    assert len(subroutine[0].children) == 1
    assert isinstance(subroutine[0].children[0], CodeBlock)

    invoke_trans = InvokeCallTrans()
    invoke_trans.apply(subroutine[0], 2)

    invoke = subroutine.children[0]
    assert isinstance(invoke, AlgorithmInvokeCall)
    assert invoke._index == 2
    assert len(invoke.children) == 1
    check_literal(invoke.children[0], "kern", "0.0")


def test_apply_codeblocks(fortran_reader):
    '''Test that an invoke with a code block argument containing multiple
    structure constructors is transformed into PSyclone-specific
    AlgorithmInvokeCall and KernelFunctor classes. Also check that an
    invoke name is also dealt with as expected.

    '''
    code = (
        "subroutine alg()\n"
        "  use kern_mod, only: kern\n"
        "  call invoke(kern(0.0), kern(1.0), name='an invoke')\n"
        "end subroutine alg\n")

    psyir = fortran_reader.psyir_from_source(code)
    subroutine = psyir.children[0]
    assert len(subroutine[0].children) == 3
    for child in subroutine[0].children:
        assert isinstance(child, CodeBlock)

    invoke_trans = InvokeCallTrans()
    invoke_trans.apply(subroutine[0], 3)

    invoke = subroutine.children[0]
    assert isinstance(invoke, AlgorithmInvokeCall)
    assert invoke._name == "'an invoke'"
    assert invoke._index == 3
    assert len(invoke.children) == 2
    check_literal(invoke.children[0], "kern", "0.0")
    check_literal(invoke.children[1], "kern", "1.0")


def test_apply_mixed(fortran_reader):
    '''Test that an invoke with a mixture of code block and array
    reference arguments is transformed into PSyclone-specific
    AlgorithmInvokeCall and KernelFunctor classes.

    '''
    code = (
        "subroutine alg()\n"
        "  use kern_mod, only: kern\n"
        "  use field_mod, only: r2d_field\n"
        "  type(r2d_field) :: field\n"
        "  call invoke(kern(0.0), kern(1.0), kern(field), kern(2.0))\n"
        "end subroutine alg\n")

    psyir = fortran_reader.psyir_from_source(code)
    subroutine = psyir.children[0]
    assert len(subroutine[0].children) == 4
    assert isinstance(subroutine[0].children[0], CodeBlock)
    assert isinstance(subroutine[0].children[1], CodeBlock)
    assert isinstance(subroutine[0].children[2], ArrayReference)
    assert isinstance(subroutine[0].children[3], CodeBlock)

    invoke_trans = InvokeCallTrans()
    invoke_trans.apply(subroutine[0], 4)

    invoke = psyir.children[0][0]
    assert isinstance(invoke, AlgorithmInvokeCall)
    assert invoke._index == 4
    assert len(invoke.children) == 4
    check_literal(invoke.children[0], "kern", "0.0")
    check_literal(invoke.children[1], "kern", "1.0")
    check_reference(invoke.children[2], "kern", "field")
    check_literal(invoke.children[3], "kern", "2.0")


def test_apply_expr(fortran_reader):
    '''Test that an invoke with a mixture of code block and array
    reference arguments as expressions is transformed into PSyclone-specific
    AlgorithmInvokeCall and KernelFunctor classes.

    '''
    code = (
        "subroutine alg()\n"
        "  use kern_mod, only: kern\n"
        "  use field_mod, only: r2d_field\n"
        "  type(r2d_field) :: field\n"
        "  call invoke(kern((field+field)/2), kern((field+field)/2,1.0))\n"
        "end subroutine alg\n")

    psyir = fortran_reader.psyir_from_source(code)
    subroutine = psyir.children[0]
    assert len(subroutine[0].children) == 2
    assert isinstance(subroutine[0].children[0], ArrayReference)
    assert isinstance(subroutine[0].children[1], CodeBlock)

    invoke_trans = InvokeCallTrans()
    invoke_trans.apply(subroutine[0], 5)

    invoke = subroutine[0]
    assert isinstance(invoke, AlgorithmInvokeCall)
    assert invoke._index == 5
    assert len(invoke.children) == 2

    klr = invoke.children[0]
    assert isinstance(klr, KernelFunctor)
    assert klr.symbol.name == "kern"
    assert len(klr.children) == 1
    arg = klr.children[0]
    assert isinstance(arg, BinaryOperation)

    klr = invoke.children[1]
    assert isinstance(klr, KernelFunctor)
    assert klr.symbol.name == "kern"
    assert len(klr.children) == 2
    arg = klr.children[0]
    assert isinstance(arg, BinaryOperation)


def test_multi_name():
    '''Check that the expected exception is raised if a name is provided
    more than once.

    '''
    code = (
        "subroutine alg()\n"
        "  use kern_mod\n"
        "  call invoke(name='Shaw', name='Fernandez')\n"
        "end subroutine alg\n")

    reader = FortranReader()
    psyir = reader.psyir_from_source(code)
    invoke_trans = InvokeCallTrans()

    with pytest.raises(TransformationError) as info:
        invoke_trans.validate(psyir.children[0][0])
    assert ("There should be at most one named argument in an invoke, but "
            "there are at least two: \'Shaw\' and \'Fernandez\'."
            in str(info.value))
