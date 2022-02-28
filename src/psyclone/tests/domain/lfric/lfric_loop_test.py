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
# Authors R. W. Ford, A. R. Porter and S. Siso, STFC Daresbury Lab
# Modified I. Kavcic and A. Coughtrie, Met Office,
#          C. M. Maynard, Met Office/University of Reading,
#          J. Henrichs, Bureau of Meteorology.

''' This module uses pytest to test the DynLoop class. This is the LFRic-
    specific subclass of the Loop class. '''

from __future__ import absolute_import, print_function
import os
import pytest
from fparser import api as fpapi
from psyclone.configuration import Config
from psyclone.domain.lfric import LFRicConstants
from psyclone.dynamo0p3 import DynLoop, DynKern, DynKernMetadata
from psyclone.errors import GenerationError, InternalError
from psyclone.parse.algorithm import parse
from psyclone.psyGen import PSyFactory
from psyclone.psyir.nodes import Schedule, ArrayReference, Reference, Literal
from psyclone.tests.lfric_build import LFRicBuild
from psyclone.transformations import (Dynamo0p3ColourTrans,
                                      DynamoOMPParallelLoopTrans,
                                      Dynamo0p3RedundantComputationTrans)

BASE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))),
    "test_files", "dynamo0p3")
TEST_API = "dynamo0.3"


def test_constructor_invalid_loop_type(monkeypatch):
    ''' Check that the constructor raises the expected errors when an invalid
    loop type is specified. '''
    # An invalid type should be caught by the setter in the base Loop class.
    with pytest.raises(GenerationError) as err:
        DynLoop(loop_type="wrong")
    const = LFRicConstants()
    assert ("Error, loop_type value (wrong) is invalid. Must be one of {0}."
            .format(const.VALID_LOOP_TYPES) in str(err.value))
    # Monkeypatch the list of valid loop types so as to reach the code
    # that attempts to set the loop variable.
    monkeypatch.setattr(LFRicConstants, "VALID_LOOP_TYPES", ["wrong"])
    with pytest.raises(InternalError) as err:
        DynLoop(loop_type="wrong")
    assert ("Unsupported loop type 'wrong' found when creating loop variable."
            " Supported values are 'colours'" in str(err.value))


def test_set_lower_bound_functions():
    ''' Test that we raise appropriate exceptions when the lower bound of
    a DynLoop is set to invalid values. '''
    schedule = Schedule()
    my_loop = DynLoop(parent=schedule)
    schedule.children = [my_loop]
    with pytest.raises(GenerationError) as excinfo:
        my_loop.set_lower_bound("invalid_loop_bounds_name")
    assert "lower bound loop name is invalid" in str(excinfo.value)
    with pytest.raises(GenerationError) as excinfo:
        my_loop.set_lower_bound("inner", index=0)
    assert "specified index" in str(excinfo.value)
    assert "lower loop bound is invalid" in str(excinfo.value)


def test_set_upper_bound_functions():
    ''' Test that we raise appropriate exceptions when the upper bound of
    a DynLoop is set to invalid values. '''
    schedule = Schedule()
    my_loop = DynLoop(parent=schedule)
    schedule.children = [my_loop]
    with pytest.raises(GenerationError) as excinfo:
        my_loop.set_upper_bound("invalid_loop_bounds_name")
    assert "upper loop bound name is invalid" in str(excinfo.value)
    with pytest.raises(GenerationError) as excinfo:
        my_loop.set_upper_bound("start")
    assert "'start' is not a valid upper bound" in str(excinfo.value)
    with pytest.raises(GenerationError) as excinfo:
        my_loop.set_upper_bound("inner", index=0)
    assert "specified index" in str(excinfo.value)
    assert "upper loop bound is invalid" in str(excinfo.value)


