import numpy as np

from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.function_quibs.cache.shallow.nd_cache.nd_indexable_cache import NdIndexableCache
from pyquibbler.quib.function_quibs.utils import create_empty_array_with_values_at_indices


class NdFieldArrayShallowCache(NdIndexableCache):
    """
    A cache for any ndarray which has dtype names (ie a "field array")
    """

    SUPPORTING_TYPES = (np.ndarray,)

    @classmethod
    def supports_result(cls, result):
        return super(NdFieldArrayShallowCache, cls).supports_result(result) and result.dtype.names is not None

    @classmethod
    def create_from_result(cls, result):
        mask = np.full(result.shape, True, dtype=[(name, np.bool_) for name in result.dtype.names])
        return cls(result, True, mask)

    def _create_paths_for_indices(self, indices):
        boolean_mask_of_indices = create_empty_array_with_values_at_indices(
            self._value.shape,
            indices=indices,
            value=True,
            empty_value=False
        )

        return [
            [PathComponent(indexed_cls=np.ndarray, component=name),
             PathComponent(indexed_cls=np.ndarray, component=np.logical_and(
                 boolean_mask_of_indices,
                 self._invalid_mask[name]
             ))]
            for name in self._invalid_mask.dtype.names
        ]

    def _get_uncached_paths_at_path_component(self,
                                              path_component):
        paths = super(NdFieldArrayShallowCache, self)._get_uncached_paths_at_path_component(path_component)
        if paths:
            return paths

        if path_component.references_field_in_field_array():
            paths = [[PathComponent(indexed_cls=np.ndarray, component=path_component.component),
                      PathComponent(indexed_cls=np.ndarray, component=self._invalid_mask[path_component.component])]]
        else:
            paths = self._create_paths_for_indices(path_component.component)

        return self._filter_empty_paths(paths)

    def _is_completely_invalid(self):
        return super(NdFieldArrayShallowCache, self)._is_completely_invalid() \
               or all(np.all(self._invalid_mask[name]) for name in self._invalid_mask.dtype.names)
