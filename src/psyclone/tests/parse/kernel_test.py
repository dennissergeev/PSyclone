# -----------------------------------------------------------------------------
# BSD 3-Clause License
#
# Copyright (c) 2019, Science and Technology Facilities Council.
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
# Authors R. W. Ford and A. R. Porter, STFC Daresbury Lab

'''A module to perform pytest unit tests on the parse/kernel.py
file. Some tests for this file are in parse_test.py. This file adds
tests for code that is not covered there.'''

import os
import pytest
from psyclone.parse.kernel import KernelType, get_kernel_metadata, \
    KernelProcedure, Descriptor, BuiltInKernelTypeFactory, get_kernel_filepath
from psyclone.parse.utils import ParseError
from fparser.api import parse

from fparser.common.readfortran import FortranStringReader
from fparser.two.parser import ParserFactory
import fparser.two.Fortran2003 as f2003
from fparser.two.utils import walk_ast
from psyclone.psyGen import InternalError

# pylint: disable=invalid-name


CODE = (
    "module test_mod\n"
    "  type, extends(kernel_type) :: test_type\n"
    "    type(arg_type), dimension(1) :: meta_args =    &\n"
    "          (/ arg_type(gh_field,gh_write,w1) /)\n"
    "     integer :: iterates_over = cells\n"
    "   contains\n"
    "     procedure, nopass :: code => test_code\n"
    "  end type test_type\n"
    "contains\n"
    "  subroutine test_code()\n"
    "  end subroutine test_code\n"
    "end module test_mod\n"

    )

# class KernelType methods get_integer_array, getkerneldescriptors
# TBD
# class KernelProcedure method get_procedure
# TBD

# function get_kernel_metadata


def test_getkernelmetadata_works(parser):
    '''Check that get_kernel_metadata returns the expected type.'''
    reader = FortranStringReader(CODE)
    parse_tree = parser(reader)
    result = get_kernel_metadata("test_type", parse_tree)
    assert isinstance(result, f2003.Derived_Type_Def)
    assert str(result.content[0].items[1]) == "test_type"


def test_getkernelmetadata_error1(monkeypatch, parser):
    '''Check that get_kernel_metadata raises an exception if an fparser2
    class instance does not have the expected method, or if the
    expected index is greater than the size of the list.

    '''
    reader = FortranStringReader(CODE)
    parse_tree = parser(reader)
    type_defs = walk_ast([parse_tree], [f2003.Derived_Type_Def])

    monkeypatch.setattr(type_defs[0], "content", [None])
    with pytest.raises(InternalError) as excinfo:
        _ = get_kernel_metadata("test_type", parse_tree)
    assert "Can't get name from derived type definition." in str(excinfo.value)

    monkeypatch.setattr(type_defs[0], "content", [])
    with pytest.raises(InternalError) as excinfo:
        _ = get_kernel_metadata("test_type", parse_tree)
    assert "Can't get name from derived type definition." in str(excinfo.value)


def test_getkernelmetadata_error2(monkeypatch, parser):
    '''Check that get_kernel_metadata raises an exception if an expected
    Derived_Type_Stmt instance is in-fact a different class instance.

    '''
    reader = FortranStringReader(CODE)
    parse_tree = parser(reader)
    type_defs = walk_ast([parse_tree], [f2003.Derived_Type_Def])

    class Dummy():
        '''A dummy replacement class for derived type statement.'''
        items = [None, None]

    monkeypatch.setattr(type_defs[0], "content", [Dummy()])
    with pytest.raises(InternalError) as excinfo:
        _ = get_kernel_metadata("test_type", parse_tree)
    assert ("First child of derived type definition is not a derived type "
            "statement.") in str(excinfo.value)