def test_lower_bound_fortran_1():
    '''tests we raise an exception in the DynLoop:_lower_bound_fortran()
    method - first GenerationError'''
    _, invoke_info = parse(os.path.join(BASE_PATH, "1_single_invoke.f90"),
                           api=TEST_API)
    psy = PSyFactory(TEST_API, distributed_memory=False).create(invoke_info)
    my_loop = psy.invokes.invoke_list[0].schedule.children[0]
    my_loop.set_lower_bound("inner", index=1)
    with pytest.raises(GenerationError) as excinfo:
        _ = my_loop._lower_bound_fortran()
    assert ("lower bound must be 'start' if we are sequential" in
            str(excinfo.value))


def test_lower_bound_fortran_2(monkeypatch):
    ''' Tests we raise an exception in the DynLoop:_lower_bound_fortran()
    method - second GenerationError. '''
    _, invoke_info = parse(os.path.join(BASE_PATH, "1_single_invoke.f90"),
                           api=TEST_API)
    psy = PSyFactory(TEST_API, distributed_memory=True).create(invoke_info)
    my_loop = psy.invokes.invoke_list[0].schedule.children[4]
    # We can not use the standard set_lower_bound function as that
    # checks for valid input
    monkeypatch.setattr(my_loop, "_lower_bound_name", value="invalid")
    with pytest.raises(GenerationError) as excinfo:
        _ = my_loop._lower_bound_fortran()
    assert ("Unsupported lower bound name 'invalid' found" in
            str(excinfo.value))


@pytest.mark.parametrize("name, index, output",
                         [("inner", 10, "inner_cell(11)"),
                          ("ncells", 10, "inner_cell(1)"),
                          ("cell_halo", 1, "ncells_cell()"),
                          ("cell_halo", 10, "cell_halo_cell(9)")])
def test_lower_bound_fortran_3(monkeypatch, name, index, output):
    ''' Test _lower_bound_fortran() with multiple valid iteration spaces. '''
    _, invoke_info = parse(os.path.join(BASE_PATH, "1_single_invoke.f90"),
                           api=TEST_API)
    psy = PSyFactory(TEST_API, distributed_memory=True).create(invoke_info)
    my_loop = psy.invokes.invoke_list[0].schedule.children[4]
    # We can not use the standard set_lower_bound function as that
    # checks for valid input
    monkeypatch.setattr(my_loop, "_lower_bound_name", value=name)
    monkeypatch.setattr(my_loop, "_lower_bound_index", value=index)
    assert my_loop._lower_bound_fortran() == "mesh%get_last_" + output + "+1"


def test_mesh_name():
    ''' Tests for the _mesh_name property of DynLoop. '''
    _, invoke_info = parse(os.path.join(BASE_PATH, "1_single_invoke.f90"),
                           api=TEST_API)
    psy = PSyFactory(TEST_API, distributed_memory=True).create(invoke_info)
    # TODO #1010. Replace this psy.gen with a call to lower_to_language_level()
    # pylint: disable=pointless-statement
    psy.gen
    loops = psy.invokes.invoke_list[0].schedule.walk(DynLoop)
    assert loops[0]._mesh_name == "mesh"


def test_mesh_name_intergrid():
    ''' Tests for the _mesh_name property of DynLoop. '''
    _, invoke_info = parse(os.path.join(BASE_PATH,
                                        "22.1_intergrid_restrict.f90"),
                           api=TEST_API)
    psy = PSyFactory(TEST_API, distributed_memory=True).create(invoke_info)
    # TODO #1010. Replace this psy.gen with a call to lower_to_language_level()
    # pylint: disable=pointless-statement
    psy.gen
    loops = psy.invokes.invoke_list[0].schedule.walk(DynLoop)
    assert loops[0]._mesh_name == "mesh_field1"


def test_upper_bound_fortran_1():
    '''tests we raise an exception in the DynLoop:_upper_bound_fortran()
    method when 'cell_halo', 'dof_halo' or 'inner' are used'''
    _, invoke_info = parse(os.path.join(BASE_PATH, "1_single_invoke.f90"),
                           api=TEST_API)
    psy = PSyFactory(TEST_API, distributed_memory=False).create(invoke_info)
    my_loop = psy.invokes.invoke_list[0].schedule.children[0]
    for option in ["cell_halo", "dof_halo", "inner"]:
        my_loop.set_upper_bound(option, index=1)
        with pytest.raises(GenerationError) as excinfo:
            _ = my_loop._upper_bound_fortran()
            assert (
                "'{0}' is not a valid loop upper bound for sequential/"
                "shared-memory code".format(option) in
                str(excinfo.value))


