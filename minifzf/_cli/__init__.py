import sys
from typing import Annotated
from cyclopts import App, Parameter

try:
    from ..selector import Selector
except ImportError:
    from minifzf.selector import Selector


def __version__() -> str:
    import importlib.metadata

    try:
        return importlib.metadata.version("minifzf")
    except importlib.metadata.PackageNotFoundError:
        import re, pathlib

        return re.search(
            r'name = "minifzf"\nversion = "(.+?)"',
            (pathlib.Path(__file__).parent.parent / "pyproject.toml").read_text(),
        ).group(1)

app = App(
    name="minifzf", 
    version=__version__(), 
    version_flags=['-v', '--version'], 
    # help="Fast and minimal fuzzy finder."
)

def read_stdin(readlines: bool = False):
    """Read values from standard input (stdin). """
    if sys.stdin.isatty():
        return
    try:
        if readlines is False:
            return sys.stdin.read().rstrip('\n')
        return [_.strip('\n') for _ in sys.stdin if _]
    except KeyboardInterrupt:
        return

@app.default
def __entry__(
    *,
    query: Annotated[str, Parameter(
        name=("-q", "--query"), help="Start the selector with the given query.")] = None,
    first: Annotated[bool, Parameter(
        name=("-1", "--first"), help="Automatically select the only match.", negative="", show_default=False)] = False
    ):
    if sys.stdin.isatty():
        selector = Selector.as_path_selector(query=query)
    else:
        selector = Selector(
            rows=[(_.strip('\n'),) for _ in sys.stdin if _], query=query)
        
    if first:
        print(selector.current_value or "")
        return
    
    _ = selector.select()
    

        

