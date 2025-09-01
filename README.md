# Mist
*Music Ingestion & Storage Tool*

---

Mist is defined as 'when there is such obscurity and the associated visibility is equal to or exceeds 1000 m.' Like fog, mist is still the result of the suspension of water droplets, but simply at a lower density.

Mist typically is quicker to dissipate and can rapidly disappear with even slight winds, it's also what you see when you can see your breath on a cold day.

---

## Usage
Have you heard of git?

Would you mind if I use YapTeX for docs? :3

## Installation
I'm not paid enough. I guess try this:
```sh
pip install .
```

### FFmpeg
FFmpeg is strongly recommended.

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

### Optional modules
To install all optional modules you can use supplied `optional-requirements.txt`:
```sh
pip install -r optional-requirements.txt
```

#### `colorama` (https://pypi.org/project/colorama/)
Colorful logging.

#### `playsound` (https://pypi.org/project/playsound/)
To inform about completion or failure.

#### `lxml` (https://pypi.org/project/lxml/)
Additional tag scraping.

On **Termux** dependencies need to be installed:
```sh
pkg install libxml2 libxslt
```

> [!CAUTION]
> Undefined operation leads to undefined behavior.