def test_upper_bound_fortran_2(monkeypatch):
    '''tests we raise an exception in the DynLoop:_upper_bound_fortran()
    method if an invalid value is provided'''
    _, invoke_info = parse(os.path.join(BASE_PATH, "1_single_invoke.f90"),
                           api=TEST_API)
    psy = PSyFactory(TEST_API, distributed_memory=False).create(invoke_info)
    my_loop = psy.invokes.invoke_list[0].schedule.children[0]
    monkeypatch.setattr(my_loop, "_upper_bound_name", value="invalid")
    with pytest.raises(GenerationError) as excinfo:
        _ = my_loop._upper_bound_fortran()
    assert (
        "Unsupported upper bound name 'invalid' found" in str(excinfo.value))
    # Pretend the loop is over colours and does not contain a kernel
    monkeypatch.setattr(my_loop, "_upper_bound_name", value="ncolours")
    monkeypatch.setattr(my_loop, "walk", lambda x: [])
    with pytest.raises(InternalError) as excinfo:
        _ = my_loop._upper_bound_fortran()
    assert ("Failed to find a kernel within a loop over colours"
            in str(excinfo.value))


def test_upper_bound_inner(monkeypatch):
    ''' Check that we get the correct Fortran generated if a loop's upper
    bound is "inner". '''
    _, invoke_info = parse(os.path.join(BASE_PATH, "1_single_invoke.f90"),
                           api=TEST_API)
    psy = PSyFactory(TEST_API, distributed_memory=True).create(invoke_info)
    my_loop = psy.invokes.invoke_list[0].schedule.children[4]
    monkeypatch.setattr(my_loop, "_upper_bound_name", value="inner")
    ubound = my_loop._upper_bound_fortran()
    assert ubound == "mesh%get_last_inner_cell(1)"


def test_upper_bound_ncolour(dist_mem):
    ''' Check that we get the correct Fortran for the upper bound of a
    coloured loop. '''
    _, invoke_info = parse(os.path.join(BASE_PATH, "1_single_invoke.f90"),
                           api=TEST_API)
    psy = PSyFactory(TEST_API, distributed_memory=dist_mem).create(invoke_info)
    sched = psy.invokes.invoke_list[0].schedule
    loops = sched.walk(DynLoop)
    # Apply a colouring transformation to the loop.
    trans = Dynamo0p3ColourTrans()
    trans.apply(loops[0])
    loops = sched.walk(DynLoop)
    if dist_mem:
        assert loops[1]._upper_bound_name == "colour_halo"
        assert (loops[1]._upper_bound_fortran() ==
                "last_cell_all_colours(colour, 1)")
        # Apply redundant computation to increase the depth of the access
        # to the halo.
        rtrans = Dynamo0p3RedundantComputationTrans()
        rtrans.apply(loops[1])
        assert (loops[1]._upper_bound_fortran() ==
                "last_cell_all_colours(colour, max_halo_depth_mesh)")
    else:
        assert loops[1]._upper_bound_name == "ncolour"
        assert (loops[1]._upper_bound_fortran() ==
                "last_cell_all_colours(colour)")


def test_upper_bound_ncolour_intergrid(dist_mem):
    ''' Check that we get the correct Fortran for a coloured loop's upper bound
    if it contains an inter-grid kernel. '''
    _, invoke_info = parse(os.path.join(BASE_PATH,
                                        "22.1_intergrid_restrict.f90"),
                           api=TEST_API)
    psy = PSyFactory(TEST_API, distributed_memory=dist_mem).create(invoke_info)
    sched = psy.invokes.invoke_list[0].schedule
    loops = sched.walk(DynLoop)
    # Apply a colouring transformation to the loop.
    trans = Dynamo0p3ColourTrans()
    trans.apply(loops[0])
    loops = sched.walk(DynLoop)
    if dist_mem:
        assert loops[1]._upper_bound_name == "colour_halo"
        assert (loops[1]._upper_bound_fortran() ==
                "last_cell_all_colours_field1(colour, 1)")
        # We can't apply redundant computation to increase the depth of the
        # access to the halo as it is not supported for inter-grid kernels.
        # Therefore we manually unset the upper bound halo depth to indicate
        # that we access the full depth.
        loops[1]._upper_bound_halo_depth = None
        assert (loops[1]._upper_bound_fortran() ==
                "last_cell_all_colours_field1(colour, "
                "max_halo_depth_mesh_field1)")
    else:
        assert loops[1]._upper_bound_name == "ncolour"
        assert (loops[1]._upper_bound_fortran() ==
                "last_cell_all_colours_field1(colour)")


