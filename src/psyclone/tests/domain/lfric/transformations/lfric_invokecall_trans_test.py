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

from psyclone.psyir.transformations import TransformationError
from psyclone.psyir.nodes import CodeBlock, Literal, Reference

from psyclone.domain.lfric.transformations import LFRicInvokeCallTrans
from psyclone.domain.lfric.algorithm import LFRicAlgorithmInvokeCall, \
    LFRicKernelFunctor, LFRicBuiltinFunctor


def check_invoke(call, kern_info, description=None):
    '''Utility routine to check that the call argument is the expected
    type, the optional description argument has the expected value and
    contains children of the expected type and name.

    :param call: the LFRicAlgorithmInvokeCall to be checked.
    :type call: :py:class:`psyclone.domain.lfric.algorithm.psyir.` \
        `LFRicAlgorithmInvokeCall`
    :param kern_info: a list of tuples containing information about \
        the expected structure of the call argument's children.
    :type kern_info: list of (class of :py:class:`psyclone.psyir.nodes.Node`, \
         str)
    :param str description: an optional description of the calls \
        contents. Defaults to None.

    '''
    assert isinstance(call, LFRicAlgorithmInvokeCall)
    if call._name:
        assert call._name == f"'{description}'"
    else:
        assert call._name is None
    assert len(call.children) == len(kern_info)
    for index, (kern_type, kern_name) in enumerate(kern_info):
        assert isinstance(call.children[index], kern_type)
        assert call.children[index].symbol.name == kern_name


def check_args(args, arg_info):
    '''Utility routine to check that the arguments for a kernel call or
    builtin are the expected type

    :param args: a list of kernel or builtin arguments.
    :type args: list of :py:class:`psyclone.psyir.nodes.Node`
    :param arg_info: a list of tuples containing information about the \
        expected structure of the args arguments.
    :type arg_info: list of (class of :py:class:`psyclone.psyir.nodes.Node`, \
         str)

    '''
    assert len(args) == len(arg_info)
    for index, (arg_type, arg_value) in enumerate(arg_info):
        assert isinstance(args[index], arg_type)
        if isinstance(args[index], Reference):
            assert args[index].symbol.name == arg_value
        else:
            # It's a literal
            assert args[index].value == arg_value


def test_init():
    '''Check that an LFRicInvokeCallTrans instance can be created
    correctly, has the expected defaults, deals with any __init__
    arguments and its name method returns the expected value.

    '''
    invoke_trans = LFRicInvokeCallTrans()
    assert invoke_trans.name == "LFRicInvokeCallTrans"
    assert isinstance(invoke_trans, LFRicInvokeCallTrans)


def test_structure_contructor(fortran_reader):
    '''Test that validation does not raise an exception if the fparser2
    node is a structure constructor.

    '''
    code = (
        "subroutine alg()\n"
        "  use kern_mod\n"
        "  call invoke(kern(1.0))\n"
        "end subroutine alg\n")

    psyir = fortran_reader.psyir_from_source(code)
    subroutine = psyir.children[0]
    lfric_invoke_trans = LFRicInvokeCallTrans()

    lfric_invoke_trans.validate(subroutine.children[0])
    lfric_invoke_trans._validate_fp2_node(
        subroutine[0].children[0]._fp2_nodes[0])


@pytest.mark.parametrize("string", ["error = 'hello'", "name = 0"])
def test_named_arg_error(string, fortran_reader):
    '''Test that the validation method raises an exception if a named
    argument has an unsupported format.

    '''
    code = (
        f"subroutine alg()\n"
        f"  use kern_mod\n"
        f"  call invoke({string})\n"
        f"end subroutine alg\n")

    psyir = fortran_reader.psyir_from_source(code)
    subroutine = psyir.children[0]
    lfric_invoke_trans = LFRicInvokeCallTrans()

    with pytest.raises(TransformationError) as info:
        lfric_invoke_trans.validate(subroutine[0])
    assert (f"Error in LFRicInvokeCallTrans transformation. If there is a "
            f"named argument, it must take the form name='str', but found "
            f"'{string}'." in str(info.value))

    with pytest.raises(TransformationError) as info:
        lfric_invoke_trans._validate_fp2_node(
            subroutine[0].children[0]._fp2_nodes[0])
    assert (f"Error in LFRicInvokeCallTrans transformation. If there is a "
            f"named argument, it must take the form name='str', but found "
            f"'{string}'." in str(info.value))


