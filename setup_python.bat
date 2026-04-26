@echo off
echo Configurando ambiente Python para JARVIS...
echo.

echo Adicionando Python ao PATH temporariamente...
set PATH=%PATH%;C:\Users\Augusto\AppData\Local\Python\pythoncore-3.14-64;C:\Users\Augusto\AppData\Local\Python\pythoncore-3.14-64\Scripts

echo Verificando instalação do Python...
python --version
echo.

echo Verificando instalação do pip...
pip --version
echo.

echo Criando ambiente virtual para o JARVIS...
python -m venv jarvis-env
echo Ambiente virtual criado com sucesso!

echo.
echo Para ativar o ambiente virtual, execute:
echo   jarvis-env\Scripts\activate
echo.
echo Para desativar, execute:
echo   deactivate
echo.
pause
