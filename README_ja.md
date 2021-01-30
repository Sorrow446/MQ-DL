# MQ-DL
モーラクオリタスからのストリームできるトラックをダウンロードするためのPythonで書かれたツールです。
![](https://i.imgur.com/iCrOETB.png)
[Windowsバイナリー](https://github.com/Sorrow446/MQ-DL/releases)
[MOOV－DL](https://github.com/Sorrow446/MOOV-DL)にも興味があるかもしれません。

## 対応されているメディア
|種類|URL例|
| --- | --- |
|アルバム|`https://content.mora-qualitas.com/artist/ryukku-to-soine-gohan/album/neo-neo-ep`
|アーティスト|`https://content.mora-qualitas.com/artist/ryukku-to-soine-gohan`
|お気に入り|`https://content.mora-qualitas.com/favorites`
|プレイリスト|`https://content.mora-qualitas.com/playlist/pp.543884501`
|トラック|`https://content.mora-qualitas.com/artist/ryukku-to-soine-gohan/album/neo-neo-ep/track/t.533232673`
|ユーザープのレイリスト|`https://content.mora-qualitas.com/playlist/mp.280976624`

## 使用例
トラックをダウンロードする。    
`mq-dl.py/mq-dl_x86.exe -u https://content.mora-qualitas.com/artist/ryukku-to-soine-gohan/album/neo-neo-ep/track/t.533232673`
２つのリストからとお気に入りのトラックをダウンロードする。    
`mq-dl.py/mq-dl_x86.exe -u E:/urls.txt G:/urls_2.txt https://content.mora-qualitas.com/favorites`
プレイリストとアーティストのディスコグラフィーをダウンロードする。    
`mq-dl.py/mq-dl_x86.exe -u https://content.mora-qualitas.com/playlist/pp.543884501 https://content.mora-qualitas.com/artist/ryukku-to-soine-gohan`

全部のメディアの種類が組み合わせられます。複製URLと複製テキストファイルがフィルターされます。

```
 _____ _____     ____  __
|     |     |___|    \|  |
| | | |  |  |___|  |  |  |__
|_|_|_|__  _|   |____/|_____|
         |__|

usage: mq-dl.py [-h] -u URLS [URLS ...] [-q {1,2,3,4}] [-c {1,2,3,4,5}]
                [-t TEMPLATE] [-k] [-o OUTPUT_DIR] [-l {1,2}]

optional arguments:
  -h, --help            show this help message and exit
  -u URLS [URLS ...], --urls URLS [URLS ...]
                        Multiple links seperated by spaces or a text file
                        path.
  -q {1,2,3,4}, --quality {1,2,3,4}
                        1: AAC PLUS, 2: MP3, 3: AAC, 4: best/FLAC.
  -c {1,2,3,4,5}, --cover-size {1,2,3,4,5}
                        1: 70, 2: 170, 3: 300, 4: 500, 5: 600.
  -t TEMPLATE, --template TEMPLATE
                        Naming template for track filenames.
  -k, --keep-cover      Keep cover in album folder. Does not apply to
                        playlists or favourites.
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                        Output directory. Double up backslashes or use single
                        forward slashes for Windows. Default: \MQ-DL downloads
  -l {1,2}, --meta-lang {1,2}
                        Metadata language. 1 = English, 2 = Japanese.
```
