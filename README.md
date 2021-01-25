# MQ-DL
Tool written in Python to download streamable tracks from mora qualitas (モーラクオリタス).    
**People have been seen selling my tools. DO NOT buy them. My tools are free and always will be.**
![](https://i.imgur.com/iCrOETB.png)
[Windows binaries](https://github.com/Sorrow446/MQ-DL/releases)
You might also be interested in [MOOV-DL](https://github.com/Sorrow446/MOOV-DL).

## Supported Media
|Type|URL example|
| --- | --- |
|Album|`https://content.mora-qualitas.com/artist/ryukku-to-soine-gohan/album/neo-neo-ep`
|Artist|`https://content.mora-qualitas.com/artist/ryukku-to-soine-gohan`
|Favourites|`https://content.mora-qualitas.com/favorites`
|Playlist|`https://content.mora-qualitas.com/playlist/pp.543884501`
|Track|`https://content.mora-qualitas.com/artist/ryukku-to-soine-gohan/album/neo-neo-ep/track/t.533232673`
|User playlist|`https://content.mora-qualitas.com/playlist/mp.280976624`

## Usage Examples
Download a single track.    
`mq-dl.py/mq-dl_x86.exe -u https://content.mora-qualitas.com/artist/ryukku-to-soine-gohan/album/neo-neo-ep/track/t.533232673`

Download from two lists and favourited tracks.    
`mq-dl.py/mq-dl_x86.exe -u E:/urls.txt G:/urls_2.txt https://content.mora-qualitas.com/favorites`

Download a playlist and an artist's discography.    
`mq-dl.py/mq-dl_x86.exe https://content.mora-qualitas.com/playlist/pp.543884501 https://content.mora-qualitas.com/artist/ryukku-to-soine-gohan`

You can mix all media types. Duplicate URLs and text files will be filtered.

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

## Config
|Option|Info|
| --- | --- |
|email|Your email address.
|password|Your password.
|output_dir|Where to download to. You must double up your backslashes or use single forward slashes instead.
|quality|Track quality to request from the API. 1: AAC PLUS, 2: MP3, 3: AAC, 4: best/FLAC.
|cover_size|Cover size to fetch. 1: 70, 2: 170, 3: 300, 4: 500, 5: 600.
|fname_template|Filename template for tracks. Available variables: artist, isrc, title, track, trackpadded, album, albumartist, copyright, label, tracktotal, upc
|keep_cover|Keep cover in album folder. Does not apply to playlists or favourites.
|meta_language|Language of metadata to request from the API. 1 = English, 2 = Japanese.
|media_types\artist\folder_template|Folder template for artist media type. Blank = no folder. Available variables: artist.
|media_types\artist\albums|Include main albums in artist media type.
|media_types\artist\compilations|Include compilation albums in artist media type.
|media_types\artist\singles_and_eps|Include singles and EPs in artist media type.
|media_types\favourites\folder_name|Folder name for favourites media type. Blank = no folder.
|media_types\track\folder_template|Folder template for track media type. Blank = no folder. Available variables: album, albumartist, copyright, label, tracktotal, upc
|media_types\album\folder_template|Folder name for album media type. Blank = no folder. Available variables: album, albumartist, copyright, label, tracktotal, upc
|media_types\playlist\folder_template|Folder name for playlist media type. Blank = no folder. Available variables: id, name
|media_types\user_playlist\folder_template|Folder name for user playlist media type. Blank = no folder. Available variables: id, name

Any of the same specified CLI arguments will override your config file.