def test_loop_start_expr(dist_mem):
    ''' Test that the start_expr property returns the expected reference
    to a symbol. '''
    _, invoke_info = parse(os.path.join(BASE_PATH, "1_single_invoke.f90"),
                           api=TEST_API)
    psy = PSyFactory(TEST_API, distributed_memory=dist_mem).create(invoke_info)
    # TODO #1010. Replace this psy.gen with a call to lower_to_language_level()
    # pylint: disable=pointless-statement
    psy.gen
    sched = psy.invokes.invoke_list[0].schedule
    loops = sched.walk(DynLoop)
    lbound = loops[0].start_expr
    assert isinstance(lbound, Reference)
    assert lbound.symbol.name == "loop0_start"


def test_loop_stop_expr(dist_mem):
    ''' Test the stop_expr property of a loop with and without colouring. '''
    _, invoke_info = parse(os.path.join(BASE_PATH, "1_single_invoke.f90"),
                           api=TEST_API)
    psy = PSyFactory(TEST_API, distributed_memory=dist_mem).create(invoke_info)
    # TODO #1010. Replace this psy.gen with a call to lower_to_language_level()
    # pylint: disable=pointless-statement
    psy.gen
    sched = psy.invokes.invoke_list[0].schedule
    loops = sched.walk(DynLoop)
    ubound = loops[0].stop_expr
    assert isinstance(ubound, Reference)
    assert ubound.symbol.name == "loop0_stop"
    # Apply a colouring transformation to the loop.
    trans = Dynamo0p3ColourTrans()
    trans.apply(loops[0])
    # TODO #1010. Replace this psy.gen with a call to lower_to_language_level()
    psy.gen
    sched = psy.invokes.invoke_list[0].schedule
    loops = sched.walk(DynLoop)
    ubound = loops[1].stop_expr
    assert isinstance(ubound, ArrayReference)
    assert ubound.symbol.name == "last_cell_all_colours"
    assert ubound.indices[0].name == "colour"
    if dist_mem:
        assert isinstance(ubound.indices[1], Literal)
        assert ubound.indices[1].value == "1"
        # Alter the loop so that it goes to the full halo depth
        loops[1]._upper_bound_halo_depth = None
        ubound = loops[1].stop_expr
        assert isinstance(ubound.indices[1], Reference)
        assert ubound.indices[1].symbol.name == "max_halo_depth_mesh"


def test_loop_stop_expr_intergrid(dist_mem):
    ''' Test the stop_expr property for a loop containing an
    inter-grid kernel. '''
    _, invoke_info = parse(os.path.join(BASE_PATH,
                                        "22.1_intergrid_restrict.f90"),
                           api=TEST_API)
    psy = PSyFactory(TEST_API, distributed_memory=dist_mem).create(invoke_info)
    # TODO #1010. Replace this psy.gen with a call to lower_to_language_level()
    # pylint: disable=pointless-statement
    psy.gen
    sched = psy.invokes.invoke_list[0].schedule
    loops = sched.walk(DynLoop)
    ubound = loops[0].stop_expr
    assert isinstance(ubound, Reference)
    assert ubound.symbol.name == "loop0_stop"
    # Apply a colouring transformation to the loop.
    trans = Dynamo0p3ColourTrans()
    trans.apply(loops[0])
    # TODO #1010. Replace this psy.gen with a call to lower_to_language_level()
    psy.gen
    sched = psy.invokes.invoke_list[0].schedule
    loops = sched.walk(DynLoop)
    ubound = loops[1].stop_expr
    assert isinstance(ubound, ArrayReference)
    assert ubound.symbol.name == "last_cell_all_colours_field1"
    assert ubound.indices[0].name == "colour"
    if dist_mem:
        assert isinstance(ubound.indices[1], Literal)
        assert ubound.indices[1].value == "1"
        # Alter the loop so that it goes to the full halo depth
        loops[1]._upper_bound_halo_depth = None
        ubound = loops[1].stop_expr
        assert isinstance(ubound.indices[1], Reference)
        assert ubound.indices[1].symbol.name == "max_halo_depth_mesh_field1"


