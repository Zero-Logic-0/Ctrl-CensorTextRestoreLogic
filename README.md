C.T.R.L. (Censor Text Restore Logic) è un software Python locale progettato per l'anonimizzazione bidirezionale dei dati sensibili. Nasce per permettere a professionisti, aziende e utenti privati di utilizzare strumenti web o agenti di intelligenza artificiale in totale sicurezza, impedendo a monte la condivisione di informazioni riservate e mantenendo ogni elaborazione esclusivamente sul proprio computer.

Cosa può censurare
Il sistema adotta un approccio ibrido, combinando espressioni regolari (Regex) contestuali e modelli di intelligenza artificiale NLP (it_core_news_lg) per individuare e mascherare:

Identificativi personali e fiscali: Codice Fiscale, Carta d'Identità, Partita IVA, IMEI, [Azienda 1].

Dati finanziari: Coordinate IBAN (nazionali e internazionali), Carte di Credito.

Rete e credenziali: Indirizzi IP (IPv4 e IPv6), Indirizzi MAC, API Key, User/Password.

Contatti e recapiti: Indirizzi email, Numeri di telefono (fissi e mobili), Indirizzi fisici, Targhe automobilistiche.

Anagrafica ed entità: Nomi di persone, Titoli professionali, Nomi aziendali e Organizzazioni.

Come utilizzarlo

Installazione: Esegui il file di installazione .bat per configurare le dipendenze e scaricare il modello IA necessario.

Avvio: Avvia il programma eseguendo il comando python main_ctrl.py nel terminale oppure facendo doppio clic sul file run.bat.

Esecuzione: L'applicazione rimane attiva in background ed in ascolto fino alla chiusura.

Scorciatoie e logica di funzionamento
L'elaborazione si basa sulla gestione intelligente della clipboard di sistema ed è completamente bidirezionale:

Ctrl+C: Copia il testo negli appunti applicando la censura automatica dei dati sensibili. Se utilizzato su un testo già censurato contenente i tag della sessione attiva, effettua l'operazione inversa ripristinando il testo in chiaro originale.

Esc: Termina l'applicazione in sicurezza azzerando la memoria RAM.
