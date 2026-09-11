<div align="center">

# mist
<img alt="logo" src="assets/logo.svg" width="30%"/>

**m**usic **i**ngestion & **s**torage **t**ool  
(another stupid content tracker)

![](https://img.shields.io/badge/code%20style-freestyle-313131.svg?style=flat-square)
![](https://img.shields.io/badge/quality-ass-1fb311.svg?style=flat-square)
![](https://img.shields.io/badge/tests-passing%20eventually-ffd700?style=flat-square)

![](https://img.shields.io/badge/Python-3.13-313131.svg?style=flat-square&logo=python&logoColor=ddd)
</div>

---

Mist is defined as 'when there is such obscurity and the associated visibility is equal to or exceeds 1000 m.' Like fog, mist is still the result of the suspension of water droplets, but simply at a lower density.

Mist typically is quicker to dissipate and can rapidly disappear with even slight winds, it's also what you see when you can see your breath on a cold day.

---

Mist downloads and preserves playlists and music from multiple platforms, including metadata and artwork.

## Features
- Download playlists with all the metadata you want.
- Detect removed items and decide on the best action to take.
  - Don't let YouTube randomly delete items from your precious playlists.
- Supports media and metadata from:
  - YouTube
  - YouTube Music
  - SoundCloud
  - Bandcamp

## Usage

### Cloning a playlist
Start by cloning a playlist.
```sh
mist clone <link-to-your-favorite-playlist>
```

Once the playlist grows a bit, synchronize it.
```sh
mist pull
```

## Installation
I'm not paid enough to package this properly yet. For now:
```sh
pip install .
```

### FFmpeg
FFmpeg is required for audio extraction.
Without it, you may end up with more than sound and the app will crash.

#### Linux
```sh
apt install ffmpeg
```

#### Termux
I want Termix to run on my phone tho.
```sh
pkg install ffmpeg
```

#### Windows
You will have to go down the rabbit hole...
https://ffmpeg.org/download.html

Ensure it's in your `PATH` variable.

### lxml

#### Termux
Dependencies for `lxml` (https://pypi.org/project/lxml/) module need to be installed.
```sh
pkg install libxml2 libxslt
```

## Configuration
#### `core.editor`
Text editor that will be used.

#### `core.concurrency`
Maximum number of concurrent downloads. Default is CPU count.

#### `core.color`
Available values are `auto`, `force` and `off`.

#### `core.version`
Indicates which version of the tool initialized the repository.

#### `core.retries`
How many times to retry after reaching rate limit.

#### `core.delay`
Delay after which to retry when rate limit is hit. Every retry doubles the delay (base value for exponential backoff).

#### `core.debug`
Boolean value to enable debug output.

---

#### `image.size`
Image dimensions to use. Format is `<width>x<height>`

#### `image.format`
Image format to use. Any part after "@" symbol is optional.
- `none` - no image will be embedded
- `jpeg`, `jpg` or `jfif` - compressed format
  - available pixel formats:
    - `l` - luminance
    - `rgb` - standard color
  - available subsampling: `4:0:0`, `4:2:0`, `4:2:2`, `4:4:4`
- `png` - lossless format
  - available pixel formats:
    - `i` - indexed
    - `ia` - indexed + alpha
    - `l` - luminance
    - `la` - luminance + alpha
    - `rgb` - standard color
    - `rgba` - standard color + alpha

> ```
> <compressed-format>[@<pixel-format>;<compression-ratio>%;<subsampling>]
> ```
> or
> ```
> <lossless-format>[@<pixel-format>;cl<compression-level>]
> ```

#### `image.adjustment`
Possible values are `zoom`, `scaled`, `crop` and `stretch`.

---

#### `remote.<name>.url`
URL of the playlist.

#### `remote.<name>.start`
Index where to start.

#### `remote.<name>.end`
Index where to end.

---

#### `clone.defaultRemoteName`
Default name for the remote when nothing is specified.

---

> [!CAUTION]
> Undefined operation leads to undefined behavior.

Wow, I really need to use [YapTeX](https://github.com/Zexyp/YapTeX) for these docs! :3

## TODOs
- `remote.<name>.skipFetchAll`
- `remote.<name>.items`
- use yaptex