def test_lfricloop_gen_code_err():
    ''' Test that the gen_code method raises the expected exception if the loop
    type is 'colours' and is within an OpenMP parallel region. '''
    _, invoke_info = parse(os.path.join(BASE_PATH, "1_single_invoke.f90"),
                           api=TEST_API)
    psy = PSyFactory(TEST_API, distributed_memory=False).create(invoke_info)
    sched = psy.invokes.invoke_list[0].schedule
    loops = sched.walk(DynLoop)
    # Apply a colouring transformation to the loop.
    trans = Dynamo0p3ColourTrans()
    trans.apply(loops[0])
    loops = sched.walk(DynLoop)
    # Parallelise the inner loop (over cells of a given colour)
    trans = DynamoOMPParallelLoopTrans()
    trans.apply(loops[1])
    # Alter the loop type manually
    loops[1]._loop_type = "colours"
    with pytest.raises(GenerationError) as err:
        loops[1].gen_code(None)
    assert ("Cannot have a loop over colours within an OpenMP parallel region"
            in str(err.value))


def test_dynloop_load_unexpected_func_space():
    ''' The load function of an instance of the DynLoop class raises an
    error if an unexpected function space is found. This test makes
    sure this error works correctly. It's a little tricky to raise
    this error as it is unreachable. However, we can sabotage an
    earlier function to make it return an invalid value.

    '''
    # first create a working instance of the DynLoop class
    _, invoke_info = parse(
        os.path.join(BASE_PATH, "19.1_single_stencil.f90"),
        api=TEST_API)
    psy = PSyFactory(TEST_API, distributed_memory=True).create(invoke_info)
    # now get access to the DynLoop class, the associated kernel class
    # and the associated field.
    schedule = psy.invokes.invoke_list[0].schedule
    loop = schedule.children[4]
    kernel = loop.loop_body[0]
    field = kernel.arguments.iteration_space_arg()
    # break the fields function space
    field._function_spaces[0]._orig_name = "broken"
    # create a function which always returns the broken field

    def broken_func():
        ''' Returns the above field no matter what '''
        return field
    # Replace the iteration_space_arg method with our broke
    # function. This is required as iteration_space_arg currently
    # never returns a field with an invalid function space.
    kernel.arguments.iteration_space_arg = broken_func
    # We can now raise the exception.
    with pytest.raises(GenerationError) as err:
        loop.load(kernel)
    const = LFRicConstants()
    assert ("Generation Error: Unexpected function space found. Expecting "
            "one of " + str(const.VALID_FUNCTION_SPACES) +
            " but found 'broken'" in str(err.value))


def test_unsupported_halo_read_access():
    ''' This test checks that we raise an error if the halo_read_access
    method finds an upper bound other than halo or ncells. The
    particular issue at the moment is that if inner is specified we do
    not know whether the stencil accesses the halo or not. However,
    this limitation is not going to affect anyone until we add in loop
    iteration space splitting transformations.

    '''
    # create a valid loop with a stencil access
    _, invoke_info = parse(
        os.path.join(BASE_PATH, "19.1_single_stencil.f90"),
        api=TEST_API)
    psy = PSyFactory(TEST_API, distributed_memory=True).create(invoke_info)
    # get access to the DynLoop object
    schedule = psy.invokes.invoke_list[0].schedule
    loop = schedule.children[4]
    # access to the argument that has a stencil access in the kernel
    kernel = loop.loop_body[0]
    stencil_arg = kernel.arguments.args[1]
    loop.set_upper_bound("inner", 1)
    # call our method
    with pytest.raises(GenerationError) as err:
        _ = loop._halo_read_access(stencil_arg)
    assert ("Loop bounds other than 'cell_halo' and 'ncells' are currently "
            "unsupported for kernels with stencil accesses. Found "
            "'inner'." in str(err.value))