def test_multi_named_arg_error(fortran_reader):
    '''Test that the validation method raises an exception if more than
    one named argument is specified in an invoke call. Also check that
    the apply method calls the validate method.

    '''
    code = (
        "subroutine alg()\n"
        "  use kern_mod\n"
        "  call invoke(name='first', name='second')\n"
        "end subroutine alg\n")

    psyir = fortran_reader.psyir_from_source(code)
    subroutine = psyir.children[0]
    lfric_invoke_trans = LFRicInvokeCallTrans()

    with pytest.raises(TransformationError) as info:
        lfric_invoke_trans.validate(subroutine[0])
    assert ("Error in LFRicInvokeCallTrans transformation. There should be at "
            "most one named argument in an invoke, but there are at least "
            "two: 'first' and 'second'." in str(info.value))

    with pytest.raises(TransformationError) as info:
        lfric_invoke_trans.apply(subroutine[0], 0)
    assert ("Error in LFRicInvokeCallTrans transformation. There should be at "
            "most one named argument in an invoke, but there are at least "
            "two: 'first' and 'second'." in str(info.value))


def test_codeblock_invalid(monkeypatch, fortran_reader):
    '''Test that the expected exception is raised if unsupported content
    is found within a codeblock. Use monkeypatch to sabotage the
    codeblock to cause the exception.

    '''
    code = (
        "subroutine alg()\n"
        "  use kern_mod\n"
        "  call invoke(name='tallulah')\n"
        "end subroutine alg\n")

    psyir = fortran_reader.psyir_from_source(code)
    subroutine = psyir.children[0]
    code_block = subroutine[0].children[0]
    assert isinstance(code_block, CodeBlock)
    monkeypatch.setattr(code_block, "_fp2_nodes", [None])

    lfric_invoke_trans = LFRicInvokeCallTrans()

    with pytest.raises(TransformationError) as info:
        lfric_invoke_trans.validate(subroutine[0])
    assert ("Expecting an algorithm invoke codeblock to contain either "
            "Structure-Constructor or actual-arg-spec, but found "
            "'NoneType'." in str(info.value))


def test_apply_codedkern_arrayref(fortran_reader):
    '''Test that a kernel call within an invoke that is mistakenly encoded
    as an ArrayRef in the PSyIR is translated into an
    LFRicKernelFunctor and expected children. This test also checks
    that an optional name is captured correctly. Also checks that the
    index argument is captured correctly.

    '''
    code = (
        "subroutine alg()\n"
        "  use kern_mod\n"
        "  use field_mod, only : field\n"
        "  type(field) :: field1\n"
        "  call invoke(kern(field1), name='hello')\n"
        "end subroutine alg\n")

    psyir = fortran_reader.psyir_from_source(code)
    subroutine = psyir.children[0]
    lfric_invoke_trans = LFRicInvokeCallTrans()

    lfric_invoke_trans.apply(subroutine[0], 1)

    check_invoke(subroutine[0], [(LFRicKernelFunctor, "kern")],
                 description="hello")
    assert subroutine[0]._index == 1
    args = subroutine[0].children[0].children
    check_args(args, [(Reference, "field1")])


def test_apply_codedkern_structconstruct(fortran_reader):
    '''Test that a kernel call within an invoke that is encoded within a
    PSyIR code block as an fparser2 Structure Constructor is
    translated into an LFRicKernelFunctor and expected children.

    '''
    code = (
        "subroutine alg()\n"
        "  use kern_mod\n"
        "  use field_mod, only : field\n"
        "  type(field) :: field1\n"
        "  call invoke(kern(1.0))\n"
        "end subroutine alg\n")

    psyir = fortran_reader.psyir_from_source(code)
    subroutine = psyir.children[0]
    lfric_invoke_trans = LFRicInvokeCallTrans()

    lfric_invoke_trans.apply(subroutine[0], 2)

    check_invoke(subroutine[0], [(LFRicKernelFunctor, "kern")])
    args = subroutine[0].children[0].children
    check_args(args, [(Literal, "1.0")])