def test_getkernelmetadata_error3(monkeypatch, parser):
    '''Check that get_kernel_metadata raises an exception if an expected
    Name instance is in-fact a different class instance.

    '''
    reader = FortranStringReader(CODE)
    parse_tree = parser(reader)
    type_defs = walk_ast([parse_tree], [f2003.Derived_Type_Def])

    monkeypatch.setattr(type_defs[0].content[0], "items", [None, None])
    with pytest.raises(InternalError) as excinfo:
        _ = get_kernel_metadata("test_type", parse_tree)
    assert ("Second child of derived type statement is not a Name.") \
        in str(excinfo.value)


def test_getkernelmetadata_not_found(monkeypatch, parser):
    '''Check that get_kernel_metadata raises an exception if an expected
    Name instance is in-fact a different class instance.

    '''
    reader = FortranStringReader(CODE)
    parse_tree = parser(reader)
    type_defs = walk_ast([parse_tree], [f2003.Derived_Type_Def])

    with pytest.raises(ParseError) as excinfo:
        _ = get_kernel_metadata("does_not_exist", parse_tree)
    assert ("Kernel type 'does_not_exist' does not exist.") \
        in str(excinfo.value)

# function get_kernel_filepath


def test_getkernelfilepath_nodir():
    '''Test that an appropriate exception is raised if the specified
    directory does not exist.

    '''
    with pytest.raises(ParseError) as excinfo:
        _ = get_kernel_filepath("test_mod", "non/existant/file/path", None)
    assert ("Supplied kernel search path does not exist or cannot be "
            "read") in str(excinfo.value)


def test_getkernelfilepath_multifile(tmpdir):
    '''Test that an appropriate exception is raised if more than one file
    matches when searching for kernels.

    '''
    filename = str(tmpdir.join("test_mod.f90"))
    ffile = open(filename, "w")
    ffile.write("")
    ffile.close()
    os.mkdir(str(tmpdir.join("tmp")))
    filename = str(tmpdir.join("tmp", "test_mod.f90"))
    ffile = open(filename, "w")
    ffile.write("")
    ffile.close()

    with pytest.raises(ParseError) as excinfo:
        _ = get_kernel_filepath("test_mod", str(tmpdir), None)
    assert ("More than one match for kernel file 'test_mod.[fF]90' "
            "found!") in str(excinfo.value)

# class BuiltInKernelTypeFactory():create test


def test_builtinfactory_metadataerror(monkeypatch):
    '''Test that an appropriate exception is raised if the builtin
    metadata cannot be parsed. This is difficult to trigger so use
    monkeypatch. We just need to make the call to the parse function
    raise an exception. This can be simply done by setting it to None
    (which gives a TypeError as it is not callable).

    '''
    from psyclone.dynamo0p3_builtins import BUILTIN_MAP as builtins
    from psyclone.dynamo0p3_builtins import BUILTIN_DEFINITIONS_FILE as \
        fname
    from fparser import api as fpapi
    monkeypatch.setattr(fpapi, "parse", None)
    factory = BuiltInKernelTypeFactory()
    with pytest.raises(ParseError) as excinfo:
        _ = factory.create(builtins.keys(), fname, "setval_c")
    assert "Failed to parse the meta-data for PSyclone built-ins" \
        in str(excinfo.value)

# class Descriptor() test


def test_descriptor_repr():
    '''Test that the __repr__ method in Descriptor() behaves as
    expected.

    '''
    tmp = Descriptor("gh_inc", "w1")
    assert repr(tmp) == "Descriptor(gh_inc, w1)"

# class KernelProcedure() test utility


def create_kernelprocedure(code):
    '''Support function that attempts to create an instance of the
    'KernelProcedure' class. It is assumed that the name of the
    metadata is 'test_type' which matches the example code in the
    'CODE' variable. The code is passed in by argument as it might be
    necessary to modify it beforehand.

    :param str code: kernel code

    :returns: An instance of the KernelProcedure class
    :rtype: :py:class:`psyclone.parse.kernel.KernelProcedure`

    '''
    module_parse_tree = parse(code)
    kernel_type_name = "test_type"
    kernel_type_parse_tree = get_kernel_metadata(kernel_type_name,
                                                 module_parse_tree)
    return KernelProcedure(kernel_type_parse_tree, kernel_type_name,
                           module_parse_tree)

