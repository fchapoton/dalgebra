r"""
File for the structures concerning differential systems

This file contains the structures and main algorithms to manipulate
and study the solutions of differential systems expressed in terms of 
differential polynomials.

AUTHORS:

    - Antonio Jimenez-Pastor (2022-02-04): initial version

"""

# ****************************************************************************
#  Copyright (C) 2022 Antonio Jimenez-Pastor <jimenezpastor@lix.polytechnique.fr>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#                  https://www.gnu.org/licenses/
# ****************************************************************************

import logging

from functools import reduce

from sage.all import latex, ZZ, PolynomialRing, Compositions, Subsets, save
from sage.categories.pushout import pushout
from sage.misc.cachefunc import cached_method #pylint: disable=no-name-in-module

from .diff_polynomial_ring import is_DifferencePolynomialRing, is_DifferentialPolynomialRing, is_RWOPolynomialRing
from ..logging.logging import verbose

logger = logging.getLogger(__name__)

class RWOSystem:
    r'''
        Class for representing a system over a ring with an operator.

        This class allows the user to represent a system of equations 
        over a ring with an operator (see :class:`~dalgebra.ring_w_operator.ring_w_operator.RingsWithOperator`)
        as a list of infinite polynomials in one or several variables.

        This class will offer a set of methods and properties to extract the main
        information of the system and also the main algorithms and methods
        to study or manipulate these systems such as elimination procedures, etc.

        INPUT:

        * ``equations``: list or tuple of polynomials (see :class:`~dalgebra.diff_polynomial.diff_polynomial_element.RWOPolynomial`). 
          The system will be the one defined by `eq = 0` for all `eq` in the input ``equations``.
        * ``parent``: the common parent to transform the input. The final parent of all
          the elements will a common structure (if possible) that will be the 
          pushout of all the parents of ``elements`` and this structure.
        * ``variables``: list of names or infinite variables that will fix 
          the variables of the system. If it is not given, we will consider all the 
          differential variables as main variables.
    '''
    def __init__(self, equations, parent=None, variables=None):
        # Building the common parent
        parents = [el.parent() for el in equations]
        if(parent != None):
            parents.insert(0,parent)

        pushed = reduce(lambda p, q : pushout(p,q), parents)
        if(not is_RWOPolynomialRing(pushed)):
            raise TypeError("The common parent is nto a ring of differential polynomials. Not valid for a DifferentialSystem")

        self.__parent = pushed
        # Building the equations
        self.__equations = tuple([pushed(el) for el in equations])
        
        # Checking the argument `variables`
        if(variables != None):
            str_vars = [str(v) for v in variables]
            gens = [str(g) for g in self.parent().gens()]
            dvars = []
            for var in str_vars:
                if(not var in gens):
                    raise ValueError("The variable %s is not valid for a system in [%s]" %(var, self.parent()))
                dvars.append(self.parent().gens()[gens.index(var)])
        else:
            dvars = self.parent().gens()
        
        # setting up the differential variables
        self.__variables = tuple(dvars)
        self.__parameters = tuple([el for el in self.parent().gens() if (not el in dvars)])

        # cached variables
        self.__CACHED_SP1 = {}
        self.__CACHED_RES = None

    ## Getters for some properties
    @property
    def _equations(self): return self.__equations
    @property
    def variables(self): return self.__variables
    @property
    def parameters(self): return self.__parameters

    def parent(self):
        return self.__parent

    def size(self):
        return len(self._equations)

    @cached_method
    def is_DifferentialSystem(self):
        return is_DifferentialPolynomialRing(self.parent())
    @cached_method
    def is_DifferenceSystem(self):
        return is_DifferencePolynomialRing(self.parent())

    def order(self, gen=None):
        r'''
            Method to return the order of the system.

            The order of a system is defined as the maximal order of their equations. This 
            method allows a generator to be given and then the order w.r.t. this variable will 
            be computed. For further information, check 
            :func:`~dalgebra.diff_polynomial.diff_polynomial_element.RWOPolynomial.order`.
        '''
        return max(equ.order(gen) for equ in self.equations())

    def equation(self, index):
        r'''
            Method to get an equation from the system.

            This method allows to obtain one equation from this system. This means, obtain a 
            polynomial that is equal to zero, assuming the polynomials in ``self._equations`` are
            all equal to zero.

            This method allow to obtain the equations in ``self._equations`` but also the derived
            equations using the operation of the system.

            INPUT:

            * ``index``: the index for the equation desired. It can be a list/tuple with two elements
              `(i, n)` or a simple index `i`.

            OUTPUT:

            A polynomial with the `i`-th equation of the system. If the input was a tuple, then we return
            the `i`-th equation after applying the operation `n` times.

            EXAMPLES::

                sage: from dalgebra import *
                sage: bR = QQ[x]; x = bR('x')
                sage: R.<u,v> = DifferentialPolynomialRing(bR)
                sage: eq1 = u[0]*x - v[1]
                sage: eq2 = u[1] - (x-1)*v[0]
                sage: system = DifferentialSystem([eq1,eq2], variables=[u,v])
                sage: system.equation(0)
                x*u_0 - v_1
                sage: system.equation(1)
                u_1 + (-x + 1)*v_0

            If the index given is not in range, we raise a :class:`IndexError`::

                sage: system.equation(2)
                Traceback (most recent call last):
                ...
                IndexError: tuple index out of range

            And if the index is a tuple, we take the index rom th first element and the order as the second::

                sage: system.equation((0,1)) == eq1.derivative()
                True
                sage: system.equation((0,5)) == eq1.derivative(times=5)
                True
        '''
        if isinstance(index, (list,tuple)) and len(index) == 2:
            return self._equations[index[0]].operation(times=index[1])
        
        try:
            return self._equations[index]
        except TypeError:
            raise TypeError(f"The format for getting one equation is not valid. We got {index}")

    def equations(self, indices=None):
        r'''
            Method to get a list of equations to the system.

            This method allows to obtain a list of equations from the system, i.e., a list of polynomials
            that are assumed to be equal to zero. This method can also be used to get equations
            from extended systems.

            INPUT:

            * ``indices``: list or tuple of elements to be obtain. See method :func:`index` for further information.
              If the input is a ``slice``, we convert it into a list. If the input is not a list or a tuple, we 
              create  list with one element and try to get that element. If ``None`` is given, then 
              we return all equations.

            OUTPUT:
            
            A list of :class:`~dalgebra.diff_polynomial.diff_polynomial_element.RWOPolynomial` with the requested
            equations from this system.

            EXAMPLES::

                sage: from dalgebra import *
                sage: bR = QQ[x]; x = bR('x')
                sage: R.<u,v> = DifferentialPolynomialRing(bR)
                sage: eq1 = u[0]*x - v[1]
                sage: eq2 = u[1] - (x-1)*v[0]
                sage: system = DifferentialSystem([eq1,eq2], variables=[u,v])

            If nothing is given, we return all the equations::

                sage: system.equations()
                (x*u_0 - v_1, u_1 + (-x + 1)*v_0)

            If only an element is given, then we return that particular element::

                sage: system.equations(1)
                (u_1 + (-x + 1)*v_0,)

            Otherwise, we return the tuple with the equations required. This can be also 
            used to obtained equations after applying the operation (see :func:`equation`)::

                sage: system.equations([(0,0), (0,1), (1,3)])
                (x*u_0 - v_1, x*u_1 + u_0 - v_2, u_4 + (-x + 1)*v_3 + (-3)*v_2)

            This method also allows the use of :class:`slice` to provide the indices for equations::

                sage: system.equations(slice(None,None,-1)) # reversing the equations
                (u_1 + (-x + 1)*v_0, x*u_0 - v_1)
        '''
        if indices is None:
            return self._equations
        elif isinstance(indices, slice):
            indices = [el for el in range(*indices.indices(self.size()))]
        
        if not isinstance(indices, (list, tuple)):
            indices = [indices]
        
        return tuple([self.equation(index) for index in indices])

    def subsystem(self, indices, variables=None):
        r'''
            Method that creates a subsystem for a given set of equations.

            This method create a new :class:`RWOSystem` with the given variables in ``indices``
            (see :func:`get_equations` to see the format of this input) and setting as 
            main variables those given in ``variables`` (see in :class:`RWOSystem` the format for 
            this input).

            INPUT:

            * ``indices``: list or tuple of indices to select the subsystem. (see :func:`get_equations` 
              to see the format of this input).
            * ``variables``: list of variables for the new system. If ``None`` is given, we use the 
              variables of ``self``.

            OUTPUT:

            A new :class:`RWOSystem` with the new given equations and the variables stated in the input.

            EXAMPLES::

                sage: from dalgebra import *
                sage: bR = QQ[x]; x = bR('x')
                sage: R.<u,v> = DifferentialPolynomialRing(bR)
                sage: eq1 = u[0]*x - v[1]
                sage: eq2 = u[1] - (x-1)*v[0]
                sage: system = DifferentialSystem([eq1,eq2], variables=[u,v])
                sage: system.subsystem([(0,0), (0,1), (1,3)])
                System over [Ring of differential polynomials in (u, v) over Differential Ring 
                [Univariate Polynomial Ring in x over Rational Field] with derivation [Map from 
                callable d/dx]] with variables [(u_*, v_*)]:
                {
                    x*u_0 - v_1 == 0
                    x*u_1 + u_0 - v_2 == 0
                    u_4 + (-x + 1)*v_3 + (-3)*v_2 == 0
                }

            This method is used when using the ``__getitem__`` notation::

                sage: system[::-1] # same system but with equations changed in order
                System over [Ring of differential polynomials in (u, v) over Differential Ring 
                [Univariate Polynomial Ring in x over Rational Field] with derivation [Map from 
                callable d/dx]] with variables [(u_*, v_*)]:
                {
                    u_1 + (-x + 1)*v_0 == 0
                    x*u_0 - v_1 == 0
                }

            Setting up the argument ``variables`` allows to change the variables considered for the system::

                sage: system.subsystem(None, variables=[u])
                System over [Ring of differential polynomials in (u, v) over Differential Ring 
                [Univariate Polynomial Ring in x over Rational Field] with derivation [Map from 
                callable d/dx]] with variables [(u_*,)]:
                {
                    x*u_0 - v_1 == 0
                    u_1 + (-x + 1)*v_0 == 0
                }
        '''
        variables = self.variables if variables is None else variables

        return self.__class__(self.equations(indices), self.parent(), variables)

    def change_variables(self, variables):
        r'''
            Method that creates a new system with new set of main variables.

            This method returns an equivalent system as ``self``, i.e., with the same 
            equations and with the same parent. Bu now we fix a different set of 
            variables as main variables of the system.

            INPUT:

            * ``variables``: set of new variables for the system. See :class:`RWOSystem`
              to see the format for this input.

            OUTPUT:

            A :class:`RWOSystem` with the same equations but main variables given by ``variables``.

            EXAMPLES::

                sage: from dalgebra import *
                sage: bR = QQ[x]; x = bR('x')
                sage: R.<u,v> = DifferentialPolynomialRing(bR)
                sage: eq1 = u[0]*x - v[1]
                sage: eq2 = u[1] - (x-1)*v[0]
                sage: system = DifferentialSystem([eq1,eq2], variables=[u,v])
                sage: system.change_variables(u)
                System over [Ring of differential polynomials in (u, v) over Differential Ring 
                [Univariate Polynomial Ring in x over Rational Field] with derivation [Map from 
                callable d/dx]] with variables [(u_*,)]:
                {
                    x*u_0 - v_1 == 0
                    u_1 + (-x + 1)*v_0 == 0
                }
                sage: system.change_variables([v])
                System over [Ring of differential polynomials in (u, v) over Differential Ring 
                [Univariate Polynomial Ring in x over Rational Field] with derivation [Map from 
                callable d/dx]] with variables [(v_*,)]:
                {
                    x*u_0 - v_1 == 0
                    u_1 + (-x + 1)*v_0 == 0
                }
        '''
        if not isinstance(variables, (list, tuple)):
            variables = [variables]
        return self.subsystem(None, variables)

    ## magic methods
    def __getitem__(self, index):
        return self.__class__(self.equations(index), self.parent(), self.variables)

    def __repr__(self):
        return "System over [%s] with variables [%s]:\n{\n\t" %(self.parent(), self.variables) + "\n\t".join(["%s == 0" %el for el in self.equations()]) + "\n}"

    def __str__(self):
        return repr(self)

    def _latex_(self):
        result = r"\text{System over }" + latex(self.parent()) + r" \text{ with variables }" + ", ".join(latex(el) for el in self.variables) + ":\n\n"
        result += r"\left\{\begin{array}{ll}"
        result += "\n".join(latex(el) + r" & = 0 \\" for el in self.equations())
        result += "\n" + r"\end{array}\right."
        return result

    ## to algebraic methods
    @cached_method
    def algebraic_variables(self):
        r'''
            Method to retrieve the algebraic variables in the system.

            This method computes the number of algebraic variables that appear on the system. This means,
            gathering each appearance of the differential variables and filter them by the variables of the system.

            OUTPUT:

            A tuple containing the algebraic variables appearing in the system (as differential polynomials)

            EXAMPLES::

                sage: from dalgebra import *
                sage: R.<u> = DifferentialPolynomialRing(QQ)
                sage: system = DifferentialSystem([u[1]-u[0]])
                sage: system.algebraic_variables()
                (u_0, u_1)
                sage: R.<u,v> = DifferentialPolynomialRing(QQ[x]); x = R.base().gens()[0]
                sage: system = DifferentialSystem([x*u[0] + x^2*u[2] - (1-x)*v[0], v[1] - v[2] + u[1]])
                sage: system.algebraic_variables()
                (v_0, v_1, v_2, u_0, u_1, u_2)
                sage: system = DifferentialSystem([x*u[0] + x^2*u[2] - (1-x)*v[0], v[1] - v[2] + u[1]], variables = [u])
                sage: system.algebraic_variables()
                (u_0, u_1, u_2)
        '''
        all_vars = list(set(sum([[self.parent()(v) for v in equ.variables()] for equ in self.equations()], [])))
        filtered = [el for el in all_vars if any(el in g for g in self.variables)]
        filtered.sort()
        return tuple(filtered)

    @cached_method
    def algebraic_equations(self):
        r'''
            Method to get the equivalent algebraic equations.

            Considering a differential polynomial algebraically means to separate semantically
            the relation of different derivatives of a differential variable. This is mainly useful 
            once all differential operations are completed.

            OUTPUT:

            A tuple of polynomials in a common parent that represent the equations of ``self`` 
            in a purely algebraic context.

            EXAMPLES::

                sage: from dalgebra import *
                sage: R.<u> = DifferentialPolynomialRing(QQ)
                sage: system = DifferentialSystem([u[1]-u[0]])
                sage: system.algebraic_equations()
                (-u_0 + u_1,)
                sage: system.extend_by_operation([1]).algebraic_equations()
                (-u_0 + u_1, -u_1 + u_2)
                
            We can check that the parent of all the equations is the same::

                sage: parents = [el.parent() for el in system.extend_by_operation([1]).algebraic_equations()]
                sage: all(el == parents[0] for el in parents[1:])
                True
                sage: parents[0]
                Multivariate Polynomial Ring in u_0, u_1, u_2 over Differential 
                Ring [Rational Field] with derivation [Map from callable 0]

            The same can be checked for a multivariate differential polynomial::

                sage: R.<u,v> = DifferentialPolynomialRing(QQ[x]); x = R.base().gens()[0]
                sage: system = DifferentialSystem([x*u[0] + x^2*u[2] - (1-x)*v[0], v[1] - v[2] + u[1]])
                sage: system.algebraic_equations()
                ((x - 1)*v_0 + x*u_0 + x^2*u_2, v_1 - v_2 + u_1)
                sage: system.extend_by_operation([1,2]).algebraic_equations()
                ((x - 1)*v_0 + x*u_0 + x^2*u_2,
                v_0 + (x - 1)*v_1 + u_0 + x*u_1 + 2*x*u_2 + x^2*u_3,
                v_1 - v_2 + u_1,
                v_2 - v_3 + u_2,
                v_3 - v_4 + u_3)
                
            And the parents are again the same for all those equations::

                sage: parents = [el.parent() for el in system.extend_by_operation([1,2]).algebraic_equations()]
                sage: all(el == parents[0] for el in parents[1:])
                True
                sage: parents[0]
                Multivariate Polynomial Ring in v_0, v_1, v_2, v_3, v_4, u_0, u_1, u_2, u_3 over 
                Differential Ring [Univariate Polynomial Ring in x over Rational Field] with 
                derivation [Map from callable d/dx]

            The output of this method depends actively in the set of active variables that defines the system::

                sage: system_with_u = DifferentialSystem([x*u[0] + x^2*u[2] - (1-x)*v[0], v[1] - v[2] + u[1]], variables=[u])
                sage: system_with_u.algebraic_equations()                                                                                                                                        
                (x*u_0 + x^2*u_2 + (x - 1)*v_0, u_1 + v_1 - v_2)
                sage: system_with_u.extend_by_operation([1,2]).algebraic_equations()
                (x*u_0 + x^2*u_2 + (x - 1)*v_0,
                u_0 + x*u_1 + 2*x*u_2 + x^2*u_3 + v_0 + (x - 1)*v_1,
                u_1 + v_1 - v_2,
                u_2 + v_2 - v_3,
                u_3 + v_3 - v_4)

            In this case, the parent prioritize the variables related with `u_*`::

                sage: system_with_u.algebraic_equations()[0].parent()
                Multivariate Polynomial Ring in u_0, u_1, u_2 over Multivariate Polynomial 
                Ring in v_0, v_1, v_2 over Differential Ring [Univariate Polynomial Ring 
                in x over Rational Field] with derivation [Map from callable d/dx]
                sage: parents = [el.parent() for el in system_with_u.extend_by_operation([1,2]).algebraic_equations()]
                sage: all(el == parents[0] for el in parents[1:])
                True
                sage: parents[0]
                Multivariate Polynomial Ring in u_0, u_1, u_2, u_3 over Multivariate Polynomial 
                Ring in v_0, v_1, v_2, v_3, v_4 over Differential Ring [Univariate Polynomial 
                Ring in x over Rational Field] with derivation [Map from callable d/dx]

        '''
        equations = [el.polynomial() for el in self.equations()]
        ## Usual pushout leads to a CoercionException due to management of variables
        ## We do the pushout by ourselves by looking into the generators and creating the best 
        ## possible polynomial ring with the maximal possible derivatives
        max_orders = reduce(lambda p, q : [max(p[i],q[i]) for i in range(len(p))], [equ.orders() for equ in self.equations()])
        base_ring = self.parent().base()
        gens = self.parent().gens()
        variables = []
        parameters = []
        subs_dict = {}
        for i in range(len(gens)):
            if(gens[i] in self.variables):
                for j in range(max_orders[i]+1):
                    variables.append(gens[i][j])
                    subs_dict[str(gens[i][j])] = gens[i][j]
            else:
                for j in range(max_orders[i]+1):
                    parameters.append(gens[i][j])
                    subs_dict[str(gens[i][j])] = gens[i][j]
        variables.sort(); parameters.sort()
        

        inner_ring = base_ring if len(parameters) == 0 else PolynomialRing(base_ring, parameters)
        
        final_parent = PolynomialRing(inner_ring, variables)
        try:
            return tuple([final_parent(el(**subs_dict)) for el in equations])
        except TypeError:
            return tuple([final_parent(str(el)) for el in equations])

    ## SP properties
    def extend_by_operation(self, Ls):
        r'''
            Method that build an extended system that satisfies SP1.

            The condition SP1 is defined in the paper :doi:`10.1016/j.laa.2013.01.016` (Section 3) in regard with a 
            system of differential polynomial: let `\mathcal{P} = \{f_1,\ldots,f_m\}`. We say that an extended set of 
            differential polynomials `SP \subset \partial(\mathcal{P})` is SP1 for some `L_1,\ldots,L_m \in \mathbb{N}` if it can be written as:

            .. MATH::

                PS = \left\{\partial^{k}(f_i) \mid k \in \{0,\ldots,L_i\}, i=1,\ldots,m\right\}

            This method provides a way to build an extended system from ``self`` using the operator of the base ring 
            that satisfies condition SP1 for a fixed set of values of `L_1,\ldots,L_m`.

            INPUT:

            * `Ls`: list or tuple of non-negative integers of length ``self.size()``.

            OUTPUT:

            Another :class:`RWOSystem` extending ``self`` with the operation in the base ring that satisfies 
            SP1 for the given list of `L_i`.

            EXAMPLES::

                sage: from dalgebra import *
                sage: R.<u> = DifferentialPolynomialRing(QQ)
                sage: system = DifferentialSystem([u[1]-u[0]])
                sage: system.extend_by_operation([0]).equations()
                (u_1 - u_0,)
                sage: system.extend_by_operation([1]).equations()
                (u_1 - u_0, u_2 - u_1)
                sage: system.extend_by_operation([5]).equations()
                (u_1 - u_0, u_2 - u_1, u_3 - u_2, u_4 - u_3, u_5 - u_4, u_6 - u_5)
                sage: R.<u,v> = DifferentialPolynomialRing(QQ[x]); x = R.base().gens()[0]
                sage: system = DifferentialSystem([x*u[0] + x^2*u[2] - (1-x)*v[0], v[1] - v[2] + u[1]], variables = [u])
                sage: system.extend_by_operation([0,0]).equations()
                (x^2*u_2 + x*u_0 + (x - 1)*v_0, u_1 - v_2 + v_1)
                sage: system.extend_by_operation([1,0]).equations()
                (x^2*u_2 + x*u_0 + (x - 1)*v_0,
                x^2*u_3 + 2*x*u_2 + x*u_1 + u_0 + (x - 1)*v_1 + v_0,
                u_1 - v_2 + v_1)
                sage: system.extend_by_operation([1,1]).equations()
                (x^2*u_2 + x*u_0 + (x - 1)*v_0,
                x^2*u_3 + 2*x*u_2 + x*u_1 + u_0 + (x - 1)*v_1 + v_0,
                u_1 - v_2 + v_1,
                u_2 - v_3 + v_2)
        '''
        # Checking the input of L
        if(not isinstance(Ls, (list, tuple))):
            raise TypeError("The argument must be a list or tuple")
        if(any(not el in ZZ or el < 0 for el in Ls)):
            raise ValueError("The argument must be a list or tuple of non-negative integers")
        
        Ls = tuple(Ls)
        if(not Ls in self.__CACHED_SP1):
            new_equations = sum([[self.equation((i,k)) for k in range(Ls[i]+1)] for i in range(self.size())], [])
            self.__CACHED_SP1[Ls] = self.__class__(new_equations, self.parent(), self.variables)

        return self.__CACHED_SP1[Ls]

    build_sp1 = extend_by_operation #: alias for method :func:`extend_by_operation`
    
    @cached_method
    def is_homogeneous(self):
        r'''
            This method checks whether the system is homogeneous in the indicated variables.

            This method relies on the method :func:`algebraic_equations` and the method :func:`is_homogeneous`
            from the polynomial class in Sage.
        '''
        return all(equ.is_homogeneous() for equ in self.algebraic_equations())

    def is_linear(self, variables=None):
        r'''
            Method that checks whether a system is linear in its variables.

            See method :func:`~dalgebra.diff_polynomial.diff_polynomial_element.RWOPolynomial.is_linear` for further
            information on how this is computed.
        '''
        variables = self.variables if variables is None else variables

        return all(equ.is_linear(variables) for equ in self.equations())

    @cached_method
    def maximal_linear_variables(self):
        rejected = []
        allowed = []

        for s in Subsets(self.variables):
            if s.is_empty(): pass
            elif any(r.issubset(s) for r in rejected): pass
            elif self.is_linear(list(s)):
                allowed.append(s)
            else:
                rejected.append(s)

        allowed = sorted(allowed, key=lambda p:len(p)) # bigger elements last
        result = []
        while len(allowed) > 0:
            candidate = allowed.pop()
            if all(not candidate.issubset(r) for r in result):
                result.append(candidate)
        return result

    def is_sp2(self):
        r'''
            Method that checks the condition SP2.

            The condition SP2 is defined in the paper :doi:`10.1016/j.laa.2013.01.016` (Section 3) in regard with a 
            system of differential polynomial: let `\mathcal{P} = \{f_1,\ldots,f_m\}` be a system of differentially algebraic equations
            in the differential variables `\mathcal{U} = \{u_1,\ldots, u_n}`. We say that the system satisfies the condition SP2
            if and only if the number of variables is valid to compute a resultant algebraically.

            This quantity changing depending on whether the equations are homogeneous (same number of variables and equations)
            or not (one more equations than variables).

            It is interesting to remark that the algebraic variables of a differential polynomial are the total amount of
            variables that appears in it before the differential relation. Namely, the result of method 
            :func:`~dalgebra.diff_polynomial.diff_polynomial_element.RWOPolynomial.variables`
            provides the algebraic variables for a differential polynomial.

            OUTPUT:

            ``True`` if the system satisfies the condition SP2, ``False`` otherwise.

            EXAMPLES::

                sage: from dalgebra import *
                sage: R.<u,v> = DifferentialPolynomialRing(QQ[x]); x = R.base().gens()[0]
                sage: system = DifferentialSystem([x*u[0] + x^2*u[2] - (1-x)*v[0], v[1] - v[2] + u[1]], variables = [u])
                sage: system.is_sp2()
                False
                sage: system.extend_by_operation([1,2]).is_sp2()
                True

            WARNING: for this method it is crucial to know that the result depends directly on the set variables for 
            the system. Namely, having different set of active variables change the output of this method for *the same* 
            differential system::

                sage: same_system = DifferentialSystem([x*u[0] + x^2*u[2] - (1-x)*v[0], v[1] - v[2] + u[1]])
                sage: system.is_sp2()
                False
                sage: system.extend_by_operation([1,2]).is_sp2()
                True
        '''
        if(self.is_homogeneous()):
            return len(self.algebraic_variables()) == self.size()
        return len(self.algebraic_variables()) == self.size() - 1

    ## resultant methods
    @verbose(logger)
    def diff_resultant(self, bound_L = 10, alg_res = "auto"):
        r'''
            Method to compute the operator resultant of this system.

            TODO: add explanation of resultant.

            This method has the optional argument ``verbose`` which, when given, 
            will print the logging output in the console (``sys.stdout``)

            INPUT:

            * ``bound_L``: bound for the values of ``Ls`` for method :func:`extend_by_operation`.
            * ``alg_res``: (``"auto"`` by default) method to compute the algebraic resultant once we extended a 
              system to a valid system (see :func:`is_sp2`). The valid values are, currently,
              ``"dixon"``, ``"macaulay"`` and ``"iterative"``.

            OUTPUT:

            The resultant for this system.

            TODO: add examples
        '''
        if self.__CACHED_RES is None:
            ## Checking arguments
            if(not alg_res in ("auto", "iterative", "dixon", "macaulay")):
                raise ValueError("The algorithm for the algebraic resultant must be 'auto', 'dixon', 'macaulay' or 'iterative'")
            if alg_res == "auto":
                logging.info("Deciding automatically the algorithm for the resultant...")
                to_use_alg = self.__decide_resultant_algorithm()
            else:
                to_use_alg = alg_res
            
            ## Computing the resultant
            logging.info(f"We compute the resultant using the algorithm {to_use_alg}")
            if(to_use_alg == "dixon"):
                output = self.__dixon(bound_L)
            elif(to_use_alg == "macaulay"):
                output = self.__macaulay(bound_L)
            elif(to_use_alg == "iterative"):
                output = self.__iterative(bound_L, alg_res)

            if output == 0: # degenerate case
                raise ValueError(f"We obtained a zero resultant --> this is a degenerate case (used {to_use_alg})")
            self.__CACHED_RES = self.parent()(output)

        return self.__CACHED_RES

    ###################################################################################################
    ### Private methods concerning the resultant
    def __decide_resultant_algorithm(self):
        r'''
            Method to decide the (hopefully) most optimal algorithm to compute the resultant.
        '''
        if self.is_linear():
            logger.info("The system is linear: we use Macaulay")
            return "macaulay"
        else:
            logger.info("We could not decide a better algorithm: using iterative elimination")
            return "iterative"

    def __get_extension(self, bound):
        if(not bound in ZZ or bound < 0):
            raise ValueError("The bound for the extension must be a non-negative integer")

        ## auxiliary generator to iterate in a "balanced way"
        def gen_cartesian(size, bound):
            for i in range(bound*size):
                for c in Compositions(i+size, length=size, max_part=bound): #pylint: disable=unexpected-keyword-arg
                    yield tuple([el-1 for el in c])

        for L in gen_cartesian(self.size(), bound):
            logger.info(f"Trying the extension {L}")
            if(self.extend_by_operation(L).is_sp2()):
                logger.info(f"Found the valid extension {L}")
                break
        else: # if we don't break, we have found nothing --> error
            raise TypeError("The system was not nicely extended with bound %d" %bound)
        return L

    def __dixon(self, bound):
        r'''
            Method that computes the resultant of an extension of ``self` using Dixon resultant.

            INPUT:

            * ``bound``: bound the the extension to look for a system to get a resultant.
        '''
        raise NotImplementedError("Dixon resultant not yet implemented")
  
    def __macaulay(self, bound):
        r'''
            Method that computes the resultant of an extension of ``self` using Macaulay resultant.

            INPUT:

            * ``bound``: bound the the extension to look for a system to get a resultant.
        '''
        logger.info("Getting the appropriate extension for having a SP2 system...")
        L = self.__get_extension(bound)

        logger.info("Getting the homogenize version of the equations...")
        equs = [el.homogenize() for el in self.extend_by_operation(L).algebraic_equations()]
        ring = equs[0].parent()
        logger.info("Computing the Macaulay resultant...")
        return ring.macaulay_resultant(equs)
  
    def __iterative(self, bound, alg_res = "auto"):
        r'''
            Method that computes the resultant of an extension of ``self` using an iterative elimination.

            INPUT:

            * ``bound``: bound the the extension to look for a system to get a resultant.
        '''
        variables = [el for el in self.variables]
        ## This method first eliminate the linear variables
        logger.info("Checking if there is any linear variable...")
        lin_vars = self.maximal_linear_variables()
        if len(lin_vars) > 0 and alg_res != "iterative":
            lin_vars = list(lin_vars[0]) # we take the biggest subset
            logger.info(f"Found linear variables {lin_vars}: we remove {'it' if len(lin_vars) == 1 else 'them'} first...")
            logger.info("##########################################################")
            system = self.change_variables(lin_vars)
            # indices with the smallest equations
            smallest_equations = sorted(range(system.size()), key=lambda p:len(system.equation(p).monomials()))
            base_cases = smallest_equations[:len(lin_vars)]
            new_equations = [
                self.parent()(system.subsystem(base_cases + [i]).diff_resultant(bound))
                for i in smallest_equations[len(lin_vars):]
            ]
            logger.info("##########################################################")
            logger.info(f"Computed {len(new_equations)} equations for the remaining {len(variables)-len(lin_vars)} variables")
            rem_variables = [el for el in variables if (not el in lin_vars)]
            logger.info(f"We now remove {rem_variables}")
            system = self.__class__(new_equations, self.parent(), rem_variables)
            return system.diff_resultant(bound, alg_res)
        
        ## Logger printing
        if alg_res != "iterative":
            logger.info("No linear variable remain in the system. We proceed by univariate eliminations")
        else:
            logger.info("Forced iterative elimination. We do not look for linear variables")
        ## The remaining variables are not linear
        if len(self.variables) > 1:
            logger.info("Several eliminations are needed --> we use recursion")
            logger.info("Picking the best variable to start with...")
            v = self.__iterative_best_variable()
            logger.info(f"Picked differential variable {repr(v)}")
            rem_vars = [nv for nv in self.variables if nv != v]
            ## Picking the best diff_pivot equation
            if self.order(v) >= 0: # the variable appear in the system
                equs_by_order = sorted(
                    [i for i in range(self.size()) if self.equation(i).order(v) >= 0], 
                    key=lambda p:self.equation(p).order(v)
                )
                others = [i for i in range(self.size()) if (not i in equs_by_order)]
                if len(equs_by_order) < 2:
                    raise ValueError(f"Not enough equations to eliminate {repr(v)}")
                pivot = self.equation(equs_by_order[0])
                logger.info(f"Picked the pivot [{str(pivot)[:30]}...] for differential elimination")
                logger.info(f"Computing the elimination for all pair of equations...")
                new_equs = [
                    self.subsystem([equs_by_order[0], i], variables=[v]).diff_resultant(bound, alg_res) 
                    for i in equs_by_order[1:]
                ]
                logger.info(f"Adding equations without {repr(v)}...")
                new_equs += [self.equation(others[i]) for i in range(len(others))]
                system = self.__class__(new_equs, self.parent(), rem_vars)
                logger.info(f"Variable {repr(v)} eliminated. Proceeding with the remaining variables {rem_vars}...")
            else:
                logger.info(f"The variable {repr(v)} does not appear. Proceeding with the remaining variables {rem_vars}...")
                system = self.subsystem(variables = rem_vars)
            return system.diff_resultant(bound, alg_res)
        else:
            logger.info("Only one variable remains. We proceed to eliminate it in an algebraic fashion")
            logger.info(f"Extending the system to eliminate {repr(self.variables[0])}...")
            L = self.__get_extension(bound)
            system = self.extend_by_operation(L) # now we can eliminate everything
            alg_equs = list(system.algebraic_equations())
            alg_vars = [alg_equs[0].parent()(str(el)) for el in system.algebraic_variables()]

            logger.info(f"Iterating to remove all the algebraic variables...")
            logger.info(f"--------------------------------------------------")
            last_index = lambda l, value : len(l) - 1 - l[::-1].index(value)
            while(len(alg_equs) > 1 and len(alg_vars) > 0):
                logger.info(f"\tRemaining variables: {alg_vars}")
                logger.info(f"\tPicking best algebraic variable to eliminate...")
                # getting th degrees of each variable in each equation
                degrees = [[equ.degree(v) for equ in alg_equs] for v in alg_vars]
                # the best variable to remove is the one that appears the least
                num_appearances = [len(alg_equs)-degrees[i].count(0) for i in range(len(alg_vars))]
                logger.info(f"\tNumber of appearance for each variable: {num_appearances}. Number of equations: {len(alg_equs)}")
                iv = last_index(num_appearances,min(num_appearances))
                v = alg_vars.pop(iv)
                logger.info(f"\tPicked {v}")

                # the "pivot" equation is the one with minimal degree in "v"
                logger.info(f"\tPicking the best 'pivot' to eliminate {v}...")
                pivot = alg_equs.pop(degrees[iv].index(min([el for el in degrees[iv] if el > 0])))
                R = pivot.parent()
                pivot = self.__iterative_to_univariate(pivot, v)
                logger.info(f"\t- Pivot --> {str(pivot)[:30]}... [with {len(pivot.monomials())} monomials and coefficients {max(len(str(c)) for c in pivot.coefficients())} long]")
                logger.info(f"\tEliminating the variable {v} in each pair of equations...")
                for i in range(len(alg_equs)):
                    if alg_equs[i].degree(v) > 0:
                        equ_to_eliminate = self.__iterative_to_univariate(alg_equs[i], v)
                        logger.info(f"\tEliminating with {str(equ_to_eliminate)[:30]}... [with {len(equ_to_eliminate.monomials())} monomials and coefficients {max(len(str(c)) for c in equ_to_eliminate.coefficients())} long]")
                        logger.info(f"\tComputing Sylvester matrix...")

                        syl_mat = pivot.sylvester_matrix(equ_to_eliminate)
                        if len(alg_vars) == 0:
                            logger.info(f"\tStoring Sylvester matrix...")
                            with open("./sylvester_matrix.txt", "w") as syl_file:
                                syl_file.write(f"{syl_mat.nrows()},{syl_mat.ncols()}\n")
                                for r in range(syl_mat.nrows()):
                                    for c in range(syl_mat.ncols()):
                                        syl_file.write(f"{r},{c};{str(syl_mat[r][c])}\n")

                        logger.info(f"\tComputing Sylvester determinant...")
                        alg_equs[i] = R(str(syl_mat.determinant()))
            ## Checking the result
            logger.info(f"--------------------------------------------------")
            logger.info(f"Elimination procedure finished. Checking that we have a result...")
            old_vars = self.algebraic_variables()
            new_vars = list(set(sum([list(set(el.variables())) for el in alg_equs],[])))
            if any(el in old_vars for el in new_vars):
                raise ValueError(f"A variable that had to be eliminated remains!!\n\
                    \t-Old vars: {old_vars}\n\
                    \t-Got vars:{new_vars}")
            
            ## We pick the minimal equation remaining
            logger.info(f"Return the smallest result obtained")
            return sorted(alg_equs, key=lambda p: p.degree()**2 + len(p.monomials()))[0]

    def __iterative_best_variable(self):
        r'''
            Method to choose the best variable to do univariate elimination.
        '''
        v = self.variables[0]
        def measure(v):
            c = 0
            for equ in self.equations():
                for t in equ.polynomial().variables():
                    if t in v:
                        c += v.index(t)**equ.polynomial().degree(t)
            return c
        m = measure(v)
        for nv in self.variables[1:]:
            nm = measure(nv)
            if nm < m: 
                v = nv
                m = nm
                
        return v

    def __iterative_to_univariate(self, polynomial, variable):
        try:
            return polynomial.polynomial(variable)
        except:
            return polynomial.parent().univariate_ring(variable)(str(polynomial))

    ###################################################################################################

