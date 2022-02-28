# -----------------------------------------------------------------------------
# BSD 3-Clause License
#
# Copyright (c) 2021-2022, Science and Technology Facilities Council.
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
# Author: J. Henrichs, Bureau of Meteorology

''' Module containing py.test tests the SymPy writer.'''

from __future__ import print_function, absolute_import

import pytest
from sympy import Function, Symbol
from sympy.parsing.sympy_parser import parse_expr

from psyclone.psyir.backend.sympy_writer import SymPyWriter
from psyclone.psyir.nodes import Literal
from psyclone.psyir.symbols import BOOLEAN_TYPE, CHARACTER_TYPE


def test_sym_writer_constructor():
    '''Test that the constructor accepts an optional dictionary.
    '''
    sympy_writer = SymPyWriter({'some': 'symbol'})
    assert sympy_writer._sympy_type_map['some'] == 'symbol'
    # Also test that not specifying a type map as argument works:
    sympy_writer = SymPyWriter()
    assert sympy_writer._sympy_type_map == {}


def test_sym_writer_boolean():
    '''Test that booleans are written in the way that SymPy accepts.
    '''
    sympy_writer = SymPyWriter()
    lit = Literal("true", BOOLEAN_TYPE)
    assert sympy_writer(lit) == "True"
    lit = Literal("false", BOOLEAN_TYPE)
    assert sympy_writer(lit) == "False"


def test_sym_writer_character():
    '''Test that characters are rejected.
    '''
    sympy_writer = SymPyWriter({})
    lit = Literal("bla", CHARACTER_TYPE)

    with pytest.raises(TypeError) as err:
        sympy_writer(lit)

    assert "SymPy cannot handle strings like 'bla'." in str(err.value)


@pytest.mark.parametrize("expressions", [("2", "2"),
                                         ("123_4", "123"),
                                         ("456_8", "456"),
                                         ("123_xx", "123")
                                         ])
def test_sym_writer_int_constants(fortran_reader, expressions):
    '''Test that integer constants are handled, including precision
    specifications (either as int or as a name).
    '''
    # A dummy program to easily create the PSyIR for the
    # expressions we need. We just take the RHS of the assignments
    source = f'''program test_prog
                integer :: x
                x = {expressions[0]}
                end program test_prog '''
    psyir = fortran_reader.psyir_from_source(source)
    # psyir is a FileContainer, its first children the program, and its
    # first children the assignment, of which we take the right hand side
    lit = psyir.children[0].children[0].rhs

    type_map = SymPyWriter.create_type_map([])
    sympy_writer = SymPyWriter(type_map)
    assert sympy_writer(lit) == expressions[1]


@pytest.mark.parametrize("expressions", [("3.1415926535897932384626",
                                          "3.1415926535897932384626"),
                                         ("1.23E5", "1.23e5"),
                                         ("1.23D5", "1.23e5"),
                                         ("1.0E+3", "1.0e+3"),
                                         ("1.0", "1.0"),
                                         ("0.01E-3", "0.01e-3"),
                                         ("3.14e-2", "3.14e-2")
                                         ])
def test_sym_writer_real_constants(fortran_reader, expressions):
    '''Test that real constants are handled, including precision
    specifications (either as int or as a name).
    '''
    # A dummy program to easily create the PSyIR for the
    # expressions we need. We just take the RHS of the assignments
    source = f'''program test_prog
                integer :: x
                x = {expressions[0]}
                end program test_prog '''

    psyir = fortran_reader.psyir_from_source(source)
    lit = psyir.children[0].children[0].rhs
    type_map = SymPyWriter.create_type_map([])
    sympy_writer = SymPyWriter(type_map)
    assert sympy_writer(lit) == expressions[1]


@pytest.mark.parametrize("expressions", [("MAX(1,2)", "Max(1, 2)"),
                                         ("MIN(1,2)", "Min(1, 2)"),
                                         ("MOD(1,2)", "Mod(1, 2)"),
                                         ("LBOUND(1,2)", "LBOUND(1, 2)")
                                         ])
def test_sym_writer_functions(fortran_reader, expressions):
    '''Test that certain standard functions are recognised and
    converted into the equivalent SymPy syntax (capitalised first
    letter). Note LBOUND is not defined in SymPy, and as such is
    not converted.

    '''
    # A dummy program to easily create the PSyIR for the
    # expressions we need. We just take the RHS of the assignments
    source = f'''program test_prog
                integer :: x
                x = {expressions[0]}
                end program test_prog '''

    psyir = fortran_reader.psyir_from_source(source)
    function = psyir.children[0].children[0].rhs
    type_map = SymPyWriter.create_type_map([])
    sympy_writer = SymPyWriter(type_map)
    assert sympy_writer(function) == expressions[1]


@pytest.mark.parametrize("expressions", [("i", {'i': Symbol('i')}),
                                         ("f(1)", {'f': Function('f')}),
                                         ("f(:)", {'f': Function('f')}),
                                         ("a%b", {'a': Symbol('a')}),
                                         ("a%b(1)", {'a': Symbol('a')})
                                         ])
