# MQ-DL
Tool written in Python to download streamable tracks from mora qualitas (モーラクオリタス).    

**People have been seen selling my tools. DO NOT buy them. My tools are free and always will be.**

![](https://orion.feralhosting.com/sorrow/share/MQ-DL_test_R2.png)
Rewrite. [Windows binaries](https://github.com/Sorrow446/MQ-DL/releases)

```
 _____ _____     ____  __
|     |     |___|    \|  |
| | | |  |  |___|  |  |  |__
|_|_|_|__  _|   |____/|_____|
         |__|

usage: MQ-DL.py [-h] -u URL [URL ...] [-q {1,2,3,4}] [-c {1,2,3,4,5}]
                [-t TEMPLATE] [-k] [-o] [-l {en-US,ja-JP}]

optional arguments:
  -h, --help            show this help message and exit
  -u URL [URL ...], --url URL [URL ...]
                        Multiple links or a text file filename / abs path.
  -q {1,2,3,4}, --quality {1,2,3,4}
                        1: AAC PLUS, 2: MP3, 3: AAC, 4: best/FLAC.
  -c {1,2,3,4,5}, --cover-size {1,2,3,4,5}
                        1: 70, 2: 170, 3: 300, 4: 500, 5: 600.
  -t TEMPLATE, --template TEMPLATE
                        Naming template for track filenames.
  -k, --keep-cover      Leave albums' covers in their respective folders.
  -o, --output-dir      Abs output directory. Double up backslashes or use
                        single forward slashes for Windows. Default: \MQ-DL
                        downloads
  -l {en-US,ja-JP}, --meta-lang {en-US,ja-JP}
                        Metadata language.
```
