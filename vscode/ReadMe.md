# ReadMe

## Link settings.json to your vscode directory

### On Windows, create a hard link:
`mklink /H C:\<path_to_dotfiles>\vscode\settings.json %APPDATA%\Code\User\settings.json`

## Link extensions

### On Windows, create a hard link:
`mklink /D C:\<path_to_dotfiles>\vscode\extensions %USERPROFILE%\.vscode\extensions`