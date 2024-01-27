ENTER = 'enter'
ESC = 'esc'
SPACE = 'space'
BACKSPACE = 'backspace'
UP = 'up'
DOWN = 'down'
ACTIVATE_SEARCH_KEYS = ('/', 'f')

READABLE_TO_CHAR = {
    "tab": "\t",
    "enter": "\n",
    "enter": "\r",
    "space": " ",
}

def normalize(key: str):
    return READABLE_TO_CHAR.get(key, key)