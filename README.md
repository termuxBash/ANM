# ANM

The generated `self_extractor.py` uses only the Python standard library to unpack the application. The application itself requires `textual` and `cryptography`.
https://script.google.com/macros/s/AKfycbzNessUVBValwuGTckyAvdZt52SV5yU46HNvKaczp7-1-S4a_gkcHyNuK8HV21PFCzheQ/exec
## Linux

```sh
python3 -m pip install -r requirements.txt
python3 self_extractor.py
```

## Termux

```sh
pkg install python
python -m pip install -r requirements.txt
python self_extractor.py
```

Run the extractor from a writable directory. It rebuilds itself after the database is edited.

## Rebuild

Before running the application for the first time, build the extractor with:

```sh
python3 builder.py
```
