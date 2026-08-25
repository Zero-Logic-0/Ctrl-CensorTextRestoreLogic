@echo off
title Installazione Dipendenze C.T.R.L.
echo ===================================================
echo Inizializzazione setup per C.T.R.L.
echo ===================================================
echo.

echo 1. Aggiornamento di pip...
python -m pip install --upgrade pip

echo.
echo 2. Installazione delle librerie necessarie...
pip install -r requirements.txt

echo.
echo 3. Download del modello NLP italiano (spaCy)...
python -m spacy download it_core_news_lg

echo.
echo ===================================================
echo Installazione completata con successo.
echo ===================================================
pause