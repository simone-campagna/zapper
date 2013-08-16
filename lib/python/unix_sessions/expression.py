#!/usr/bin/env python3
#
# Copyright 2013 Simone Campagna
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

__author__ = 'Simone Campagna'

import abc

class Expression(metaclass=abc.ABCMeta):
    def __init__(self):
        pass

    def _coerce_operand(self, other):
        if isinstance(other, Expression):
            return other
        else:
            return ConstExpression(other)

    def bind(self, instance):
        pass

    @abc.abstractmethod
    def get_value(self):
        pass

    @abc.abstractmethod
    def __str__(self):
        pass

    def __and__(self, other):
        return And(self, other)

    def __rand__(self, other):
        return And(other, self)

    def __or__(self, other):
        return Or(self, other)

    def __ror__(self, other):
        return Or(other, self)

    def __add__(self, other):
        return Add(self, other)

    def __radd__(self, other):
        return Add(other, self)

    def __sub__(self, other):
        return Sub(self, other)

    def __rsub__(self, other):
        return Sub(other, self)

    def __mul__(self, other):
        return Mul(self, other)

    def __rmul__(self, other):
        return Mul(other, self)

    def __div__(self, other):
        return Div(self, other)

    def __rdiv__(self, other):
        return Div(other, self)

    def __truediv__(self, other):
        return TrueDiv(self, other)

    def __rtruediv__(self, other):
        return TrueDiv(other, self)

    def __floordiv__(self, other):
        return Flooriv(self, other)

    def __rflooriv__(self, other):
        return FloorDiv(other, self)

    def __pow__(self, other):
        return Pow(self, other)

    def __rpow__(self, other):
        return Pow(other, self)

    def __mod__(self, other):
        return Mod(self, other)

    def __eq__(self, other):
        return Eq(self, other)

    def __ne__(self, other):
        return Ne(self, other)

    def __lt__(self, other):
        return Lt(self, other)

    def __le__(self, other):
        return Le(self, other)

    def __gt__(self, other):
        return Gt(self, other)

    def __ge__(self, other):
        return Ge(self, other)

    def __rmod__(self, other):
        return Mod(other, self)

    def __pos__(self):
        return Pos(self)

    def __neg__(self):
        return Neg(self)

    def __abs__(self):
        return Abs(self)

    def __not__(self):
        return Not(self)

class AttributeGetter(Expression):
    def __init__(self, attribute_name, symbol=None):
        self.attribute_name = attribute_name
        if symbol is None:
            symbol = attribute_name
        self.symbol = symbol
        self.instance = None

    def bind(self, instance):
        self.instance = instance

    def get_value(self):
        return getattr(self.instance, self.attribute_name)

    def __str__(self):
        return self.symbol

class ConstExpression(Expression):
    def __init__(self, const_value):
        self.const_value = const_value

    def get_value(self):
        return self.const_value

    def __str__(self):
        return str(self.const_value)

class BinaryOperator(Expression):
    __symbol__ = '?'
    def __init__(self, left_operand, right_operand):
        self.left_operand = self._coerce_operand(left_operand)
        self.right_operand = self._coerce_operand(right_operand)

    def bind(self, instance):
        self.left_operand.bind(instance)
        self.right_operand.bind(instance)

    def get_value(self):
        return self.compute(self.left_operand.get_value(), self.right_operand.get_value())

    @abc.abstractmethod
    def compute(self, l, r):
        pass

    def __str__(self):
        return "({l} {s} {r})".format(l=self.left_operand, s=self.__symbol__, r=self.right_operand)
    
class UnaryOperator(Expression):
    __symbol__ = '?'
    def __init__(self, operand):
        self.operand = self._coerce_operand(operand)

    def bind(self, instance):
        self.operand.bind(instance)

    def get_value(self):
        return self.compute(self.operand.get_value())

    @abc.abstractmethod
    def compute(self, o):
        pass

    def __str__(self):
        return "({s} {o})".format(s=self.__symbol__, o=self.operand)
    
class And(BinaryOperator):
    __symbol__ = "and"
    def compute(self, l, r):
        return l and r

class Or(BinaryOperator):
    __symbol__ = "or"
    def compute(self, l, r):
        return l or r

class Add(BinaryOperator):
    __symbol__ = "+"
    def compute(self, l, r):
        return l + r

class Mul(BinaryOperator):
    __symbol__ = "*"
    def compute(self, l, r):
        return l * r

class Sub(BinaryOperator):
    __symbol__ = "-"
    def compute(self, l, r):
        return l - r

class Div(BinaryOperator):
    __symbol__ = "/"
    def compute(self, l, r):
        return l / r

class TrueDiv(BinaryOperator):
    __symbol__ = "/"
    def compute(self, l, r):
        return l / r

class Flooriv(BinaryOperator):
    __symbol__ = "//"
    def compute(self, l, r):
        return l // r

class Pow(BinaryOperator):
    __symbol__ = "**"
    def compute(self, l, r):
        return l * r

class Mod(BinaryOperator):
    __symbol__ = "%"
    def compute(self, l, r):
        return l % r

class Eq(BinaryOperator):
    __symbol__ = "=="
    def compute(self, l, r):
        return l == r

class Ne(BinaryOperator):
    __symbol__ = "!="
    def compute(self, l, r):
        return l != r

class Lt(BinaryOperator):
    __symbol__ = "<"
    def compute(self, l, r):
        return l <  r

class Le(BinaryOperator):
    __symbol__ = "<="
    def compute(self, l, r):
        return l <= r

class Gt(BinaryOperator):
    __symbol__ = ">"
    def compute(self, l, r):
        return l >  r

class Ge(BinaryOperator):
    __symbol__ = ">="
    def compute(self, l, r):
        return l >= r

class Pos(UnaryOperator):
    __symbol__ = "+"
    def compute(self, o):
        return +o

class Abs(UnaryOperator):
    def compute(self, o):
        return +o

    def __str__(self):
        return "abs({0})".format(self.operand)

class Neg(UnaryOperator):
    __symbol__ = "-"
    def compute(self, o):
        return -o

class Not(UnaryOperator):
    __symbol__ = "not"
    def compute(self, o):
        return not o

if __name__ == "__main__":
    class MyClass(object):
        def __init__(self, a, b):
            self.alfa = a
            self.beta = b

    ALFA = AttributeGetter('alfa', 'ALFA')
    BETA = AttributeGetter('beta', 'BETA')

    e = (ALFA > 10) & (BETA < 3)
    print(e)

    x = MyClass(100, 100)
    y = MyClass(100, 0)
    z = MyClass(1, 1)
    e.bind(x)
    print(e.get_value())
    e.bind(y)
    print(e.get_value())
    e.bind(z)
    print(e.get_value())
