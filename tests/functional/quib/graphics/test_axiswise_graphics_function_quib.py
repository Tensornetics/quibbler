import numpy as np
from pytest import mark

from pyquibbler import iquib

from ..utils import check_invalidation

# A 3d array in which every dimension has a different size
parametrize_data = mark.parametrize('data', [np.arange(24).reshape((2, 3, 4))])
parametrize_indices = mark.parametrize('indices_to_invalidate', [-1, 0, (0, 0), (0, 1, 2), (0, ...), [True, False]])


@parametrize_indices
@parametrize_data
@mark.parametrize('axis', [-1, (-1, 1), 0, 1, 2, (0, 2), (0, 1), None])
@mark.parametrize('keepdims', [True, False, None])
@mark.parametrize('where', [True, False, [[[True], [False], [True]]], None])
def test_reduction_axiswise_invalidation(indices_to_invalidate, axis, keepdims, where, data):
    kwargs = dict(axis=axis)
    if keepdims is not None:
        kwargs['keepdims'] = keepdims
    if where is not None:
        kwargs['where'] = where
    check_invalidation(lambda iq: np.sum(iq, **kwargs), data, indices_to_invalidate)


@parametrize_indices
@parametrize_data
@mark.parametrize('axis', [0, 1, 2, -1, -2])
@mark.parametrize('func_out_dims', [0, 1, 2])
def test_apply_along_axis_invalidation(indices_to_invalidate, axis, func_out_dims, data):
    func1d = lambda slice: np.sum(slice).reshape((1,) * func_out_dims)
    check_invalidation(lambda iq: np.apply_along_axis(func1d, axis, iq), data, indices_to_invalidate)


@parametrize_indices
@parametrize_data
@mark.parametrize('excluded', [{0}, set(), None])
@mark.parametrize('func', [lambda x: np.sum(x), ])
# lambda x: (np.sum(x), np.sum(x))])
def test_vectorize_invalidation(indices_to_invalidate, data, excluded, func):
    kwargs = {}
    if excluded is not None:
        kwargs['excluded'] = excluded
    check_invalidation(lambda iq: np.vectorize(func, **kwargs)(iq), data, indices_to_invalidate)


def test_vectorize_invalidation_with_non_numpy_func():
    vec = np.vectorize(lambda a: int(np.sum(a)), signature='(a)->()')
    check_invalidation(lambda iq: vec(iq), [1, 2, 3], 0)


@parametrize_indices
@parametrize_data
def test_vectorize_invalidation_with_multiple_params(data, indices_to_invalidate):
    quib_arg = iquib(np.arange(12).reshape((3, 4)))
    non_quib_arg = np.arange(8).reshape((2, 1, 4))
    quib_kwarg = iquib(3)
    non_quib_kwarg = np.arange(3).reshape((3, 1))

    vec = np.vectorize(lambda a, b, c, d, e=0: a + b + c + d + e)
    check_invalidation(lambda iq: vec(iq, quib_arg, non_quib_arg, d=quib_kwarg, e=non_quib_kwarg),
                       data, indices_to_invalidate)


@mark.parametrize('excluded', [{1}, {'b'}, set(), None])
def test_vectorize_invalidation_with_quib_as_kwarg(excluded):
    kwargs = {}
    if excluded is not None:
        kwargs['excluded'] = excluded
    vec = np.vectorize(lambda a, b: a + b)
    check_invalidation(lambda iq: vec(5, b=iq), [1, 2, 3], 0)


@parametrize_indices
@parametrize_data
def test_vectorize_invalidation_with_different_core_dims(data, indices_to_invalidate):
    data2 = np.arange(100, 122).reshape(1, 22)
    func = lambda a, b: (np.array([np.sum(a) + np.sum(b)] * 4), np.sum(a) + np.sum(b))
    vec = np.vectorize(func, signature='(a,b),(c)->(d),()')
    check_invalidation(lambda iq: vec(iq, data2), data, indices_to_invalidate)
