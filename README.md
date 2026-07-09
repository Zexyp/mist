<div align="center">

# mist
**m**usic **i**ngestion & **s**torage **t**ool

![](https://img.shields.io/badge/code%20style-freestyle-313131.svg?style=flat-square)
![](https://img.shields.io/badge/quality-ass-1fb311.svg?style=flat-square)
![](https://img.shields.io/badge/tests-passing%20eventually-ffd700?style=flat-square)
</div>

---

Mist is defined as 'when there is such obscurity and the associated visibility is equal to or exceeds 1000 m.' Like fog, mist is still the result of the suspension of water droplets, but simply at a lower density.

Mist typically is quicker to dissipate and can rapidly disappear with even slight winds, it's also what you see when you can see your breath on a cold day.

---

## Features
- TODO

## Usage
Would you mind if I use YapTeX for docs? :3

## Installation
I'm not paid enough. Try this:
```sh
pip install .
```

> ### FFmpeg
> FFmpeg is strongly recommended, otherwise you will have more than sound and the app will prolly crash.
> 
> #### Linux
> ```sh
> apt install ffmpeg
> ```
> 
> #### Termux
> I want Termix to run on my phone tho.
> ```sh
> pkg install ffmpeg
> ```
> 
> #### Windows
> You will have to go down the rabbit hole...

> ### lxml
> 
> #### Termux
> Dependencies for `lxml` (https://pypi.org/project/lxml/) module need to be installed.
> ```sh
> pkg install libxml2 libxslt
> ```

## Configuration
- `core.editor`
- `core.debug`
- `core.color`
- `core.version`
- `core.concurrency`

- `clone.defaultRemoteName`

- `remote.<name>.url`

### TODO:
- `remote.<name>.skipFetchAll`
- `remote.<name>.start`
- `remote.<name>.end`
- `remote.<name>.items`

**TODO:** use yaptex

> [!CAUTION]
> Undefined operation leads to undefined behavior.
