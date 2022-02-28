# -----------------------------------------------------------------------------
# BSD 3-Clause License
#
# Copyright (c) 2021-2022, Science and Technology Facilities Council
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
# Modified by J. Henrichs, Bureau of Meteorology

'''Module containing tests for the AlgorithmInvokeCall and
KernelFunctor algorithm-layer-specific nodes. The tests include
translation of PSyIR to PSyclone Algorithm PSyIR and PSyclone
Algorithm PSyIR to processed PSyIR.

'''
from __future__ import absolute_import
import pytest

from psyclone.errors import InternalError
from psyclone.psyir.frontend.fortran import FortranReader
from psyclone.psyir.nodes import Reference, Node, ArrayReference, \
    BinaryOperation, Container, Loop, Literal
from psyclone.psyir.nodes.node import colored
from psyclone.psyir.symbols import RoutineSymbol, DataTypeSymbol, \
    StructureType, Symbol, REAL_TYPE, DataSymbol, INTEGER_TYPE
from psyclone.domain.common.algorithm import AlgorithmInvokeCall, \
    KernelFunctor
from psyclone.errors import GenerationError
from psyclone.domain.common.transformations import AlgTrans


def create_alg_psyir(code):
    '''Utility to create a PSyclone Algorithm PSyIR tree from Fortran
    code.

    :param str code: Fortran algorithm code encoded as a string.

    :returns: PSyclone Algorithm PSyIR tree representing the Fortran \
        code.
    :rtype: :py:class:`psyclone.psyir.nodes.Node`

    '''
    fortran_reader = FortranReader()
    psyir = fortran_reader.psyir_from_source(code)

    alg_trans = AlgTrans()
    alg_trans.apply(psyir)

    return psyir


def check_call(call, routine_name, container_name, args_info):
    '''Utility function to check the contents of a processed invoke call.

    :param invoke: the call node that is being checked.
    :type invoke: :py:class:`psyclone.psyir.nodes.Call`
    :param str routine_name: the name of the call node.
    :param str container_name: the name of the container containing \
        the call node.
    ;param args_info: information to check the call arguments.
    :type args_info: list of \
        (:py:class:`psyclone.psyir.nodes.Reference`, str) or \
        (:py:class:`psyclone.psyir.nodes.ArrayReference`, str, [str or \
        BinaryOperation])

    '''
    assert isinstance(call.routine, RoutineSymbol)
    assert call.routine.name == routine_name
    assert call.routine.is_import
    assert call.routine.interface.container_symbol.name == container_name
    args = call.children
    assert len(args) == len(args_info)
    for idx, arg_info in enumerate(args_info):
        arg_type = arg_info[0]
        name = arg_info[1]
        assert isinstance(args[idx], arg_type)
        assert args[idx].symbol.name == name
        if arg_type is ArrayReference:
            indices_info = arg_info[2]
            indices = args[idx].children
            assert len(indices) == len(indices_info)
            for idx2, index_info in enumerate(indices_info):
                if isinstance(index_info, str):
                    assert indices[idx2].symbol.name == index_info
                else:  # BinaryOperation
                    assert isinstance(indices[idx2], BinaryOperation)


def _check_alg_names(invoke, module_name):
    '''Utility function to check that the
    create_psylayer_symbol_root_names method creates the expected
    names.

    :param invoke: the invoke call for which names are being created.
    :type invoke: \
        :py:class:`psyclone.domain.common.algorithm.psyir.AlgorithmInvokeCall`
    :param str module_name: the expected module name.

    '''
    assert isinstance(invoke, AlgorithmInvokeCall)
    assert invoke._psylayer_routine_root_name is None
    assert invoke._psylayer_container_root_name is None

    invoke.create_psylayer_symbol_root_names()

    assert invoke._psylayer_routine_root_name == "invoke_0_kern"
    assert invoke._psylayer_container_root_name == module_name

    # Check that the names are only created once.
    routine_root_name_tmp = invoke._psylayer_routine_root_name
    container_root_name_tmp = invoke._psylayer_container_root_name
    invoke.create_psylayer_symbol_root_names()
    assert invoke._psylayer_routine_root_name is routine_root_name_tmp
    assert invoke._psylayer_container_root_name is container_root_name_tmp


