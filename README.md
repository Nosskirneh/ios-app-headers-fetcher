# ios-app-headers-fetcher

Headers from iOS are easily browsed at [limneos site](http://developer.limneos.net/?ios=11.1.2) and [other GitHub repos](https://github.com/nst/iOS-Runtime-Headers/). However, headers from 3rd party apps are not publicity available. When building tweaks that depend on such apps, it's always a cat and mouse game to support their latest versions. Being able to compare classes and methods between versions makes this a lot easier.

ios-app-headers-fetcher is a Python script that first decrypts the app over SSH on an iOS device. The decrypted app is then transferred back where the headers are dumped and commited to a repo.

In my tweaks I often target Spotify and Deezer. These two, and possibly others can be found [at the headers repo](https://github.com/Nosskirneh/ios-app-headers).

## Requirements
[Clutch](https://github.com/KJCracks/Clutch) is used to decrypt apps. It exists several other solutions (CrackerXI, bfdecrypt, uncrypt11) that work on iOS 11, but as far as I know these do not support CLI or require the app to be opened.

[class-dump](http://stevenygard.com/download/class-dump-3.5.dmg) is used for retrieving the headers. I recommend compiling it from scratch to avoid the `Cannot find offset for address 0xa000000001003538 in stringAtAddress:` error with some (Swift?) apps.

## Installation
Firstly, make sure your ssh id_rsa file contains the SSH key from the device you're trying to connect. I recommend using `ssh-copy-id` if this is not the case.

`brew install libgit2` or [similar for other systems](https://github.com/libgit2/pygit2/blob/master/docs/install.rst)

`sudo -H pip3 install paramiko pygit2`

`git clone https://github.com/Nosskirneh/ios-app-headers-fetcher`

`cd ios-app-headers-fetcher; git clone git@github.com:Nosskirneh/ios-app-headers.git headers` or other repo of yours

Configure the IP in `config.py` or leave blank for use of `$THEOS_DEVICE_IP`.