def test_itn_space_write_w2broken_w1(dist_mem, tmpdir):
    ''' Check that generated loop over cells in the PSy layer has the
    correct upper bound when a kernel writes to two fields, the first on
    a discontinuous space (w2broken) and the second on a continuous space (w1).
    The resulting loop (when dm=True) must include the L1 halo because of
    the second field argument which is continuous.

    '''
    _, invoke_info = parse(
        os.path.join(BASE_PATH, "1.5.1_single_invoke_write_multi_fs.f90"),
        api=TEST_API)
    psy = PSyFactory(TEST_API,
                     distributed_memory=dist_mem).create(invoke_info)
    generated_code = str(psy.gen)

    assert "loop0_start = 1\n" in generated_code
    if dist_mem:
        assert "loop0_stop = mesh%get_last_halo_cell(1)\n" in generated_code
        output = (
            "      !\n"
            "      DO cell=loop0_start,loop0_stop\n")
        assert output in generated_code
    else:
        assert "loop0_stop = m2_proxy%vspace%get_ncell()\n" in generated_code
        output = (
            "      ! Call our kernels\n"
            "      !\n"
            "      DO cell=loop0_start,loop0_stop\n")
        assert output in generated_code

    assert LFRicBuild(tmpdir).code_compiles(psy)


def test_itn_space_fld_and_op_writers(tmpdir):
    ''' Check that generated loop over cells in the psy layer has the
    correct upper bound when a kernel writes to both an operator and a
    field, the latter on a discontinuous space and first in the list
    of args. (Loop must include L1 halo because we're writing to an
    operator.) '''
    _, invoke_info = parse(
        os.path.join(BASE_PATH, "1.5.2_single_invoke_write_fld_op.f90"),
        api=TEST_API)
    for dist_mem in [False, True]:
        psy = PSyFactory(TEST_API,
                         distributed_memory=dist_mem).create(invoke_info)
        generated_code = str(psy.gen)
        if dist_mem:
            assert ("loop0_stop = mesh%get_last_halo_cell(1)\n" in
                    generated_code)
            output = (
                "      !\n"
                "      DO cell=loop0_start,loop0_stop\n")
            assert output in generated_code
        else:
            assert ("loop0_stop = op1_proxy%fs_from%get_ncell()\n" in
                    generated_code)
            output = (
                "      ! Call our kernels\n"
                "      !\n"
                "      DO cell=loop0_start,loop0_stop")
            assert output in generated_code

        assert LFRicBuild(tmpdir).code_compiles(psy)


def test_itn_space_any_any_discontinuous(dist_mem, tmpdir):
    ''' Check that generated loop over cells has correct upper
    bound when a kernel writes to fields on any_space (continuous)
    and any_discontinuous_space.

    '''
    _, invoke_info = parse(
        os.path.join(BASE_PATH,
                     "1.5.3_single_invoke_write_any_anyd_space.f90"),
        api=TEST_API)
    psy = PSyFactory(TEST_API,
                     distributed_memory=dist_mem).create(invoke_info)
    generated_code = str(psy.gen)

    assert LFRicBuild(tmpdir).code_compiles(psy)

    assert "loop0_start = 1\n" in generated_code

    if dist_mem:
        assert "loop0_stop = mesh%get_last_halo_cell(1)" in generated_code
        output = (
            "      !\n"
            "      DO cell=loop0_start,loop0_stop\n")
        assert output in generated_code
    else:
        assert "loop0_stop = f1_proxy%vspace%get_ncell()" in generated_code
        output = (
            "      ! Call our kernels\n"
            "      !\n"
            "      DO cell=loop0_start,loop0_stop\n")
        assert output in generated_code


