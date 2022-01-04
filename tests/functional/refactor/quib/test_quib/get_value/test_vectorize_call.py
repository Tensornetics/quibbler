import functools
from unittest import mock

import numpy as np
import pytest
from matplotlib import pyplot as plt

from pyquibbler import CacheBehavior, iquib
from pyquibbler.env import GRAPHICS_EVALUATE_NOW
from pyquibbler.quib import PathComponent
from tests.functional.quib.utils import PathBuilder, get_func_mock
from tests.functional.refactor.quib.test_quib.get_value.test_apply_along_axis import parametrize_data
from tests.functional.refactor.quib.test_quib.get_value.utils import check_get_value_valid_at_path, collecting_quib


@parametrize_data
@pytest.mark.parametrize('func', [lambda x: np.sum(x)])
@pytest.mark.parametrize('indices_to_get_value_at', [0, (0, 0), (-1, ...)])
def test_vectorize_get_value_valid_at_path(data, func, indices_to_get_value_at):
    path_to_get_value_at = [PathComponent(np.ndarray, indices_to_get_value_at)]
    check_get_value_valid_at_path(np.vectorize(func), data, path_to_get_value_at)


@pytest.mark.parametrize('pass_quibs', [True, False])
def test_vectorize_get_value_valid_at_path_with_excluded_quib(pass_quibs):
    excluded = collecting_quib(np.array([1, 2, 3]))

    @functools.partial(np.vectorize, excluded={1}, signature='(n)->(m)', pass_quibs=pass_quibs)
    def func(_a, b):
        if pass_quibs:
            # TODO: proxy_quib
           # assert isinstance(b, ProxyQuib) and b._quib is excluded
            assert b is excluded
        return b

    fquib = func([0, 1], excluded)
    fquib.set_cache_behavior(CacheBehavior.OFF)
    path = PathBuilder(fquib)[0].path

    with excluded.collect_valid_paths() as valid_paths:
        fquib.get_value_valid_at_path(path)

    assert valid_paths == [[]]


@pytest.mark.parametrize(['quib_data', 'non_quib_data'], [
    (np.zeros((2, 3)), np.zeros((4, 2, 3))),
    (np.zeros((3, 3)), np.zeros((1, 3))),
    (np.zeros((1, 3, 3)), np.zeros((4, 1, 3))),
    (np.zeros((4, 2, 3)), np.zeros((2, 3))),
])
def test_vectorize_get_value_valid_at_path_when_args_have_different_loop_dimensions(quib_data, non_quib_data):
    func = lambda quib: np.vectorize(lambda x, y: x + y)(quib, quib_data)
    check_get_value_valid_at_path(func, non_quib_data, [PathComponent(np.ndarray, 0)])


@pytest.mark.parametrize('indices_to_get_value_at', [0, (1, 1), (1, ..., 2)])
def test_vectorize_get_value_at_path_with_core_dims(indices_to_get_value_at):
    quib_data = np.zeros((2, 2, 3, 4))
    non_quib_data = np.zeros((2, 3, 4, 5))
    func = lambda a, b: np.array([np.sum(a) + np.sum(b)] * 6)
    vec = np.vectorize(func, signature='(a,b),(c)->(d)')
    check_get_value_valid_at_path(lambda quib: vec(non_quib_data, quib), quib_data,
                                  [PathComponent(np.ndarray, indices_to_get_value_at)])


def test_vectorize_partial_calculation():
    def f(x):
        return x

    func_mock = get_func_mock(f)
    with GRAPHICS_EVALUATE_NOW.temporary_set(True):
        quib = np.vectorize(func_mock)(iquib(np.arange(3)))
    # Should call func_mock twice
    quib.get_value_valid_at_path(PathBuilder(quib)[0].path)
    assert func_mock.call_count == 2, func_mock.mock_calls
    # Should call func_mock one time
    quib.get_value_valid_at_path(PathBuilder(quib)[1].path)
    assert func_mock.call_count == 3, func_mock.mock_calls[2:]
    # Should not call func_mock
    quib.get_value_valid_at_path(PathBuilder(quib)[0].path)
    assert func_mock.call_count == 3, func_mock.mock_calls[3:]


def test_vectorize_get_value_valid_at_path_none():
    quib = np.vectorize(lambda x: x)(iquib([1, 2, 3]))

    value = quib.get_value_valid_at_path(None)

    assert len(value) == 3


def test_vectorize_with_pass_quibs():
    @functools.partial(np.vectorize, pass_quibs=True)
    def vectorized(x):
        return iquib(x.get_value() + 1)

    result = vectorized(iquib(np.arange(2)))
    assert np.array_equal(result.get_value(), [1, 2])


def test_vectorize_with_pass_quibs_and_core_dims():
    @functools.partial(np.vectorize, pass_quibs=True, signature='(a)->(x)')
    def vectorized(x):
        return iquib(x.get_value() + 1)[:-1]

    result = vectorized(iquib(np.zeros((2, 3))))
    assert np.array_equal(result.get_value(), np.ones((2, 2)))


def test_lazy_vectorize():
    func_mock = mock.Mock(return_value=5)
    parent = iquib([0, 1, 2, 3])
    reference_to_vectorize = np.vectorize(func_mock, update_type="never")(parent)
    func_mock.assert_not_called()

    parent[0] = 100
    parent[1] = 101
    parent[2] = 102
    func_mock.assert_called_once()


def test_vectorize_doesnt_evaluate_sample_when_getting_value():
    func_mock = mock.Mock(return_value=5)
    parent = iquib([0, 1, 2])
    result = np.vectorize(func_mock, otypes=[np.int32])(parent)

    result[1].get_value()

    func_mock.assert_called_once_with(1)


def test_vectorize_with_data_with_zero_dims():
    data = iquib(np.array(np.zeros((3, 0, 2))))
    mock_func = mock.Mock()

    result = np.vectorize(mock_func, otypes=[np.int32])(data).get_value()

    assert np.array_equal(result, np.empty((3, 0, 2), dtype=np.int32))
    mock_func.assert_not_called()