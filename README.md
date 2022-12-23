# PlayStoreDownloader

## Prerequisites

Python 3 (Tested with Python 3.10.7)

urllib3 < 1.26 (Tested with 1.25.11)

Zip Library (Simply install using your package manager)

SSH / SCP (Should come with your system, uh, unless you are using Windows CMD?)

[This Google Play API](https://github.com/Augustin-FL/googleplay-api)

## Configuration

just check `config.json` and you'll figure it out.

some game contain a standalone apk version (without obb) and also a apk + obb version. If you want the prior one, you may wish to set the subversion's "compatibilityMode" as true (e.g. Arcaea in the given config.json).

*To be completed...*