def test_itn_space_any_w2trace(dist_mem, tmpdir):
    ''' Check generated loop over cells has correct upper bound when a
    kernel writes to fields on any_space and W2trace (both continuous).

    '''
    _, invoke_info = parse(
        os.path.join(BASE_PATH,
                     "1.5.4_single_invoke_write_anyspace_w2trace.f90"),
        api=TEST_API)
    psy = PSyFactory(TEST_API,
                     distributed_memory=dist_mem).create(invoke_info)
    generated_code = str(psy.gen)

    assert LFRicBuild(tmpdir).code_compiles(psy)

    assert "loop0_start = 1\n" in generated_code

    if dist_mem:
        assert "loop0_stop = mesh%get_last_halo_cell(1)\n" in generated_code
        output = (
            "      !\n"
            "      DO cell=loop0_start,loop0_stop\n")
        assert output in generated_code
    else:
        # Loop upper bound should use f2 as that field is *definitely*
        # on a continuous space (as opposed to the one on any_space
        # that might be).
        assert "loop0_stop = f2_proxy%vspace%get_ncell()" in generated_code
        output = (
            "      ! Call our kernels\n"
            "      !\n"
            "      DO cell=loop0_start,loop0_stop\n")
        assert output in generated_code


def test_no_halo_for_discontinuous(tmpdir):
    ''' Test that we do not create halo exchange calls when our loop
    only iterates over owned cells (e.g. it writes to a discontinuous
    field), we only read from a discontinuous field and there are no
    stencil accesses '''
    _, info = parse(os.path.join(BASE_PATH,
                                 "1_single_invoke_w2v.f90"),
                    api=TEST_API)
    psy = PSyFactory(TEST_API, distributed_memory=True).create(info)
    result = str(psy.gen)
    assert "halo_exchange" not in result

    assert LFRicBuild(tmpdir).code_compiles(psy)


def test_halo_for_discontinuous(tmpdir, monkeypatch, annexed):
    '''This test checks the case when our loop iterates over owned cells
    (e.g. it writes to a discontinuous field), we read from a
    continuous field, there are no stencil accesses, but we do not
    know anything about the previous writer.

    As we don't know anything about the previous writer we have to
    assume that it may have been over dofs. If so, we could have dirty
    annexed dofs so need to add a halo exchange (for the three
    continuous fields being read (f1, f2 and m1). This is the case
    when api_config.compute_annexed_dofs is False.

    If we always iterate over annexed dofs by default, our annexed
    dofs will always be clean. Therefore we do not need to add a halo
    exchange. This is the case when
    api_config.compute_annexed_dofs is True.

    '''
    api_config = Config.get().api_conf(TEST_API)
    monkeypatch.setattr(api_config, "_compute_annexed_dofs", annexed)
    _, info = parse(os.path.join(BASE_PATH,
                                 "1_single_invoke_w3.f90"),
                    api=TEST_API)
    psy = PSyFactory(TEST_API, distributed_memory=True).create(info)
    result = str(psy.gen)
    if annexed:
        assert "halo_exchange" not in result
    else:
        assert "IF (f1_proxy%is_dirty(depth=1)) THEN" in result
        assert "CALL f1_proxy%halo_exchange(depth=1)" in result
        assert "IF (f2_proxy%is_dirty(depth=1)) THEN" in result
        assert "CALL f2_proxy%halo_exchange(depth=1)" in result
        assert "IF (m1_proxy%is_dirty(depth=1)) THEN" in result
        assert "CALL m1_proxy%halo_exchange(depth=1)" in result

    assert LFRicBuild(tmpdir).code_compiles(psy)


