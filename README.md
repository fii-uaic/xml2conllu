# xml2conllu
TreeBank converter from UAIC XML format to CoNLL-U format

## Building the application ##
To build the application you'll need to have [PyInstaller](http://www.pyinstaller.org/) installed in the virtual environment.

After installing it navigate to `src` directory and use the following command to build the application:

``` powershell
pyinstaller -n xml2conllu.exe -F --noconsole .\xml2conllu.py
```

Unfortunately, specifying `--noconsole` may result in antivirus software deleting the executable immediately. Thus it's safer to skip the flag and use:

``` powershell
pyinstaller -n xml2conllu.exe -F .\xml2conllu.py
```

## Running the application from command-line ##
The application can be executed from command-line without GUI. To do so, use the following command:

``` shell
xml2conllu.exe --no-window --xml-file <xml-file-path> --postag-file <postag-file-path> --conllu-file <conllu-file-path> [--sent-id-start <integer-value>] [--sentence-type train|test]
```

To see what each parameter is doing, type:

``` shell
xml2conllu.exe --help
```
