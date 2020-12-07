powershell -Command "Get-ChildItem .\distribution -Recurse | rmdir -Recurse"
mkdir distribution
cd .\distribution
pyinstaller ..\run.py --name "FactorioTwitchBot" --onefile --noconsole --icon ..\icon.ico
powershell -Command "Copy-Item -Recurse ..\configs\ -Destination .\dist\configs\"
powershell -Command "Copy-Item ..\README.md -Destination .\dist\README.txt"
powershell -Command "Copy-Item ..\settings.txt -Destination .\dist\settings.txt"
cd ..