def test_algorithminvokecall():
    '''Check that an instance of AlgorithmInvokeCall can be
    created. Also check any optional arguments.

    '''
    routine = RoutineSymbol("hello")
    call = AlgorithmInvokeCall(routine, 2)
    assert call._children_valid_format == "[KernelFunctor]*"
    assert call._text_name == "AlgorithmInvokeCall"
    assert call._colour == "green"
    assert call._psylayer_routine_root_name is None
    assert call._psylayer_container_root_name is None
    assert call._index == 2
    assert call.parent is None
    assert call._name is None

    name = "description"
    parent = Container("container")
    call = AlgorithmInvokeCall(
        routine, 2, parent=parent, name=name)
    assert call.parent is parent
    assert call._name == name


def test_algorithminvokecall_error():
    '''Check that AlgorithmInvokeCall raises the expected exceptions if
    the invoke argument has an invalid value.

    '''
    routine = RoutineSymbol("hello")
    with pytest.raises(TypeError) as info:
        AlgorithmInvokeCall(routine, "error")
    assert ("AlgorithmInvokeCall index argument should be an int but found "
            "'str'." in str(info.value))

    with pytest.raises(ValueError) as info:
        AlgorithmInvokeCall(routine, -1)
    assert ("AlgorithmInvokeCall index argument should be a non-negative "
            "integer but found -1." in str(info.value))

    with pytest.raises(TypeError) as info:
        AlgorithmInvokeCall(routine, 1, name=routine)
    assert ("AlgorithmInvokeCall name argument should be a str but "
            "found 'RoutineSymbol'." in str(info.value))


def test_aic_create():
    '''Check that the create method behaves as expected.'''

    kernel_functor = KernelFunctor(DataTypeSymbol("dummy", REAL_TYPE))
    routine = RoutineSymbol("hello")
    index = 10
    aic = AlgorithmInvokeCall.create(routine, [kernel_functor], index)
    assert isinstance(aic, AlgorithmInvokeCall)
    assert len(aic.children) == 1
    assert aic.children[0] is kernel_functor
    assert aic._routine is routine
    assert aic._index == index
    assert aic._name is None

    name = "description"
    aic = AlgorithmInvokeCall.create(
        routine, [kernel_functor.detach()], index, name=name)
    assert aic._name == name

    with pytest.raises(GenerationError) as info:
        AlgorithmInvokeCall.create(routine, kernel_functor, index)
    assert ("AlgorithmInvokeCall create arguments argument should be a list "
            "but found 'KernelFunctor'." in str(info.value))


class DummySubClass(AlgorithmInvokeCall):
    '''A dummy subclass of AlgorithmInvokeCall used for testing the
    behaviour of the create method in AlgorithmInvokeCall.

    '''


@pytest.mark.parametrize("cls", [AlgorithmInvokeCall, DummySubClass])
def test_aic_create_object(cls):
    '''Check that the AlgorithmInvokeCall create method creates the
    expected object (which could be a subclass of AlgorithmInvokeCall)

    '''
    routine = RoutineSymbol("hello")
    call = cls.create(routine, [], 0)
    assert call.routine is routine
    # pylint: disable=unidiomatic-typecheck
    assert type(call) is cls


def test_aic_validate_child():
    '''Check that the _validate_child method behaves as expected.'''

    kernel_functor = KernelFunctor(DataTypeSymbol("dummy", REAL_TYPE))
    assert AlgorithmInvokeCall._validate_child(0, kernel_functor)
    assert not AlgorithmInvokeCall._validate_child(0, "Invalid")

    routine = RoutineSymbol("hello")
    call = AlgorithmInvokeCall(routine, 0)
    with pytest.raises(GenerationError) as info:
        call.children = ["invalid"]
    assert ("Item 'str' can't be child 0 of 'AlgorithmInvokeCall'. The valid "
            "format is: '[KernelFunctor]*'." in str(info.value))
    call.children = [kernel_functor]


