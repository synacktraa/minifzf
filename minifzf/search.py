import regex
from typing import Iterable, Optional, Callable, TypeVar


search_type = TypeVar("search_type")

def iter_search_results(
    query: str,
    possibilities: Iterable[search_type],
    *,
    processor: Optional[Callable[[search_type], str]] = None,
):
    """
    Powerful searching function that uses regex building
    for matching the query with the possibilities.
    Yoinked from github.com/justfoolingaround/animdl

    :param query: The query to search for.
    :param possibilities: The possibilities to search in.
    :param processor: A function that processes the possibilities.

    :return: A generator that yields the search results.
    """
    
    pattern = regex.compile(
        r"(.*?)".join(map(regex.escape, query.strip())),
        flags=regex.IGNORECASE)

    for search_value in possibilities:
        if processor is not None:
            processed_value = str(processor(search_value))
        else:
            processed_value = str(search_value)

        if query in processed_value or pattern.search(processed_value):
            yield processed_value