# class KernelProcedure():get_procedure tests


def test_kernelprocedure_notfound():
    '''Test that the appropriate exception is raised if the kernel
    subroutine specified in the kernel metadata does not exist in the
    module.

    '''
    with pytest.raises(ParseError) as excinfo:
        my_code = CODE.replace("=> test_code", "=> non_existant_code")
        _ = create_kernelprocedure(my_code)
    assert "Kernel subroutine 'non_existant_code' not found." \
        in str(excinfo.value)

# class KernelProcedure() tests


def test_kernelprocedure_repr():
    '''Test that the __repr__ method in KernelProcedure() behaves as
    expected.

    '''
    tmp = create_kernelprocedure(CODE)
    assert repr(tmp) == ("KernelProcedure(test_code)")


def test_kernelprocedure_str():
    '''Test that the __str__ method in KernelProcedure() behaves as
    expected.

    '''
    tmp = create_kernelprocedure(CODE)
    assert str(tmp) == ("    SUBROUTINE test_code()\n"
                        "    END SUBROUTINE test_code")

# class KernelType():getkerneldescriptors tests


def test_kerneltype_typename():
    '''Test that an exception is raised if the metadata type name is not
    what was expected.

    '''
    my_code = CODE.replace("meta_args", "invalid_name")
    parse_tree = parse(my_code)

    with pytest.raises(ParseError) as excinfo:
        _ = KernelType(parse_tree)
    assert "No kernel metadata with type name 'meta_args' found." \
        in str(excinfo.value)


def test_kerneltype_array():
    '''Test that an exception is raised if the metadata variable is not an
    array.

    '''
    my_code = CODE.replace(", dimension(1)", "")
    parse_tree = parse(my_code)

    with pytest.raises(ParseError) as excinfo:
        _ = KernelType(parse_tree)
    assert ("In kernel metadata 'test_type': 'meta_args' variable must be "
            "an array.") in str(excinfo.value)


def test_kerneltype_dimensions():
    '''Test that an exception is raised if the metadata variable is a
    multi-dimensional array.

    '''
    my_code = CODE.replace("dimension(1)", "dimension(1,1)")
    parse_tree = parse(my_code)

    with pytest.raises(ParseError) as excinfo:
        _ = KernelType(parse_tree)
    assert ("In kernel metadata 'test_type': 'meta_args' variable must be a "
            "1 dimensional array") in str(excinfo.value)


def test_kerneltype_brackets():
    '''Test that an exception is raised if the metadata is supplied within
    square brackets as this is not supported within the parser.

    '''
    my_code = CODE.replace("(/", "[")
    my_code = my_code.replace("/)", "]")
    parse_tree = parse(my_code)

    with pytest.raises(ParseError) as excinfo:
        _ = KernelType(parse_tree)
    assert ("Parser does not currently support [...] initialisation for "
            "'meta_args', please use (/.../) instead.") in str(excinfo.value)


def test_kerneltype_nargs():
    '''Test that an exception is raised if the number of arguments does
    not match the specified number of arguments in the kernel
    metadata.

    '''
    my_code = CODE.replace("dimension(1)", "dimension(2)")
    parse_tree = parse(my_code)

    with pytest.raises(ParseError) as excinfo:
        _ = KernelType(parse_tree)
    assert ("In the 'meta_args' metadata, the number of args '2' and extent "
            "of the dimension '1' do not match.") in str(excinfo.value)


def test_kerneltype_repr():
    '''Test that the __repr__ method in KernelType() behaves as expected.'''

    parse_tree = parse(CODE)

    tmp = KernelType(parse_tree)
    assert repr(tmp) == "KernelType(test_type, cells)"