def test_aic_node_str():
    '''Check that the node_str method returns the expected representation
    of this node.

    '''
    routine = RoutineSymbol("hello")
    call = AlgorithmInvokeCall.create(
        routine, [], 0, name="describing an invoke")
    assert ("AlgorithmInvokeCall[name=\"describing an invoke\"]"
            in call.node_str(colour=False))


def test_aic_defroutinerootname():
    '''Check that the _def_routine_root_name() internal method behaves as
    expected.

    '''
    symbol_name = "dummy"
    kernel_functor = KernelFunctor(DataTypeSymbol(symbol_name, REAL_TYPE))
    routine = RoutineSymbol("hello")
    index = 3
    call = AlgorithmInvokeCall(routine, index)
    call.children = [kernel_functor]
    assert call._def_routine_root_name() == f"invoke_{index}_{symbol_name}"

    call.children.append(kernel_functor.copy())
    assert call._def_routine_root_name() == f"invoke_{index}"

    for name in [" a  description ", "' a__description '",
                 "\" a  description \""]:
        call._name = name
        assert call._def_routine_root_name() == "invoke_a__description"


def test_aic_defroutineroot_name_error():
    '''Check that the _def_routine_root_name() internal method raises the
    expected exception if the supplied name is invalid.

    '''
    symbol_name = "dummy"
    kernel_functor = KernelFunctor(DataTypeSymbol(symbol_name, REAL_TYPE))
    routine = RoutineSymbol("hello")
    index = 3
    call = AlgorithmInvokeCall(routine, index)
    call.children = [kernel_functor]
    assert call._def_routine_root_name() == f"invoke_{index}_{symbol_name}"

    call.children.append(kernel_functor.copy())
    assert call._def_routine_root_name() == f"invoke_{index}"

    for name in ["1name", "name!", "nameʑ", "ʒʓʔʕʗʘʙʚʛʜʝʞ"]:
        call._name = name
        with pytest.raises(TypeError) as info:
            _ = call._def_routine_root_name()
        print(name)
        assert (f"AlgorithmInvokeCall:_def_routine_root_name() the (optional) "
                f"name of an invoke must be a string containing a valid name "
                f"(with any spaces replaced by underscores) but found "
                f"'{name}'." in str(info.value))


def test_aic_createpsylayersymbolrootnames():
    '''Check that the create_psylayer_symbol_root_names method behaves in
    the expected way when the name comes from a subroutine, a module
    and when it has a filecontainer, i.e. it creates and stores a root
    name for a routine symbol and a container symbol. Also check that
    it raises the expected exception if no FileContainer or Routine
    nodes are found in the tree.

    '''
    code = (
        "subroutine alg1()\n"
        "  use kern_mod, only : kern\n"
        "  use field_mod, only : field_type\n"
        "  type(field_type) :: field1\n"
        "  call invoke(kern(field1))\n"
        "end subroutine alg1\n")

    # FileContainer and Routine (subroutine)
    psyir = create_alg_psyir(code)
    invoke = psyir.children[0][0]
    _check_alg_names(invoke, "psy_alg1")

    # Routine, no FileContainer
    psyir = create_alg_psyir(code)
    psyir = psyir.children[0]
    psyir.detach()
    invoke = psyir[0]
    _check_alg_names(invoke, "psy_alg1")

    code = (
        "module my_mod\n"
        "contains\n"
        "subroutine alg1()\n"
        "  use kern_mod, only : kern\n"
        "  use field_mod, only : field_type\n"
        "  type(field_type) :: field1\n"
        "  call invoke(kern(field1))\n"
        "end subroutine alg1\n"
        "end module my_mod\n")

    # File container and module
    psyir = create_alg_psyir(code)
    invoke = psyir.children[0].children[0][0]
    _check_alg_names(invoke, "psy_my_mod")

    # Module, no FileContainer
    psyir = create_alg_psyir(code)
    psyir = psyir.children[0]
    psyir.detach()
    invoke = psyir.children[0][0]
    _check_alg_names(invoke, "psy_my_mod")

    # No modules or FileContainers (should not happen)
    invoke._psylayer_container_root_name = None
    invoke.detach()
    with pytest.raises(InternalError) as error:
        invoke.create_psylayer_symbol_root_names()
    assert "No Routine or Container node found." in str(error.value)


