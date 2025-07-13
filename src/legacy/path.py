import os
from pathlib import Path

DIR = Path(__file__).parent

DIR_OUTPUT = os.path.normpath(os.path.join(DIR, "../outputs/"))
DIR_TEMP = os.path.normpath(os.path.join(DIR, "../tmp/json/"))

DIR_FONT_FOR_HAN_SERIF = os.path.normpath(os.path.join(DIR, "../res/fonts/han-serif"))
DIR_FONT_FOR_HANDWRITTEN = os.path.normpath(
    os.path.join(DIR, "../res/fonts/handwritten")
)

DIR_PHONICS = os.path.normpath(os.path.join(DIR, "../res/phonics/"))
