r"""
File for the ring structure of Differential polynomials

This file contains all the element structures for Differential polynomials.

AUTHORS:

    - Antonio Jimenez-Pastor (2012-05-19): initial version

"""

# ****************************************************************************
#  Copyright (C) 2021 Antonio Jimenez-Pastor <ajpastor@risc.uni-linz.ac.at>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#                  https://www.gnu.org/licenses/
# ****************************************************************************

from sage.all import cached_method, ZZ

from sage.rings.polynomial.infinite_polynomial_ring import InfinitePolynomialGen
from sage.rings.polynomial.infinite_polynomial_element import InfinitePolynomial_dense, InfinitePolynomial_sparse

def is_InfinitePolynomial(element):
    r'''
        Method to decide whether or not an element is a polynomial with infinite variables.

        This is a call to ``isinstance`` with the two main element classes of Infinite Polynomial
        Rings.
    '''
    return (isinstance(element, InfinitePolynomial_dense) or isinstance(element, InfinitePolynomial_sparse))

class DiffPolynomialGen (InfinitePolynomialGen):
    def __init__(self, parent, name):
        from .differential_polynomial_ring import DiffPolynomialRing
        if(not (isinstance(parent, DiffPolynomialRing))):
            raise TypeError("The DiffPolynomialGen must have a DiffPolynomialRing parent")
        super().__init__(parent, name)

    def __getitem__(self, i):
        return self._parent(super().__getitem__(i))

    def contains(self, element):
        name = str(element)
        spl = name.split("_")
        first = "_".join(spl[:-1])
        return first == self._name

    def index(self, element):
        if(self.contains(element)):
            return int(str(element).split("_")[-1])

    def __hash__(self):
        return hash(self._name)