def test_apply_builtin_structconstruct(fortran_reader):
    '''Test that a builtin call within an invoke that is encoded within a
    PSyIR code block as an fparser2 Structure Constructor is
    translated into an LFRicBuiltinFunctor and expected children. This
    test also checks that an optional name is captured correctly.

    '''
    code = (
        "subroutine alg()\n"
        "  use kern_mod\n"
        "  use field_mod, only : field\n"
        "  type(field) :: field1\n"
        "  call invoke(setval_c(field1, 1.0))\n"
        "end subroutine alg\n")

    psyir = fortran_reader.psyir_from_source(code)
    subroutine = psyir.children[0]
    lfric_invoke_trans = LFRicInvokeCallTrans()

    lfric_invoke_trans.apply(subroutine[0], 3)

    check_invoke(subroutine[0], [(LFRicBuiltinFunctor, "setval_c")])
    args = subroutine[0].children[0].children
    check_args(args, [(Reference, "field1"), (Literal, "1.0")])


def test_apply_builtin_arrayref(fortran_reader):
    '''Test that a builtin call within an invoke that is mistakenly
    encoded as an ArrayRef in the PSyIR is translated into an
    LFRicBuiltinFunctor and expected children. This test also checks
    that an optional name is captured correctly.

    '''
    code = (
        "subroutine alg()\n"
        "  use kern_mod\n"
        "  use field_mod, only : field\n"
        "  type(field) :: field1\n"
        "  integer :: value\n"
        "  call invoke(setval_c(field1, value), name='test')\n"
        "end subroutine alg\n")

    psyir = fortran_reader.psyir_from_source(code)
    subroutine = psyir.children[0]
    lfric_invoke_trans = LFRicInvokeCallTrans()

    lfric_invoke_trans.apply(subroutine[0], 4)

    check_invoke(subroutine[0], [(LFRicBuiltinFunctor, "setval_c")],
                 description="test")
    args = subroutine[0].children[0].children
    check_args(args, [(Reference, "field1"), (Reference, "value")])


def test_apply_mixed(fortran_reader):
    '''Test that an invoke with a mixture of kernels and builtins, with a
    number of the kernels and an optional name being within a single
    codeblock, are translated into an LFRicBuiltinFunctor and expected
    children.

    '''
    code = (
        "subroutine alg()\n"
        "  use kern_mod\n"
        "  use field_mod, only : field\n"
        "  type(field) :: field1\n"
        "  integer :: value\n"
        "  call invoke(kern(field1), setval_c(field1, 1.0), name='test', "
        "setval_c(field1, 1.0), setval_c(field1, value))\n"
        "end subroutine alg\n")

    psyir = fortran_reader.psyir_from_source(code)
    subroutine = psyir.children[0]
    lfric_invoke_trans = LFRicInvokeCallTrans()

    lfric_invoke_trans.apply(subroutine[0], 5)

    check_invoke(
        subroutine[0],
        [(LFRicKernelFunctor, "kern"), (LFRicBuiltinFunctor, "setval_c"),
         (LFRicBuiltinFunctor, "setval_c"), (LFRicBuiltinFunctor, "setval_c")],
        description="test")
    args = subroutine[0].children[0].children
    check_args(args, [(Reference, "field1")])
    args = subroutine[0].children[1].children
    check_args(args, [(Reference, "field1"), (Literal, "1.0")])
    args = subroutine[0].children[2].children
    check_args(args, [(Reference, "field1"), (Literal, "1.0")])
    args = subroutine[0].children[3].children
    check_args(args, [(Reference, "field1"), (Reference, "value")])