def test_sympy_writer_create_type_map(expressions, fortran_reader):
    '''Tests that the static create_type_map creates a dictionary
    with correctly declared references (and not any member names,
    which will be added later).
    '''

    # A dummy program to easily create the PSyIR for the
    # expressions we need. We just take the RHS of the assignments
    source = f'''program test_prog
                use my_mod
                type(my_type) :: a, b(10)
                integer :: i, f(10)
                x = {expressions[0]}
                end program test_prog '''

    psyir = fortran_reader.psyir_from_source(source)
    expr = psyir.children[0].children[0].rhs
    type_map = SymPyWriter.create_type_map([expr])
    assert type_map == expressions[1]


@pytest.mark.parametrize("expressions", [("a%x", "a%a_x"),
                                         ("b(i)%x", "b(i)%b_x"),
                                         ("a%x(i)", "a%a_x(i)"),
                                         ("b(j)%x(i)", "b(j)%b_x(i)"),
                                         ("b(i)%c(b_c)", "b(i)%b_c_1(b_c)"),
                                         ("a_c + a%c(i)", "a_c + a%a_c_1(i)"),
                                         ("b(b_c)%c(i)", "b(b_c)%b_c_1(i)"),
                                         ("b(b_c)%c(i)", "b(b_c)%b_c_1(i)"),
                                         ("a_b_c + a_b_c_1 + a%b%c",
                                          "a_b_c + a_b_c_1 + a%a_b%a_b_c_2"),
                                         ])
def test_sym_writer_rename_members(fortran_reader, expressions):
    '''Test that members are converted and get a unique name that
    does not clash with any other variable used in the expression.

    '''
    # A dummy program to easily create the PSyIR for the
    # expressions we need. We just take the RHS of the assignments
    source = f'''program test_prog
                use my_mod
                type(my_type) :: a, b(10)
                integer :: i, j, x, a_c, b_c, a_b_c, a_b_c_1
                x = {expressions[0]}
                end program test_prog '''

    psyir = fortran_reader.psyir_from_source(source)
    expr = psyir.children[0].children[0].rhs
    type_map = SymPyWriter.create_type_map([expr])
    sympy_writer = SymPyWriter(type_map)
    assert sympy_writer(expr) == expressions[1]


@pytest.mark.parametrize("expressions", [("a%x", {"a": Symbol("a"),
                                                  "a_x": Symbol("a_x")}),
                                         ("a%x(i)", {"a": Symbol("a"),
                                                     "a_x": Function("a_x"),
                                                     "i": Symbol("i")}),
                                         ("b(i)%x(i)", {"b": Function("b"),
                                                        "b_x": Function("b_x"),
                                                        "i": Symbol("i")}),
                                         ("b(b_c)%c(i)",
                                          {"b": Function("b"),
                                           "b_c": Symbol("b_c"),
                                           "b_c_1": Function("b_c_1"),
                                           "i": Symbol("i")}),
                                         ])
def test_sym_writer_symbol_types(fortran_reader, expressions):
    '''Tests that arrays are detected as SymPy functions, and scalars
    as SymPy symbols. The expressions parameter contains as first
    element the expression to parse, and as second element the
    expected mapping of names to SymPy functions or symbols.

    '''
    # A dummy program to easily create the PSyIR for the
    # expressions we need. We just take the RHS of the assignments
    source = f'''program test_prog
                use my_mod
                type(my_type) :: a, b(10)
                integer :: i, j, x, a_c, b_c, a_b_c, a_b_c_1
                x = {expressions[0]}
                end program test_prog '''

    psyir = fortran_reader.psyir_from_source(source)
    expr = psyir.children[0].children[0].rhs
    type_map = SymPyWriter.create_type_map([expr])
    sympy_writer = SymPyWriter(type_map)
    # Note that this call can extend the type_map with type information
    # about member names.
    _ = sympy_writer(expr)
    assert sympy_writer._sympy_type_map == expressions[1]


def test_sym_writer_convert_to_sympy_expressions(fortran_reader):
    '''Tests that convenience function `convert_to_sympy_expressions`
    works as expected.

    '''
    # A dummy program to easily create the PSyIR for the
    # expressions we need. We just take the RHS of the assignments
    source = '''program test_prog
                use my_mod
                type(my_type) :: a, b(10)
                integer :: i, j, x, a_c, b_c, a_b_c, a_b_c_1
                x = a%b + a%c(1) + i
                x = a_b + j
                end program test_prog '''

    psyir = fortran_reader.psyir_from_source(source)
    exp1 = psyir.children[0].children[0].rhs
    exp2 = psyir.children[0].children[1].rhs
    sympy_list = SymPyWriter.convert_to_sympy_expressions([exp1, exp2])

    assert sympy_list[0] == parse_expr("a%a_b_1 + a%a_c(1) + i")
    assert sympy_list[1] == parse_expr("a_b + j")
