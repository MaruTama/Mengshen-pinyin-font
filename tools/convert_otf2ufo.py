# [UFO Extractor](https://github.com/robotools/extractor)

import extractor
import defcon

ufo = defcon.Font()
extractor.extractUFO("SawarabiMincho-Regular.ttf", ufo)
ufo.save("unchi.ufo")
