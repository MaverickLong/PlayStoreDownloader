# PlayStoreDownloader

## What this program do

This program fetches the latest Android application packages from Google Play, format and push them onto the download servers, and update the download site frontend.

As this is an script for a specific scenario, modifications to the script are needed if you wish to use it under other circumstances. Feel free to do it.

## Prerequisites

Python 3 (Tested with Python 3.10.7)

urllib3 < 1.26 (Tested with 1.25.11)

Zip Library (Simply install using your package manager)

SSH / SCP (Should come with your system, uhh, unless you are using Windows CMD?)

If you wish to push the packages to the download servers and/or push the index markdown to the frontend, you must add the SSH public key of the server which you deploys this script to the download servers' and/or frontend's authorized_keys section. This program relys on SCP on transferring the files.

[This Google Play API](https://github.com/Augustin-FL/googleplay-api)

## Configuration

just check `config.json` and you'll figure it out.

~~some game contain a standalone apk version (without obb or apks) and also a apk + obb / apks version. If you want the prior one, you may wish to set the subversion's "compatibilityMode" as true (e.g. Arcaea in the given config.json).~~

The downloader will now try fetching the standalone apk version by default, by using an earlier Android API. if it fails in fetching, it will instead use a more up-to-date Android API and fetch again.

*To be completed...*
