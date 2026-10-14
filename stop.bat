@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo   Онлайн-переводчик (вариант 18) - остановка проекта
echo ============================================================
echo   1 - остановить контейнеры (данные БД СОХРАНЯЮТСЯ)
echo   2 - остановить и удалить контейнеры (данные БД сохраняются)
echo   3 - остановить, удалить контейнеры И данные БД
echo   0 - отмена
echo.

where docker >nul 2>&1
if not errorlevel 1 goto docker_ok
set "PATH=%LOCALAPPDATA%\Programs\DockerDesktop\resources\bin;%PATH%"
:docker_ok

set /p choice=Введите 1, 2, 3 или 0: 

if "%choice%"=="1" goto do_stop
if "%choice%"=="2" goto do_down
if "%choice%"=="3" goto do_down_v
echo Отменено.
pause
exit /b 0

:do_stop
echo Останавливаем контейнеры...
docker compose stop
goto done

:do_down
echo Останавливаем и удаляем контейнеры...
docker compose down
goto done

:do_down_v
echo Останавливаем, удаляем контейнеры и данные БД...
docker compose down -v

:done
echo.
docker compose ps
echo.
echo Готово.
pause