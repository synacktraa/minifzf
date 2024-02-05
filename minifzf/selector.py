from pathlib import Path
from string import printable
from threading import Event, Thread
from typing import Mapping, Iterable, Optional

from rich import box
from rich.text import Text
from rich.live import Live
from rich.table import Table
from rich.layout import Layout
from rich.console import Console

from sshkeyboard import listen_keyboard, stop_listening

from . import _key, _style
from .search import iter_search_results


class Selector:
    def __init__(
        self, 
        rows: list[Iterable[str]], 
        headers: Optional[Iterable[str]] = None,
        query: str = None
    ):
        """
        Initiate a selector instance.
        :param rows: List of rows to select from.
        :param headers: Column headers. By default headers are not shown.
        :param query: Query to search rows for representing in the selector.
        
        .. code-block:: python
        from minifzf import Selector
        from pathlib import Path

        selector = Selector(
            headers=['files'], 
            rows=[[str(p)] for p in Path.cwd().glob('*')])
        selected = selector.select()
        """
        self._live = Live("", screen=True, auto_refresh=False)
        self._original_rows = rows
        self._inital_row_count = len(self._original_rows)
        self._rows = self.search_rows(query=query)
        self._no_row_height = 3
        self._headers = headers or []
        self._show_header = bool(headers)
        if self._show_header is True:
            self._no_row_height += 2
        self._query = query or ""
        if query:
            self._searching = True
            self._no_row_height += 1
        else:
            self._searching = False
        self._ptr = 0
        self._start_idx = 0
        self._end_idx = min(*self.rows_count(include_visible=True))
        self._selected = None

    @classmethod
    def from_mappings(cls, mappings: Iterable[Mapping[str, str]], query: str = None):
        """
        Initiate selector from mapped objects.
        :param mappings: An iterable of mapping/dictionary.
        :param query: Query to search rows for representing in the selector.

        .. code-block:: python
        from minifzf import Selector

        mappings = [
            {"id": "51009", "name": "Jujutsu Kaisen 2nd Season"},
            {"id": "40748", "name": "Jujutsu Kaisen"},
            {"id": "48561", "name": "Jujutsu Kaisen 0 Movie"}
        ]
        selector = Selector.from_mappings(mappings=mappings)
        selected = selector.select()
        """
        if not mappings:
            raise ValueError("Empty sequence, can't proceed further.")
        
        mapkeys = [list(m.keys()) for m in mappings]
        assert all(keys == mapkeys[0] for keys in mapkeys), \
            "Keys must be same for every mapping object."
        
        rows = [list(m.values()) for m in mappings]
        return cls(rows=rows, headers=mapkeys[0], query=query)
    
    @classmethod
    def as_path_selector(
        cls, 
        directory: Optional[Path] = None,
        only_files: bool = True, 
        only_dirs: bool = False,
        recursive: bool = True,
        query: str = None
    ):
        """
        Initiate a path selector instance.
        :param directory: Path to directory. [default: `Path.cwd()`]
        :param only_files: If true, only files are used for selection.
        :param only_dirs: If true, only directories are used for selection.
        :param recursive: If true, all paths are retrieved recursively for selection.
        :param query: Query to search rows for representing in the selector.

        .. code-block:: python
        from minifzf import Selector
        from pathlib import Path

        path_selector = Selector.as_path_selector(
            directory=Path('path/to/directory'), recursive=False)
        selected = path_selector.select()
        """
        if directory is None:
            directory = Path.cwd()
        else:
            if not directory.exists():
                raise LookupError(f"{str(directory)} doesn't exists.")
            if not directory.is_dir():
                raise NotADirectoryError(f"{str(directory)} is not a directory.")
        
        paths = list(directory.rglob('*') if recursive else directory.glob('*'))
        if only_files == only_dirs:
            rows = [(str(p),) for p in paths]
        elif only_files:
            rows = [(str(p),) for p in paths if p.is_file()]
        else:
            rows = [(str(p),) for p in paths if p.is_dir()]
        return cls(rows=rows, query=query)
    
    def rows_count(self, include_visible: bool = False):
        if self._searching is False:
            row_count = self._inital_row_count
        else:
            row_count = len(self._rows)
        
        if include_visible is False:
            return row_count
        
        console_h = self._live.console.height
        visibles = min(console_h - self._no_row_height, row_count)
        if visibles < console_h:
            return row_count, visibles
        return row_count, visibles - self._no_row_height

    def scroll_up(self):
        """Scroll up one step."""
        if self._ptr <= 0:
            return
        self._ptr -= 1
        if self._ptr >= self._start_idx:
            return
        self._start_idx = self._ptr
        row_cnt, visibles = self.rows_count(include_visible=True)
        self._end_idx = min(row_cnt, self._start_idx + visibles)

    def scroll_down(self):
        """Scroll down one step."""
        row_cnt, visibles = self.rows_count(include_visible=True)
        if self._ptr >= row_cnt - 1:
            return
        self._ptr += 1
        if self._ptr < self._end_idx:
            return
        self._end_idx = self._ptr + 1
        self._start_idx = max(0, self._end_idx - visibles)

    def search_rows(self, query: str):
        o_rows = self._original_rows
        if not query:
            return o_rows
        return [r for r in o_rows if any(iter_search_results(query, r))]

    def navigate(self, key: str):
        """Navigate based on given key."""
        if key == _key.UP:
            self.scroll_up()
        elif key in _key.DOWN:
            self.scroll_down()
        elif key in _key.ACTIVATE_SEARCH_KEYS:
            self._searching = True
            self._no_row_height += 1
            _, visibles = self.rows_count(include_visible=True)
            if self._end_idx > visibles:
                self._end_idx -= 1

    def __update_rows(self, key: str):
        """Update rows with new query."""
        key = _key.normalize(key=key)
        if key in (_key.UP, _key.DOWN):
            return self.navigate(key=key)
        
        if key == _key.BACKSPACE:
            self._query = self._query[:-1]
        elif key == _key.ESC:
            self._searching = False
            self._no_row_height -= 1
            self._query = ""
        elif key in printable:
            self._query += key

        self._rows = self.search_rows(query=self._query)
        self._ptr, self._start_idx = 0, 0
        self._end_idx = min(*self.rows_count(include_visible=True))

    def construct_table(self) -> Table:
        """Construct new table."""
        table = Table(
            box=box.ROUNDED, 
            show_header=self._show_header, 
            width=self._live.console.width)
        
        for h in self._headers:
            table.add_column(h)

        for i, row in enumerate(self._rows[self._start_idx:self._end_idx]):
            is_selected = self._start_idx + i == self._ptr
            _row = [Text.from_ansi(str(e)) for e in row]
            table.add_row(
                *_row, style=_style.SELECTED_STYLE if is_selected else None)

        return table

    def construct_layout(self) -> Layout:
        """Construct new layout."""
        layout = Layout()
        row_count = Layout(Text(
            f'{self.rows_count()}/{self._inital_row_count}', 
            style=_style.COUNT_STYLE), size=1)
        table = Layout(self.construct_table())
        
        if self._searching is False:
            layout.split(table, row_count)
            return layout
        
        search_display = Text(f"> {self._query}", style=_style.SEARCH_STYLE)
        layout.split(
            table, row_count, Layout(search_display, size=1))
        return layout

    @property
    def current_value(self):
        """Get value at current pointer."""
        value = self._rows[self._ptr] if self._rows else None
        if value is None:
            return
        value = list(value)
        if len(value) == 1:
            return value[0]
        if self._headers:
            return dict(zip(self._headers, value))
        return value

    def refresh(self):
        """Refresh live console."""
        self._live.update(self.construct_layout(), refresh=True)

    def exit(self, msg: str = ""):
        """Exit the live console."""
        self._live.stop()
        self._live.console.clear()
        if msg:
            self._live.console.print(msg)
        stop_listening()
    
    def __update_idxs_after_resize(self):
        row_cnt, visibles = self.rows_count(include_visible=True)
        self._start_idx = max(0, min(self._ptr, row_cnt - visibles))
        self._end_idx = min(row_cnt, self._start_idx + visibles)
        self._ptr = min(max(self._ptr, self._start_idx), self._end_idx - 1)

    def resize(self, stop_event: Event):
        """
        Resize callback for continuously adapting to changing environment.
        """
        curr_size = self._live.console.size
        while not stop_event.is_set():
            if stop_event.wait(timeout=0.5):
                break
            new_size = Console().size
            if new_size == curr_size:
                continue
            curr_size = new_size
            self.__update_idxs_after_resize()
            self.refresh()        

    def sendkey(self, key: str):
        """Send key to live console."""
        if key == _key.ENTER:
            self._selected = self.current_value
            self.exit(str(self._selected or ""))
        elif self._searching is True:
            self.__update_rows(key=key)
        elif self._searching is False:
            if key in (_key.ESC, 'q'):
                self.exit()
            self.navigate(key=key)
        self.refresh()

    def select(self):
        """Start the live console and return selected item."""
        resize_check_stop_event = Event()
        resize_cb_thread = Thread(
            target=self.resize, kwargs={'stop_event': resize_check_stop_event}, daemon=True)
        try:
            self._live.start()
            self.refresh()
            resize_cb_thread.start()
            listen_keyboard(
                on_press=self.sendkey, until=None, delay_other_chars=0, delay_second_char=0, lower=False)
        except KeyboardInterrupt:
            self.exit()
        finally:
            resize_check_stop_event.set()
            resize_cb_thread.join()

        return self._selected