def test_aic_lowertolanguagelevel_error():
    '''Check that the lower_to_language_level method raises the expected
    exception when an unexpected argument is found.

    '''
    code = (
        "subroutine alg1()\n"
        "  use kern_mod\n"
        "  use field_mod, only : field_type\n"
        "  type(field_type) :: field\n"
        "  call invoke(kern(field*1.0))\n"
        "end subroutine alg1\n")

    psyir = create_alg_psyir(code)
    invoke = psyir.children[0]
    with pytest.raises(GenerationError) as info:
        invoke.lower_to_language_level()
    assert ("Expected Algorithm-layer kernel arguments to be a literal, "
            "reference or array reference, but found 'BinaryOperation'."
            in str(info.value))


def test_aic_lowertolanguagelevel_error2():
    '''Check that the lower_to_language_level method raises the expected
    exception when no invoke symbol is found in the PSyIR.

    '''
    code = (
        "subroutine alg1()\n"
        "  use kern_mod\n"
        "  use field_mod, only : field_type\n"
        "  type(field_type) :: field\n"
        "  call invoke(kern(field))\n"
        "end subroutine alg1\n")

    psyir = create_alg_psyir(code)
    invoke = psyir.children[0]
    symbol_table = invoke.scope.symbol_table
    invoke_symbol = symbol_table.lookup("invoke")
    symbol_table.remove(invoke_symbol)

    with pytest.raises(InternalError) as info:
        invoke.lower_to_language_level()
    assert "No 'invoke' symbol found." in str(info.value)


def test_aic_lowertolanguagelevel_expr():
    '''Check that the lower_to_language_level method deals correctly with
    simple associative expresssions, i.e. i+1 is the same as 1+i.

    '''
    code = (
        "subroutine alg1()\n"
        "  use kern_mod\n"
        "  use field_mod, only : field_type\n"
        "  type(field_type) :: field(10)\n"
        "  integer :: i\n"
        "  call invoke(kern(field(i+1), field(1+i)))\n"
        "end subroutine alg1\n")

    psyir = create_alg_psyir(code)
    subroutine = psyir.children[0]
    invoke = subroutine.children[0]
    invoke.lower_to_language_level()
    assert len(subroutine.children[0].children) == 1


def test_aic_lowertolanguagelevel_single():
    '''Check that the lower_to_language_level method works as expected
    when it has a single kernel with multiple fields of the same
    name. Also check that the lower_to_language_level method creates
    the required routine and container symbols if they have not
    already been created. Also check that the lower_to_language_level
    method removes the invoke symbol from the appropriate symbol
    table.

    '''
    code = (
        "subroutine alg1()\n"
        "  use kern_mod\n"
        "  use field_mod, only : field_type\n"
        "  integer :: i,j\n"
        "  type(field_type) :: field1, field2(10)\n"
        "  call invoke(kern1(field1, field1, field2(i), field2( j )))\n"
        "end subroutine alg1\n")

    psyir = create_alg_psyir(code)
    invoke = psyir.children[0][0]

    assert isinstance(invoke, AlgorithmInvokeCall)
    assert len(psyir.walk(AlgorithmInvokeCall)) == 1
    assert len(psyir.walk(KernelFunctor)) == 1
    assert "invoke" in invoke.scope.symbol_table._symbols

    # Don't call create_psylayer_symbol_root_names() here. This is to
    # check that lower_to_language_level() creates the names if
    # needed.
    invoke.lower_to_language_level()

    assert not psyir.walk(AlgorithmInvokeCall)
    assert not psyir.walk(KernelFunctor)
    invoke = psyir.children[0][0]
    assert "invoke" not in invoke.scope.symbol_table._symbols

    call = psyir.children[0][0]
    check_call(call, "invoke_0_kern1", "psy_alg1",
               [(Reference, "field1"),
                (ArrayReference, "field2", ["i"]),
                (ArrayReference, "field2", ["j"])])