def test_halo_for_discontinuous_2(tmpdir, monkeypatch, annexed):
    '''This test checks the case when our loop iterates over owned cells
    (e.g. it writes to a discontinuous field), we read from a
    continuous field, there are no stencil accesses, and the previous
    writer iterates over ndofs or nannexed.

    When the previous writer iterates over ndofs we have dirty annexed
    dofs so need to add a halo exchange. This is the case when
    api_config.compute_annexed_dofs is False.

    When the previous writer iterates over nannexed we have clean
    annexed dofs so do not need to add a halo exchange. This is the
    case when api_config.compute_annexed_dofs is True

    '''
    api_config = Config.get().api_conf(TEST_API)
    monkeypatch.setattr(api_config, "_compute_annexed_dofs", annexed)
    _, info = parse(os.path.join(BASE_PATH,
                                 "14.7_halo_annexed.f90"),
                    api=TEST_API)
    psy = PSyFactory(TEST_API, distributed_memory=True).create(info)
    result = str(psy.gen)
    if annexed:
        assert "halo_exchange" not in result
    else:
        assert "IF (f1_proxy%is_dirty(depth=1)) THEN" not in result
        assert "CALL f1_proxy%halo_exchange(depth=1)" in result
        assert "IF (f2_proxy%is_dirty(depth=1)) THEN" not in result
        assert "CALL f2_proxy%halo_exchange(depth=1)" in result
        assert "IF (m1_proxy%is_dirty(depth=1)) THEN" in result
        assert "CALL m1_proxy%halo_exchange(depth=1)" in result

    assert LFRicBuild(tmpdir).code_compiles(psy)


def test_dynloop_halo_read_access_error1(monkeypatch):
    '''Test that the halo_read_access method in class DynLoop raises the
    expected exception when an unsupported field access is found.

    '''
    _, invoke_info = parse(os.path.join(BASE_PATH, "1_single_invoke.f90"),
                           api=TEST_API)
    psy = PSyFactory(TEST_API, distributed_memory=True).create(invoke_info)
    schedule = psy.invokes.invoke_list[0].schedule
    loop = schedule[4]
    kernel = loop.loop_body[0]
    field = kernel.arguments.args[1]
    monkeypatch.setattr(field, "_access", "unsupported")
    with pytest.raises(InternalError) as info:
        loop._halo_read_access(field)
    assert ("Unexpected field access type 'unsupported' found for arg 'f1'."
            in str(info.value))


def test_dynloop_halo_read_access_error2(monkeypatch):
    '''Test that the halo_read_access method in class DynLoop raises the
    expected exception when an unsupported field type is found.

    '''
    _, invoke_info = parse(os.path.join(BASE_PATH, "1_single_invoke.f90"),
                           api=TEST_API)
    psy = PSyFactory(TEST_API, distributed_memory=True).create(invoke_info)
    schedule = psy.invokes.invoke_list[0].schedule
    loop = schedule[4]
    kernel = loop.loop_body[0]
    field = kernel.arguments.args[1]
    monkeypatch.setattr(field, "_argument_type", "unsupported")
    with pytest.raises(InternalError) as info:
        loop._halo_read_access(field)
    assert ("Expecting arg 'f1' to be an operator, scalar or field, but "
            "found 'unsupported'." in str(info.value))


def test_null_loop():
    ''' Check that we can create a 'null'-type loop and that the validation
    check in the load() method behaves as expected.
    '''
    loop = DynLoop(loop_type="null")
    assert loop.loop_type == "null"
    assert loop.node_str(colour=False) == "Loop[type='null']"

    # Create a kernel by parsing some metadata
    ast = fpapi.parse('''
module testkern_mod
  type, extends(kernel_type) :: testkern_type
     type(arg_type), meta_args(2) =                         &
          (/ arg_type(gh_scalar, gh_real, gh_read),         &
             arg_type(gh_field,  gh_real, gh_readwrite, w3) &
           /)
     integer :: operates_on = cell_column
   contains
     procedure, nopass :: code => testkern_code
  end type testkern_type
contains
  subroutine testkern_code(a, b, c, d)
  end subroutine testkern_code
end module testkern_mod
''', ignore_comments=False)
    dkm = DynKernMetadata(ast, name="testkern_type")
    kern = DynKern()
    kern.load_meta(dkm)
    with pytest.raises(GenerationError) as err:
        loop.load(kern)
    assert ("A DynLoop of type 'null' can only contain a kernel that "
            "operates on the 'domain' but kernel 'testkern_code' operates "
            "on 'cell_column'" in str(err.value))
