

class SymbolicMaths:
    _instance = None

    @staticmethod
    def get():
        if not SymbolicMaths._instance:
            try:
                # pylint: disable=unused-import
                import sympy
                SymbolicMaths._instance = SymbolicMathsSympy()
            except ImportError:
                SymbolicMaths._instance = SymbolicMathsSimple()
        return SymbolicMaths._instance


# ============================================================================
class SymbolicMathsSympy:

    def __init__(self):
        pass

    def greater_than(self, exp1, exp2):
        from psyclone.psyir.backend.fortran import FortranWriter
        import sympy
        fw = FortranWriter()
        str_exp1 = sympy.parse_expr(fw(exp1))
        str_exp2 = sympy.parse_expr(fw(exp2))
        result = sympy.simplify(str_exp1 > str_exp2)
        return result

    def greater_equal(self, exp1, exp2):
        import sympy
        from psyclone.psyir.backend.fortran import FortranWriter
        fw = FortranWriter()
        from sympy.parsing.sympy_parser import parse_expr
        str_exp1 = parse_expr(fw(exp1))
        str_exp2 = parse_expr(fw(exp2))
        result = sympy.simplify(str_exp1 >= str_exp2)
        return result


# ============================================================================
class SymbolicMathsSimple:
    '''Symbolic maths class that is not based on Sympy. It only offers
    limited capabilities, good enough for most typical use cases, but
    not all.

    '''

    def __init__(self):
        print("Creating simple")

    def greater_than(self, exp1, exp2):
        return True

    def greater_equal(self, exp1, exp2):
        return True
