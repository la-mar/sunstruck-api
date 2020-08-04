import hashlib
import itertools
import logging
from collections import OrderedDict
from typing import Any, Generator, Iterable, List, Mapping, Type, Union

logger = logging.getLogger(__name__)


def make_hash(data: Union[List, OrderedDict]) -> str:
    return hashlib.md5(str(data).encode()).hexdigest()


def ensure_list(value: Any) -> List[Any]:
    """ Convert or unpack any iterable into a list, with the exception of mappings.
        If the passed value is either a mapping or not an iterable, it is returned
        wrapped in a list.

        Example:
        >>> iterable = [1,2,3]
        >>> ensure_iterable(iterable)
        >>> [1,2,3]

        >>> mapping = {"a": 1, "b": 2}
        >>> ensure_iterable(mapping)
        >>> [{"a": 1, "b": 2}]

        >>> scalar = "hello world!"
        >>> ensure_iterable(scalar)
        >>> ["hello world!"]

        """

    if isinstance(value, (Mapping, str)):  # do not unpack dictionaries
        return [value]
    elif isinstance(value, Iterable):
        return list(value)
    else:
        return [value]


def reduce(values: Iterable) -> Union[Iterable, Any]:
    """ Reduce an iterable to a scalar if length is 1. Returns None if iterable
        is empty. """

    try:
        while isinstance(values, Iterable) and not isinstance(values, (Mapping, str)):
            values = list(values)
            if len(values) <= 1:
                values = values[0]
            else:
                break

        return values

    except IndexError:
        return None


def chunks(iterable: Iterable, n: int = 1000, cls: Type = list) -> Generator:
    """ Slice and unpack a nested iterable into a flat iterable containing a
        maximum of n elements.

    Arguments:
        iterable {Iterable} -- items to process

    Keyword Arguments:
        n {int} -- max number of elements per chunk (default: 1000)
        cls {Type} -- iterable type in which to cast chunks (default: list)

    Yields:
        Generator -- generator of iterables
    """

    it = iter(iterable)
    while True:
        chunked = itertools.islice(it, n)
        try:
            first_element = next(chunked)
        except StopIteration:
            return
        yield cls(itertools.chain((first_element,), chunked))