class DiffPolynomial (InfinitePolynomial_dense):
    r'''
        Class for representing differential polynomials.

        Given a differential ring `R`, we can define the ring of differential polynomials
        on `y` over `R` as the *infinite polynomial ring* 

        .. MATH::

            R[y_0, y_1,\ldots]

        where the derivation `\partial` has been uniquely extended such that, for all `n \in \mathbb{N}`:

        .. MATH::

            \partial(y_n) = y_{n+1}.

        The ring of differential polynomials on `y` over `R` is denoted by `R\{y\}`. We can iterate the 
        process to define th ring of differential polynomials in several variables:

        .. MATH::

            R\{y,z\} \simeq R\{y\}\{z\} \simeq R\{z\}\{y\}

        This object of this class represents the polynomials of a ring of differential polynomials. They 
        are a natural extension of the class :class:`~sage.rings.polynomial.infinite_polynomial_element.InfinitePolynomial_dense`
        including some extra functionality more specific of differential polynomials (such as the derivation and the evaluation).

        INPUT:

        * ``parent``: a :class:`~dalgebra.differential_polynomial.differential_polynomial_ring.DiffPolynomialRing` 
          where the new element will be contained.
        * ``polynomial``: a valid polynomial to be casted into an element of ``parent``.

        We recommend not to use this constructor, but instead build the polynomials using the generators of the 
        corresponding :class:`~dalgebra.differential_polynomial.differential_polynomial_ring.DiffPolynomialRing`.
    '''
    def __init__(self, parent, polynomial):
        if(is_InfinitePolynomial(polynomial)):
            polynomial = polynomial.polynomial()
        super().__init__(parent, polynomial)

    # Magic methods
    def __call__(self, *args, **kwargs):
        r'''
            Override of the __call__ method. 

            Evaluating a differential polynomial has a different meaning than evaluating a polynomial
            with infinitely many variables (see method 
            :func:`~dalgebra.differential_polynomial.differential_polynomial_ring.DiffPolynomialRing.eval`
            for further information)

            INPUT:

            * ``args`` and ``kwargs`` with the same format as in 
              :func:`~dalgebra.differential_polynomial.differential_polynomial_ring.DiffPolynomialRing.eval`

            OUTPUT:

            The evaluate object as in :func:`~dalgebra.differential_polynomial.differential_polynomial_ring.DiffPolynomialRing.eval`.

            EXAMPLES::

            sage: from dalgebra.differential_polynomial.differential_polynomial_ring import * 
                sage: R.<y> = DiffPolynomialRing(QQ['x']); x = R.base().gens()[0]
                sage: y[1](0)
                0
                sage: (y[0] + y[1])(x)
                x + 1
                sage: (y[0] + y[1])(y=x)
                x + 1

            This method commutes with the use of :func:`derivation`::

                sage: (x^2*y[1]^2 - y[2]*y[1]).derivative()(y=x) == (x^2*y[1]^2 - y[2]*y[1])(y=x).derivative()
                True

            This evaluation also works naturally with several infinite variables::

                sage: S = DiffPolynomialRing(R, 'a'); a,y = S.gens()
                sage: (a[1] + y[0]*a[0])(a=x, y=x^2)
                x^3 + 1
                sage: in_eval = (a[1] + y[0]*a[0])(y=x); in_eval
                a_1 + x*a_0
                sage: parent(in_eval)
                Ring of differential polynomials in (a) over [Univariate Polynomial Ring in x over Rational Field]
        '''
        return self.parent().eval(self, *args, **kwargs)

    # Arithmetic methods
    def _add_(self, x):
        return DiffPolynomial(self.parent(), super()._add_(x))
    def _sub_(self, x):
        return DiffPolynomial(self.parent(), super()._sub_(x))
    def _mul_(self, x):
        return DiffPolynomial(self.parent(), super()._mul_(x))
    def _rmul_(self, x):
        return DiffPolynomial(self.parent(), super()._rmul_(x))
    def _lmul_(self, x):
        return DiffPolynomial(self.parent(), super()._lmul_(x))
    def __pow__(self, n):
        return DiffPolynomial(self.parent(), super().__pow__(n))

    # Differential methods
    @cached_method
    def derivative(self, times=1):
        r'''
            Compute the derivative of a differential polynomial.

            Since the derivation for a differential polynomial is determined once 
            we know the derivation in the ring of coefficients, the only extra argument
            or this method is the amount of derivatives to compute.

            This method relies on the method 
            :func:`~dalgebra.differential_polynomial.differential_polynomial_ring.DiffPolynomialRing.derivation`.

            INPUT:

            * ``times``: amount of derivatives of ``self`` to be computed.
            
            OUTPUT:

            The ``times``-th derivative of ``self``.

            EXAMPLES::

                sage: from dalgebra.differential_polynomial.differential_polynomial_ring import * 
                sage: R.<y> = DiffPolynomialRing(QQ['x']); x = R.base().gens()[0]
                sage: y[0].derivative()
                y_1
                sage: y[1].derivative(5)
                y_6
                sage: (y[0]^3).derivative(times=3)
                3*y_3*y_0^2 + 18*y_2*y_1*y_0 + 6*y_1^3
                sage: (x*y[10]).derivative()
                x*y_11 + y_10
                sage: (x^2*y[1]^2 - y[2]*y[1]).derivative()
                -y_3*y_1 - y_2^2 + 2*x^2*y_2*y_1 + 2*x*y_1^2

            This derivation also works naturally with several infinite variables::

                sage: S = DiffPolynomialRing(R, 'a'); a,y = S.gens()
                sage: (a[1] + y[0]*a[0]).derivative()
                a_1*y_0 + a_0*y_1 + a_2
                sage: (a[0]*y[0]).derivative(2)
                a_2*y_0 + 2*a_1*y_1 + a_0*y_2
                sage: (a[0]*y[0]).derivative(3)
                a_3*y_0 + 3*a_2*y_1 + 3*a_1*y_2 + a_0*y_3
        '''
        if((not times in ZZ) or (times < 0)):
            raise ValueError("A differential polynomial can not be differentiated %s times" %times)
        elif(times == 0):
            return self
        elif(times > 1):
            return self.derivative(times=times-1).derivative()
        else:
            return self.parent().derivation(self)
