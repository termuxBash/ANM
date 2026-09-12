# ANM

The generated `self_extractor.py` uses only the Python standard library to unpack the application. The application itself requires `textual` and `cryptography`.

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