class DifferentialSystem (RWOSystem):
    r'''
        Class representing a differential system.

        This class allows the user to represent a system of differential equations 
        as a list of differential polynomials in one or several variables.

        This class will offer a set of methods and properties to extract the main
        information of the differential system and also the main algorithms and methods
        to study or manipulate these systems.

        INPUT:

        * ``equations``: list or tuple of differential polynomials. The system will
          be the one defined by `eq = 0` for all `eq` in the input ``equations``.
        * ``parent``: the common parent to transform the input. The final parent of all
          the elements will a common structure (if possible) that will be the 
          pushout of all the parents of ``elements`` and this structure.
        * ``variables``: list of names or differential variables that will fix 
          the variables of the system. If it is not given, we will consider all the 
          differential variables as main variables.
    '''
    def __init__(self, equations, parent=None, variables=None):
        super().__init__(equations, parent, variables)

        if not is_DifferentialPolynomialRing(self.parent()):
            raise TypeError("The common parent is nto a ring of differential polynomials. Not valid for a DifferentialSystem")

    extend_by_derivation = RWOSystem.extend_by_operation #: new alias for :func:`extend_by_operation`

class DifferenceSystem (RWOSystem):
    r'''
        Class representing a difference system.

        This class allows the user to represent a system of difference equations 
        as a list of difference polynomials in one or several variables.

        This class will offer a set of methods and properties to extract the main
        information of the difference system and also the main algorithms and methods
        to study or manipulate these systems.

        INPUT:

        * ``equations``: list or tuple of difference polynomials. The system will
          be the one defined by `eq = 0` for all `eq` in the input ``equations``.
        * ``parent``: the common parent to transform the input. The final parent of all
          the elements will a common structure (if possible) that will be the 
          pushout of all the parents of ``elements`` and this structure.
        * ``variables``: list of names or difference variables that will fix 
          the variables of the system. If it is not given, we will consider all the 
          difference variables as main variables.
    '''
    def __init__(self, equations, parent=None, variables=None):
        super().__init__(equations, parent, variables)

        if not is_DifferencePolynomialRing(self.parent()):
            raise TypeError("The common parent is nto a ring of difference polynomials. Not valid for a DifferenceSystem")

    extend_by_difference = RWOSystem.extend_by_operation #: new alias for :func:`extend_by_operation`

__all__ = ["DifferentialSystem", "DifferenceSystem"]