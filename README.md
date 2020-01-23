# hpwren-mirror

Script to mirror subsets of HPWREN.


This script has only be developed for and tested with subsets of HPWREN camera data, it may not work for all camera data. Please feel free to send pull requests.

## Configuration

Add to your ~/.bashrc
```bash
export HPWREN_MIRROR_DIR=${HOME}/hpwrendata/
```

Example datasets.conf:
```text
# location identifier, camera/view , description
marconi    ,n       , Upper Talega
```


Multiple cameras can be separated with semicolon: `n;s`


## Usage
```bash
hpwren-mirror.py -c datasets.conf
```


## Disclaimer
If you download pictures from HPWREN, please respect their disclaimer:

[http://hpwren.ucsd.edu/cameras/disclaimer.html](http://hpwren.ucsd.edu/cameras/disclaimer.html)