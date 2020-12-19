import logging
import itertools as it
from typing import (
    Any,
    Dict,
    Iterable,
    Iterator,
    List,
    MutableSet,
    Optional,
    Sequence,
    Set,
    TypeVar,
    Union,
    overload,
)
log = logging.getLogger(__name__)

SLICE_ALL = slice(None)

T = TypeVar("T")


def _is_atomic(obj: Any) -> bool:
    return isinstance(obj, str) or isinstance(obj, tuple)


class OrderedSet(MutableSet[T], Sequence[T]):
    def __init__(self, iterable: Optional[Iterable[T]] = None):
        self.items = []  # type: List[T]
        self.map = {}  # type: Dict[T, int]
        if iterable is not None:
            self |= iterable

    def __len__(self):
        return len(self.items)

    @overload
    def __getitem__(self, index: Sequence[int]) -> List[T]:
        ...

    @overload
    def __getitem__(self, index: slice) -> "OrderedSet[T]":
        ...

    def __getitem__(self, index: int) -> T:
        if isinstance(index, slice) and index == SLICE_ALL:
            return self.copy()
        elif isinstance(index, Iterable):
            return [self.items[i] for i in index]
        elif isinstance(index, slice) or hasattr(index, "__index__"):
            result = self.items[index]
            if isinstance(result, list):
                return self.__class__(result)
            else:
                return result
        else:
            raise TypeError(
                "Don't know how to index an OrderedSet by %r" % index)

    def copy(self) -> "OrderedSet[T]":
        return self.__class__(self)

    def __getstate__(self):
        if len(self) == 0:
            return (None,)
        else:
            return list(self)

    def __setstate__(self, state):
        if state == (None,):
            self.__init__([])
        else:
            self.__init__(state)

    def __contains__(self, key: Any) -> bool:
        return key in self.map

    def add(self, key: T, index: Optional[int] = None) -> int:
        if key not in self.map:
            if index is None:
                self.map[key] = len(self.items)
                self.items.append(key)
            else:
                self.map[key] = index
                for k, v in self.map.items():
                    if v >= index:
                        self.map[k] = v+1
                self.items.insert(index, key)
        return self.map[key]

    def extend(self, keys: Iterable[T], index: Optional[int] = None):
        if index is None:
            len_ = len(self.items)
            for key in keys:
                if key not in self.map:
                    self.map[key] = len_
                    self.items.append(key)
                    len_ += 1
        else:
            c = 0
            for key in keys:
                if key not in self.map:
                    self.map[key] = index + c
                    self.items.insert(index + c, key)
                    c += 1
            if c:
                for k, v in self.map.items():
                    if v >= index + c:
                        self.map[k] = v+c

        # keys = filter(lambda key: key not in self.map, keys)
        # if index is None:
        #     self.map.update(
        #         {(key, i) for key, i in zip(keys, it.count(len(self.items)))}
        #     )
        #     self.items.extend(keys)
        # else:
        #     self.map.update(
        #         {(key, i) for key, i in zip(keys, it.count(index))}
        #     )
        #     for k, v in self.map.items():
        #         if v >= index:
        #             self.map[k] = v + len(keys)
        #     print(self.map)
        #     self.items[index:index] = keys

    def raw_add(self, key: T, index: Optional[int] = None) -> None:
        if index is None:
            self.map[key] = len(self.items)
            self.items.append(key)
        else:
            self.map[key] = index
            for k, v in self.map.items():
                if v >= index:
                    self.map[k] = v+1
            self.items.insert(index, key)

    append = add

    def update(self, sequence: Union[Sequence[T], Set[T]]) -> int:
        item_index = 0
        try:
            for item in sequence:
                item_index = self.add(item)
        except TypeError:
            raise ValueError(
                "Argument needs to be an iterable, got %s" % type(sequence)
            )
        return item_index

    @overload
    def index(self, key: T) -> int:
        ...

    def index(self, key: Sequence[T]) -> List[int]:
        if isinstance(key, Iterable) and not _is_atomic(key):
            return [self.index(subkey) for subkey in key]
        return self.map[key]

    # Provide some compatibility with pd.Index
    get_loc = index
    get_indexer = index

    def last(self) -> T:
        if self.items:
            return self.items[-1]

    def remove(self, from_: int, count: int = 1) -> None:
        if from_ >= len(self.items):
            raise IndexError("Out of range")
        if from_ + count >= len(self.items):
            count = len(self.items) - from_
        for elem in self.items[from_:from_+count]:
            del self.map[elem]
        del self.items[from_:from_+count]
        for k, v in self.map.items():
            if v >= from_:
                self.map[k] = v - count

    def pop(self) -> T:
        if not self.items:
            raise IndexError("Set is empty")

        elem = self.items[-1]
        del self.items[-1]
        del self.map[elem]
        return elem

    def discard(self, key: T) -> None:
        if key in self:
            i = self.map[key]
            del self.items[i]
            del self.map[key]
            for k, v in self.map.items():
                if v >= i:
                    self.map[k] = v - 1

    def clear(self) -> None:
        del self.items[:]
        self.map.clear()

    def __iter__(self) -> Iterator[T]:
        return iter(self.items)

    def __reversed__(self) -> Iterator[T]:
        return reversed(self.items)

    def __repr__(self) -> str:
        if not self:
            return "%s()" % (self.__class__.__name__,)
        return "%s(%r)" % (self.__class__.__name__, list(self))

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Sequence):
            return list(self) == list(other)
        try:
            other_as_set = set(other)
        except TypeError:
            return False
        else:
            return set(self) == other_as_set

    def union(self, *sets: Union[Sequence[T], Set[T]]) -> "OrderedSet[T]":
        cls = self.__class__ if isinstance(self, OrderedSet) else OrderedSet
        containers = map(list, it.chain([self], sets))
        items = it.chain.from_iterable(containers)
        return cls(items)
