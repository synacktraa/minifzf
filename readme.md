<div align="center">
  <img src="https://github.com/synacktraa/minifzf/assets/91981716/8d4132dd-b873-4921-a2a2-2b2ede989a74" alt="MiniFzf GIF">
</div>

Lightweight and efficient Python library inspired by the powerful features of `fzf`, the popular command-line fuzzy finder. `minifzf` is designed to bring the essential functionalities of `fzf` into your Python CLI projects with ease and simplicity.

---

### Key Features:
- **Basic FZF Functionalities**: Incorporates the fundamental features of `fzf`, offering efficient and fast fuzzy finding and selection capabilities right in your command line.
- **Library Use**: Can be easily imported and used as a module in other Python projects, enhancing the interactive command-line interface experience.
- **Simplicity and Efficiency**: Stripped down to core features, ensuring a lightweight and straightforward user experience without the overhead of complex functionalities.

### Ideal Use Cases:
- Interactive data selection and navigation in Python CLI applications.
- Quick searching and filtering in command-line based tools or scripts.
- Enhancing existing Python projects with simple, efficient selection capabilities.
- Developers seeking a minimalistic yet powerful alternative to `fzf` for Python.

### Installation:

```bash
pip install minifzf
```

### CLI Usage:

```
$ mfzf --help

Usage: minifzf COMMAND [OPTIONS]

╭─ Commands ────────────────────────────────────────────╮
│ --help,-h     Display this message and exit.          │
│ --version,-v  Display application version.            │
╰───────────────────────────────────────────────────────╯
╭─ Parameters ──────────────────────────────────────────╮
│ --query  -q  Start the selector with the given query. │
│ --first  -1  Automatically select the only match.     │
╰───────────────────────────────────────────────────────╯
```

Start `minifzf` selection for current directory.

```bash
mfzf
```

With initial query.

```bash
minifzf -q "<Your Query>"
```

Returned most relevant item.

```bash
mfzf -q "<Your Query>" -1
```

Select from Standard Input.

> No UNIX support for now (Throws `[Errno 25] Inappropriate ioctl for device` because minifzf uses sshkeyboard which utilizes termios library.)
```bash
cat filename | minifzf
```

### Library Usage:

Initiating selector with headers and rows.

```python
from minifzf import Selector
from pathlib import Path

selector = Selector(
    headers=['files'],
    rows=[[str(p)] for p in Path.cwd().glob('*')])
selected = selector.select()
```

Initating selector with mappings.

```python
from minifzf import Selector

mappings = [
    {"id": "51009", "name": "Jujutsu Kaisen 2nd Season"},
    {"id": "40748", "name": "Jujutsu Kaisen"},
    {"id": "48561", "name": "Jujutsu Kaisen 0 Movie"}
]
selector = Selector.from_mappings(mappings=mappings)
selected = selector.select()
```

Initiating a path selector.

```python
from minifzf import Selector
from pathlib import Path

path_selector = Selector.as_path_selector(
    directory=Path('path/to/directory'), recursive=False)
selected = path_selector.select()
```

### Contribution and Feedback:
We welcome contributions and feedback to improve `minifzf`. If you have ideas, issues, or want to contribute, please feel free to open an issue or a pull request.