def test_aic_lowertolanguagelevel_multi():
    '''Check that the lower_to_language_level method works as expected
    when it has multiple kernels with fields of the same name. Also
    check that an invoke name is supported.

    '''
    code = (
        "subroutine alg1()\n"
        "  use kern_mod\n"
        "  use precision_mod, only : r_def\n"
        "  use field_mod, only : field_type\n"
        "  integer :: i,j\n"
        "  type(field_type) :: field1, field2(10)\n"
        "  call invoke(kern1(field1), kern2(field1), kern3(field2(i)), &\n"
        "              kern1(field2(I)), kern2(field2( j )), &\n"
        "              kern3(field2(j+1)), kern1(1.0_r_def), &\n"
        "              name=\"multi kern invoke\")\n"
        "end subroutine alg1\n")

    psyir = create_alg_psyir(code)
    invoke = psyir.children[0][0]

    assert isinstance(invoke, AlgorithmInvokeCall)
    assert len(psyir.walk(AlgorithmInvokeCall)) == 1
    assert len(psyir.walk(KernelFunctor)) == 7

    # Explicitly create the language level root names before lowering
    # to make sure lower_to_language_level works if they have already
    # been created.
    invoke.create_psylayer_symbol_root_names()
    invoke.lower_to_language_level()

    assert not psyir.walk(AlgorithmInvokeCall)
    assert not psyir.walk(KernelFunctor)

    call = psyir.children[0][0]
    check_call(call, "invoke_multi_kern_invoke", "psy_alg1",
               [(Reference, "field1"),
                (ArrayReference, "field2", ["i"]),
                (ArrayReference, "field2", ["j"]),
                (ArrayReference, "field2", [BinaryOperation])])


def test_aic_lowertolanguagelevel_multi_invoke():
    '''Check that the lower_to_language_level method works as expected
    when it has multiple invoke's. Also purposely add existing
    algorithm names that clash with root names to make sure generated
    names are correct. Also check that the lower_to_language_level
    method removes the invoke symbol from the appropriate symbol table
    when the second invoke is lowered.

    '''
    code = (
        "subroutine alg1()\n"
        "  use kern_mod, only : kern1, kern2\n"
        "  use field_mod, only : field_type\n"
        "  type(field_type) :: field1\n"
        "  real :: invoke_0_kern1, psy_alg1\n"
        "  call invoke(kern1(field1))\n"
        "  call invoke(kern2(field1))\n"
        "end subroutine alg1\n")

    psyir = create_alg_psyir(code)
    invoke1 = psyir.children[0][0]
    invoke2 = psyir.children[0][1]

    assert isinstance(invoke1, AlgorithmInvokeCall)
    assert isinstance(invoke2, AlgorithmInvokeCall)
    assert len(psyir.walk(AlgorithmInvokeCall)) == 2
    assert len(psyir.walk(KernelFunctor)) == 2
    assert "invoke" in invoke1.scope.symbol_table._symbols
    assert "invoke" in invoke2.scope.symbol_table._symbols

    # Don't call create_psylayer_symbol_root_names() here. This is to
    # check that lower_to_language_level() creates the names if
    # needed.

    # Just lower one of the invoke's. The 'invoke' symbol should still
    # exist.
    invoke1.lower_to_language_level()
    call1 = psyir.children[0][0]
    assert not isinstance(call1, AlgorithmInvokeCall)
    assert isinstance(invoke2, AlgorithmInvokeCall)
    assert len(psyir.walk(AlgorithmInvokeCall)) == 1
    assert len(psyir.walk(KernelFunctor)) == 1
    assert "invoke" in call1.scope.symbol_table._symbols
    assert "invoke" in invoke2.scope.symbol_table._symbols

    # Now lower the second invoke. The 'invoke' symbol should be
    # removed.
    invoke2.lower_to_language_level()
    call2 = psyir.children[0][1]

    assert not psyir.walk(AlgorithmInvokeCall)
    assert not psyir.walk(KernelFunctor)
    assert "invoke" not in call1.scope.symbol_table._symbols
    assert "invoke" not in call2.scope.symbol_table._symbols

    assert call1.routine.name == "invoke_0_kern1_1"
    assert call1.routine.interface.container_symbol.name == "psy_alg1_1"

    assert call2.routine.name == "invoke_1_kern2"
    assert call2.routine.interface.container_symbol.name == "psy_alg1_1"


