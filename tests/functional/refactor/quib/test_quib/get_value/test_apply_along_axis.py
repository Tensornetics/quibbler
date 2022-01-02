import itertools

from pyquibbler import iquib
from pyquibbler.env import GRAPHICS_EVALUATE_NOW
from pyquibbler.quib import PathComponent
from pyquibbler.quib.assignment.utils import deep_get
from pyquibbler.refactor.quib.quib import Quib
from tests.functional.quib.utils import get_func_mock
from tests.functional.refactor.quib.test_quib.get_value.utils import check_get_value_valid_at_path
import numpy as np
import pytest


# A 3d array in which every dimension has a different size
parametrize_data = pytest.mark.parametrize('data', [np.arange(24).reshape((2, 3, 4))])
parametrize_indices_to_invalidate = pytest.mark.parametrize('indices_to_invalidate',
                                                     [-1, 0, (0, 0), (0, 1, 2), (0, ...), [True, False]])
parametrize_keepdims = pytest.mark.parametrize('keepdims', [True, False, None])
parametrize_where = pytest.mark.parametrize('where', [True, False, [[[True], [False], [True]]], None])


@parametrize_data
@pytest.mark.parametrize('axis', [0, 1, 2, -1, -2])
@pytest.mark.parametrize('func_out_dims', [0, 1, 2])
@pytest.mark.parametrize('indices_to_get_value_at', [0, (0, 0), (-1, ...)])
def test_apply_along_axis_get_value_valid_at_path(indices_to_get_value_at, axis, func_out_dims, data):
    func1d = lambda slice: np.sum(slice).reshape((1,) * func_out_dims)
    path_to_get_value_at = [PathComponent(np.ndarray, indices_to_get_value_at)]

    check_get_value_valid_at_path(lambda quib: np.apply_along_axis(func1d, axis, quib), data, path_to_get_value_at)


def create_lazy_apply_along_axis_quib(func, arr, axis, args=None, kwargs=None, call_func_with_quibs=False):
    with GRAPHICS_EVALUATE_NOW.temporary_set(True):
        return np.apply_along_axis(func, axis, iquib(arr) if not isinstance(arr, Quib) else arr,
                                   *(args or []), **(kwargs or {}), call_func_with_quibs=call_func_with_quibs)


@pytest.mark.parametrize('shape, axis, func1d_res', [
        (tuple(dimensions), axis, res)
        for shape_size in range(1, 3)
        for axis in range(-shape_size, shape_size)
        for dimensions in itertools.product(*[range(1, 4) for _ in range(shape_size)])
        for res in [1, np.arange(9).reshape((3, 3)), None]
])
@pytest.mark.parametrize('pass_quibs', [True, False])
def test_apply_along_axis_get_shape(shape, axis, func1d_res, pass_quibs):
    func = get_func_mock(lambda x: func1d_res)
    arr = np.arange(np.prod(shape)).reshape(shape)
    quib = create_lazy_apply_along_axis_quib(func=func, arr=arr, axis=axis, call_func_with_quibs=pass_quibs)
    expected_input_arr = arr[tuple([slice(None) if i == quib._function_runner.core_axis else 0 for i in range(len(arr.shape))])]

    res = quib.get_shape()

    assert func.call_count == 1
    call = func.mock_calls[0]
    oned_slice = call.args[0]
    if pass_quibs:
        assert isinstance(oned_slice, Quib)
        oned_slice = oned_slice.get_value()
    else:
        assert not isinstance(oned_slice, Quib)
    assert np.array_equal(oned_slice, expected_input_arr)
    assert res == np.apply_along_axis(func, axis=axis, arr=arr).shape


def get_sample_indexing_paths(input_shape, apply_shape, axis):
    res = np.apply_along_axis(func1d=lambda _: np.zeros(apply_shape), arr=np.zeros(input_shape), axis=axis)

    paths = [[()], []]

    if len(res.shape) > 0:
        paths.append([np.array([0 for _ in res.shape])])

    if len(res.shape) > 1:
        paths.append([(0, np.arange(res.shape[1]))])
        paths.append([(0, res.shape[1] - 1)])
    return paths


def assert_all_apply_calls_with_slices_were_relevant(func, axis, input_arr, path, applied_slices):
    whole_result = np.apply_along_axis(func, axis=axis, arr=input_arr)
    current_result = deep_get(whole_result, path)

    for slice_ in applied_slices:
        for num in np.ravel(slice_):
            new_arr = np.array(input_arr)
            new_arr[new_arr == num] = 999
            new_result = np.apply_along_axis(func, axis=axis, arr=new_arr)
            new_result_at_path = deep_get(new_result, path)
            assert not np.array_equal(new_result_at_path, current_result )


@pytest.mark.parametrize('input_shape, apply_result_shape, axis, components', [
        (tuple(input_dimensions), tuple(apply_dimensions), axis, components)
        for input_shape_size in range(0, 3)
        for axis in range(-input_shape_size, input_shape_size)
        for apply_result_shape_size in range(0, 3)
        for input_dimensions in itertools.product(*[range(1, 3) for _ in range(input_shape_size)])
        for apply_dimensions in [[], *itertools.product(*[range(1, 3) for _ in range(apply_result_shape_size)])]
        for components in get_sample_indexing_paths(tuple(input_dimensions), tuple(apply_dimensions), axis)
])
@pytest.mark.parametrize('pass_quibs', [True, False])
def test_apply_along_axis_get_value(input_shape, apply_result_shape, axis, components, pass_quibs):
    assert len(components) <= 1, "Sanity: No support for testing multiple components (also irrelevant)"
    slices = []
    running_in_quib = False

    def apply(oned_slice):
        if running_in_quib:
            if pass_quibs:
                assert isinstance(oned_slice, Quib)
                oned_slice = oned_slice.get_value()
            else:
                assert not isinstance(oned_slice, Quib)

            slices.append(oned_slice)
        return np.full(apply_result_shape, np.sum(oned_slice))

    func = get_func_mock(apply)
    arr = np.arange(np.prod(input_shape)).reshape(input_shape)
    quib = create_lazy_apply_along_axis_quib(arr=arr, func=func, axis=axis, call_func_with_quibs=pass_quibs)
    quib.get_shape()  # We need to call get_shape to cache it as get_shape is a zero cost operation in overall scheme
    # and is allowed to be called without consequence by the quib
    path = [PathComponent(component=component, indexed_cls=np.ndarray) for component in components]
    running_in_quib = True

    res = quib.get_value_valid_at_path(path)

    running_in_quib = False
    whole_apply_axis_result = np.apply_along_axis(func, axis=axis, arr=arr)
    expected_result = deep_get(whole_apply_axis_result, path)
    res_at_components = deep_get(res, path)
    assert np.array_equal(res_at_components, expected_result)
    assert_all_apply_calls_with_slices_were_relevant(
        func=func,
        axis=axis,
        input_arr=arr,
        applied_slices=slices,
        path=path
    )