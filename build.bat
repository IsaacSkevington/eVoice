@echo off
echo ==================================================
echo COPYRIGHT 2020 Jacqueline Dobreva/Isaac Skevington
echo ==================================================
echo ------------Welcome to the Eve build tool, please read the following carefully
echo Assuming correct extraction of the zip file this came in, the file requirements should be satisfied
echo Please check that they are as detailed below:
echo Please make sure that python and pip are installed and both on path
echo Please make sure the EveUI.spec and the EveUI.py file are both in this directory
echo Please make sure the image files required are placed in a subdirectory named e-Voice and the icon in this directory
echo The code will not be signed. To sign to code, generate a certificate or send the executable to os3help@gmail.com to be signed
timeout /t 20
echo Starting build
echo Installing requirements
pip install astroid
pip install certifi
pip install colorama
pip install cycler
pip install isort
pip install kiwisolver
pip install lazy-object-proxy
pip install mccabe
pip install mysql-connector-python
pip install numpy
pip install Pillow
pip install protobuf
pip install pylint
pip install pyparsing
pip install python-dateutil
pip install six
pip install tk
pip install toml
pip install wrapt
pip install XlsxWriter
pip install altgraph
pip install Babel
pip install cachetools
pip install chardet
pip install future
pip install idna
pip install importlib-metadata
pip install pefile
pip install pyinstaller
pip install pyinstaller-hooks-contrib
pip install pyodbc
pip install pytz
pip install pywin32-ctypes
pip install requests
pip install tkcalendar
pip install tornado
pip install urllib3
pip install zipp
echo Requirements installed
echo Buidling the file
pyinstaller EveUI.spec
echo Build complete, the exe is in the dist folder
pause