def test_aic_lowertolanguagelevel_invoke_symbols():
    '''Check that the lower_to_language_level method removes the
    appropriate invoke symbols when these symbols are within symbol
    tables that are connected to different parts of the PSyIR tree,
    including where the nodes are ancestors of each other.

    '''
    code = (
        "module mod1\n"
        "contains\n"
        "subroutine alg1()\n"
        "  use kern_mod, only : kern1\n"
        "  use field_mod, only : field_type\n"
        "  type(field_type) :: field\n"
        "  call invoke(kern1(field))\n"
        "end subroutine alg1\n"
        "subroutine alg2()\n"
        "  use kern_mod, only : kern2\n"
        "  use field_mod, only : field_type\n"
        "  type(field_type) :: field\n"
        "  call invoke(kern2(field))\n"
        "end subroutine alg2\n"
        "end module\n")

    psyir = create_alg_psyir(code)
    # Add an invoke symbol to the module (Container node)
    container = psyir.children[0]
    assert isinstance(container, Container)
    container.symbol_table.add(RoutineSymbol("invoke"))

    invoke1 = container.children[0][0]
    assert isinstance(invoke1, AlgorithmInvokeCall)
    invoke2 = container.children[1][0]
    assert isinstance(invoke2, AlgorithmInvokeCall)

    assert "invoke" in invoke1.scope.symbol_table._symbols
    assert "invoke" in invoke2.scope.symbol_table._symbols

    psyir.lower_to_language_level()

    call1 = container.children[0][0]
    call2 = container.children[1][0]
    assert "invoke" not in call1.scope.symbol_table._symbols
    assert "invoke" not in call2.scope.symbol_table._symbols

    container = psyir.children[0]
    assert "invoke" in container.symbol_table._symbols


def test_aic_lowertolanguagelevel_invoke_symbols_scope():
    '''Check that the lower_to_language_level method removes the
    appropriate invoke symbol when it is in a different scope to the
    invoke call.

    '''
    code = (
        "subroutine alg()\n"
        "  use kern_mod, only : kern\n"
        "  use field_mod, only : field_type\n"
        "  type(field_type) :: field\n"
        "  call invoke(kern(field))\n"
        "end subroutine alg\n")
    psyir = create_alg_psyir(code)
    # Move the invoke so the invoke symbol is in a different scope to
    # the invoke call.
    invoke = psyir.children[0][0]
    assert isinstance(invoke, AlgorithmInvokeCall)
    symbol = invoke.scope.symbol_table.new_symbol(
        root_name="i", symbol_type=DataSymbol, datatype=INTEGER_TYPE)
    loop = Loop.create(
        symbol, Literal("0", INTEGER_TYPE), Literal("1", INTEGER_TYPE),
        Literal("1", INTEGER_TYPE), [invoke.detach()])
    psyir.children[0].children.append(loop)

    assert "invoke" not in invoke.scope.symbol_table._symbols
    assert "invoke" in loop.scope.symbol_table._symbols

    psyir.lower_to_language_level()

    assert not psyir.walk(AlgorithmInvokeCall)
    assert not psyir.walk(KernelFunctor)
    loop = psyir.children[0][0]
    invoke = loop.loop_body[0]
    assert "invoke" not in invoke.scope.symbol_table._symbols
    assert "invoke" not in loop.scope.symbol_table._symbols


