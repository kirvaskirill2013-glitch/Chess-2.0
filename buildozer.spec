
[app]

title = Chess 2.0
package.name = chess2
package.domain = org.example

source.dir = .
source.include_exts = py,json,txt,png,jpg,kv

version = 2.0

requirements = python3,kivy==2.3.0,python-chess

orientation = portrait
fullscreen = 0

android.api = 35
android.minapi = 24
android.ndk = 28c
android.archs = arm64-v8a

[buildozer]

log_level = 2
warn_on_root = 1

