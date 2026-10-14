@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo   Онлайн-переводчик (вариант 18) - запуск проекта
echo ============================================================
echo.

where docker >nul 2>&1
if not errorlevel 1 goto docker_ok
echo [i] Команда docker не найдена в PATH. Пробуем стандартный путь...
set "PATH=%LOCALAPPDATA%\Programs\DockerDesktop\resources\bin;%PATH%"
where docker >nul 2>&1
if not errorlevel 1 goto docker_ok
echo [!] Docker не найден.
echo     Установите Docker Desktop: https://www.docker.com/products/docker-desktop/
pause
exit /b 1

:docker_ok
docker info >nul 2>&1
if not errorlevel 1 goto engine_ok
echo [i] Движок Docker не запущен. Запускаем Docker Desktop...
if exist "%LOCALAPPDATA%\Programs\DockerDesktop\Docker Desktop.exe" start "" "%LOCALAPPDATA%\Programs\DockerDesktop\Docker Desktop.exe"
if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
echo [i] Ожидание готовности Docker (может занять до 2-3 минут)...
set /a _try=0
:waitloop
set /a _try+=1
if %_try% GTR 60 goto engine_fail
timeout /t 5 /nobreak >nul
docker info >nul 2>&1
if errorlevel 1 goto waitloop

:engine_ok
echo [ok] Docker готов.
echo.

echo [1/2] Сборка образов и запуск 4 контейнеров...
docker compose up -d --build
if errorlevel 1 goto compose_fail

echo.
echo [2/2] Ожидание готовности сервисов...
timeout /t 8 /nobreak >nul
docker compose ps
echo.

echo Открываем http://localhost:8080 в браузере...
start "" http://localhost:8080
echo.
echo ============================================================
echo   Готово! Приложение доступно: http://localhost:8080
echo   Остановить проект: двойной клик по stop.bat
echo ============================================================
pause
exit /b 0

:engine_fail
echo [!] Docker так и не запустился. Откройте Docker Desktop вручную и повторите.
pause
exit /b 1

:compose_fail
echo.
echo [!] Не удалось запустить проект. Смотрите вывод выше.
echo     Частая причина - занятый порт 8080. Подробности в README.md.
pause
exit /b 1