def test_kernelfunctor():
    '''Check that an instance of KernelFunctor class can be created. Also
    check that the symbol method works as expected.

    '''
    symbol = DataTypeSymbol("hello", StructureType())
    klr = KernelFunctor(symbol)
    assert klr._symbol == symbol
    assert klr.symbol == symbol
    assert klr._colour == "yellow"
    assert klr._text_name == "KernelFunctor"
    assert klr.parent is None


def test_kernelfunctor_parent():
    '''Check that the optional parent argument to a KernelFunctor class
    constructor is stored correctly.

    '''
    parent = Node()
    symbol = DataTypeSymbol("hello", StructureType())
    klr = KernelFunctor(symbol, parent=parent)
    assert klr.parent == parent


def test_kernelfunctor_invalid_symbol():
    '''Check KernelFunctor raises the expected exception if the type of
    the symbol argument is invalid.

    '''
    with pytest.raises(TypeError) as info:
        _ = KernelFunctor(Symbol("hello"))
    assert ("KernelFunctor symbol argument should be a DataTypeSymbol but "
            "found 'Symbol'." in str(info.value))


class SubClass(KernelFunctor):
    '''Utility subclass of KernelFunctor to test that the create method
    in KernelFunctor behaves as expected for subclasses.'''


@pytest.mark.parametrize("cls", [KernelFunctor, SubClass])
def test_kernelfunctor_create(cls):
    '''Check that the create method of KernelFunctor works as expected.

    '''
    symbol = DataTypeSymbol("hello", StructureType())
    klr = cls.create(symbol, [])
    # pylint: disable=unidiomatic-typecheck
    assert type(klr) is cls
    assert klr._symbol == symbol
    assert not klr.children

    arg = Reference(Symbol("dummy"))
    klr = KernelFunctor.create(symbol, [arg])
    assert len(klr.children) == 1
    assert klr.children[0] == arg
    assert arg.parent == klr


def test_kernelfunctor_create_invalid_symbol():
    '''Check that the create method of KernelFunctor raises the expected
    exception if the provided symbol argument is not the correct type.

    '''
    symbol = Symbol("hello")
    with pytest.raises(GenerationError) as info:
        _ = KernelFunctor.create(symbol, [])
    assert ("KernelFunctor create() symbol argument should be a DataTypeSymbol"
            " but found 'Symbol'." in str(info.value))


def test_kernelfunctor_create_invalid_args1():
    '''Check that the create method of KernelFunctor raises the expected
    exception if the provided 'arguments' argument is not a list.

    '''
    symbol = DataTypeSymbol("hello", StructureType())
    with pytest.raises(GenerationError) as info:
        _ = KernelFunctor.create(symbol, "Not a list")
    assert ("KernelFunctor create() arguments argument should be a list "
            "but found 'str'." in str(info.value))


def test_kernelfunctor_invalid_args2():
    '''Check that the create method of KernelFunctor raises the expected
    exception if its supplied list of children are not the expected
    type (tests _validate_child method and _children_valid_format
    variable)

    '''
    symbol = DataTypeSymbol("hello", StructureType())
    with pytest.raises(GenerationError) as info:
        _ = KernelFunctor.create(symbol, ["hello"])
    assert("Item 'str' can't be child 0 of 'KernelFunctor'. The valid "
           "format is: '[DataNode]*'." in str(info.value))


def test_kernelfunctor_node_str():
    '''Check the node_str method of the KernelFunctor class.'''

    symbol = DataTypeSymbol("hello", StructureType())
    arg = Reference(Symbol("dummy"))
    klr = KernelFunctor.create(symbol, [arg])
    coloredtext = colored("KernelFunctor", KernelFunctor._colour)
    assert klr.node_str() == coloredtext+"[name:'hello']"


def test_kernelfunctor_str():
    '''Check the str method of the KernelFunctor class.'''

    symbol = DataTypeSymbol("hello", StructureType())
    arg = Reference(Symbol("dummy"))
    klr = KernelFunctor.create(symbol, [arg])
    assert klr.__str__() == "KernelFunctor[name:'hello']"
