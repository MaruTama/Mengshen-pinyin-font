# [ufo2ft](https://github.com/googlefonts/ufo2ft)
from defcon import Font
from ufo2ft import compileOTF

ufo = Font('unchi.ufo')
otf = compileOTF(ufo)
otf.save('MyFont-Regular.otf')
