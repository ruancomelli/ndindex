"""
Tests are extremely important for ndindex. All operations should produce
correct results. We test this by checking against numpy arange (the array
values do not matter, so long as they are distinct).

There are two primary types of tests that we employ to verify this

- Exhaustive tests. These test every possible value in some range. See for
  example test_slice. This is the best type of test, but unfortunately, it is
  often impossible to do due to combinatorial explosion.

- Hypothesis tests. Hypothesis is a library that can intelligently check a
  combinatorial search space. This requires writing hypothesis strategies that
  can generate all the relevant types of indices (see helpers.py). For more
  information on hypothesis, see
  https://hypothesis.readthedocs.io/en/latest/index.html.

The basic idea in both cases is the same. Take the pure index and the
ndindex(index).raw, or in the case of a transformation, the before and after
raw index, and index an arange with them. If they do not give the same output
array, or do not both produce the same error, the code is not correct.

"""

from itertools import chain, product
from functools import reduce
from operator import mul

from numpy import arange

from hypothesis import given
from hypothesis.strategies import integers, lists, one_of

from .helpers import check_same, ints, slices, tuples

def _iterslice(start_range=(-10, 10), stop_range=(-10, 10), step_range=(-10, 10)):
    for start in chain(range(*start_range), [None]):
        for stop in chain(range(*stop_range), [None]):
            for step in chain(range(*step_range), [None]):
                yield (start, stop, step)

def test_slice():
    a = arange(100)
    for start, stop, step in _iterslice():
        check_same(a, slice(start, stop, step))

@given(slices(), integers(5, 100))
def test_slice_hypothesis(s, size):
    a = arange(size)
    check_same(a, s)

def test_integer():
    a = arange(10)
    for i in range(-12, 12):
        check_same(a, i)

@given(ints(), integers(5, 100))
def test_integer_hypothesis(idx, size):
    a = arange(size)
    check_same(a, idx)

def test_tuple():
    # Exhaustive tests here have to be very limited because of combinatorial
    # explosion.
    a = arange(2*2*2).reshape((2, 2, 2))
    types = {
        slice: lambda: _iterslice((-1, 1), (-1, 1), (-1, 1)),
        # slice: _iterslice,
        int: lambda: ((i,) for i in range(-3, 3)),
    }

    for t1, t2, t3 in product(types, repeat=3):
        for t1_args in types[t1]():
            for t2_args in types[t2]():
                for t3_args in types[t3]():
                    idx1 = t1(*t1_args)
                    idx2 = t2(*t2_args)
                    idx3 = t3(*t3_args)

                    index = idx1, idx2, idx3
                    # Disable the same exception check because there could be
                    # multiple invalid indices in the tuple, and for instance
                    # numpy may give an IndexError but we would give a
                    # TypeError because we check the type first.
                    check_same(a, index, same_exception=False)

# np.prod has overflow and math.prod is Python 3.8+ only
def prod(seq):
    return reduce(mul, seq, 1)

@given(tuples(one_of(ints(), slices())),
       lists(integers(0, 10)).filter(
           # numpy gives errors with empty arrays with large shapes.
           # See https://github.com/numpy/numpy/issues/15753
           lambda shape: prod([i for i in shape if i]) < 100000))
def test_tuples_hypothesis(idx, shape):
    a = arange(prod(shape)).reshape(shape)
    check_same(a, idx, same_exception=False)
