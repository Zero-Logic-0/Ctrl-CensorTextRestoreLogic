import time  # Importa il modulo per gestire le pause di sistema (es. attesa aggiornamento appunti)
import sys  # Importa il modulo per le funzioni di sistema e per forzare la chiusura del programma
import threading  # Importa il modulo per eseguire l'intercettazione dei tasti in background
import re  # Importa il modulo per le espressioni regolari (usato per cercare pattern testuali/matematici)
import spacy  # Importa la libreria di Intelligenza Artificiale per l'elaborazione del linguaggio naturale
import pyperclip  # Importa la libreria per leggere il testo copiato e sovrascrivere gli appunti
from pynput import keyboard  # Importa il modulo per intercettare i tasti globalmente (anche fuori dal terminale)

print("Ctrl Attivo - Avvio in corso...")  # Stampa un messaggio nel terminale per segnalare l'inizio dell'avvio

try:  # Avvia un blocco di prova per catturare eventuali errori nel caricamento del modello IA
    nlp = spacy.load("it_core_news_lg")  # Carica in memoria il modello IA avanzato italiano (Large)
    print("[IA] Modello 'Large' caricato con successo (Massima Precisione).")  # Conferma all'utente il caricamento
except OSError:  # Intercetta l'errore che si verifica se il modello non è installato nel computer
    print("\n[ERRORE] Modello IA 'it_core_news_lg' non trovato!")  # Avvisa l'utente della mancanza del modello
    print("Per favore, apri il terminale e digita esattamente questo comando:")  # Fornisce istruzioni per risolvere
    print("python -m spacy download it_core_news_lg\n")  # Mostra il comando esatto per installare il modello
    sys.exit(1)  # Termina immediatamente l'esecuzione del programma segnalando uno stato di errore

class CTRLEngine:  # Definisce la classe principale che si occupa di analizzare e censurare i dati
    def __init__(self):  # Costruttore della classe, eseguito durante l'inizializzazione del motore
        self.rigid_patterns = [  # Crea una lista contenente le regole matematiche (Regex) per i dati sensibili
            ("Codice Fiscale", re.compile(r'\b[A-Z]{6}\d{2}[A-EHLMPR-T]\d{2}[A-Z]\d{3}[A-Z]\b', re.IGNORECASE)),  # Regola per i Codici Fiscali italiani
            ("Partita IVA", re.compile(r'\b(?:IT)?\d{11}\b', re.IGNORECASE)),  # Regola per trovare le Partite IVA (con o senza 'IT')
            ("Email", re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', re.IGNORECASE)),  # Regola standard per gli indirizzi Email
            ("IBAN", re.compile(r'\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){3,7}(?:\s?[A-Z0-9]{1,4})?\b', re.IGNORECASE)),  # Regola per i codici IBAN internazionali
            # Pattern Carte esteso: supporta Amex 15 cifre (inizia con 34 o 37) prima della verifica telefono per evitare sovrapposizioni
            ("Carta di Credito", re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}|\b3[47]\d{2}[-\s]?\d{6}[-\s]?\d{5}\b|\b\d{4}[-\s]?\d{6}[-\s]?\d{5}\b|\b\d{13,19}\b', re.IGNORECASE)),
            ("Telefono", re.compile(r'(?:(?:\+|00)\d{1,3}[\s.-]?)?(?:\(\d{2,5}\)[\s.-]?|\d{2,5}[\s.-])\d{5,8}\b', re.IGNORECASE)),  # Regola per i numeri telefonici e prefissi
            ("Indirizzo IP", re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b')),  # Regola matematica esatta per IP IPv4
            ("Targa", re.compile(r'\b[A-Z]{2}\s?\d{3}\s?[A-Z]{2}\b', re.IGNORECASE)),  # Regola per le targhe automobilistiche italiane (es. AB123CD)
            ("Azienda", re.compile(r'\b[A-Z0-9À-ÿ][A-Za-z0-9À-ÿ\s&\.\'-]{1,50}?\s+(?:S\.r\.l\.s\.|S\.p\.A\.|S\.r\.l\.|S\.n\.c\.|S\.a\.s\.|S\.u\.r\.l\.|S\.a\.p\.a\.|Soc\.?\s*Coop\.?|SpA|Srls|Srl|Surl|Snc|Sas|GmbH|LLC|Ltd|Inc\.?)(?!\w)', re.IGNORECASE))  # Cerca ragioni sociali tramite i loro acronimi ufficiali
        ]  # Chiude la lista dei pattern rigidi

        # Definisce la struttura logica per identificare Nomi e Cognomi con iniziali maiuscole (inclusi prefissi come De, Di, Mac)
        name_pattern = r'\s+[A-ZÀÈÉÌÒÙ][a-zà-ÿ]+(?:[\'\s](?:di\s+|da\s+|de(?:l|ll\'|lla|i|gli|lle)?\s+|De\s+|Di\s+|Mac|Mc|O\')?[A-ZÀÈÉÌÒÙ][a-zà-ÿ]+)?'
        # Elenca i titoli professionali, civili e accademici più comuni
        title_list = r'Dott\.ssa|Dott\.?|Dottoressa|Dr\.ssa|Dr\.?|Prof\.ssa|Prof\.?|Avv\.?|Avvocato|Ing\.?|Ingegnere|Arch\.?|Architetto|Geom\.?|Pres\.?|Presidente|Dir\.?|Direttore|Sindaco|Assessore|Min\.?|Ministro|Cons\.?|Consigliere|Sig\.na|Sig\.ra|Sig\.?|Signor|Signora|Signorina|Mr\.?|Mrs\.?|Miss'
        # Unisce i titoli e i nomi in un'unica regola Regex compilata per un'esecuzione rapida
        self.titles_regex = re.compile(r'\b(?i:' + title_list + r')' + name_pattern + r'(?!\w)')

        # Blacklist aggiornata: parole comuni o abbreviazioni ('cf') che l'IA non deve confondere con Enti/Aziende/Persone
        self.blacklist = {
            "codice", "fiscale", "cf", "iban", "partita", "iva", "email", "telefono", 
            "carta", "credito", "stato", "lavori", "server", "targa", "via", "piazza", 
            "fatturazione", "registrazione", "pratica", "protocollo", "dossier", "istanza"
        }

    def mask(self, text: str) -> tuple[str, dict]:  # Metodo principale per oscurare i dati nel testo fornito
        if len(text) > 100000:  # Misura di sicurezza: evita il blocco del sistema se si copiano testi enormi (es. interi libri)
            return text, {}  # Ritorna il testo inalterato e un dizionario vuoto
        sanitized_text = text  # Crea una stringa di lavoro clonando il testo originale
        session_map = {}  # Dizionario per memorizzare l'associazione tra Tag oscurato e Dato originale
        counters = {}  # Contatori per enumerare dinamicamente le categorie (es. Utente 1, Utente 2)
        unique_matches = {}  # Dizionario di appoggio per evitare di sovrascrivere o raddoppiare gli stessi dati trovati

        def get_tag(category_name: str) -> str:  # Funzione interna per generare la stringa del Tag incrementale
            counters[category_name] = counters.get(category_name, 0) + 1  # Incrementa il contatore specifico della categoria
            return f"[{category_name} {counters[category_name]}]"  # Genera il testo finale (es. "[Azienda 1]")

        try:  # Inizia il blocco sicuro per catturare errori durante l'estrazione
            # FASE 1: Ricerca basata su regole matematiche precise (Regex)
            for label, pattern in self.rigid_patterns:  # Itera tutte le espressioni regolari predefinite
                for m in pattern.finditer(sanitized_text):  # Cerca tutte le occorrenze esatte nel testo
                    val = m.group().strip()  # Estrae la stringa trovata e pulisce gli spazi ai bordi
                    if val and val not in unique_matches:  # Se è valida e non è già stata processata
                        unique_matches[val] = label  # Assegna la stringa alla sua etichetta (es. 'Codice Fiscale')

            # FASE 2: Ricerca dei Nomi propri preceduti da Titoli (es. Dott. Rossi)
            for m in self.titles_regex.finditer(sanitized_text):
                val = m.group().strip()  # Pulisce gli spazi vuoti
                if val and val not in unique_matches:
                    unique_matches[val] = "Contatto"  # Salva sotto la categoria unificata 'Contatto'

            # FASE 3: Elaborazione tramite Intelligenza Artificiale (NLP - Natural Language Processing)
            try:
                doc = nlp(sanitized_text)  # Sottopone il testo residuo all'analisi semantica del modello IA
                for ent in doc.ents:  # Itera le entità (nomi, luoghi, organizzazioni) riconosciute
                    val = ent.text.strip()  # Estrae la stringa individuata dall'IA
                    if val and val not in unique_matches:  # Se l'entità è nuova e non identificata dalle Regex
                        # Verifica Anti-Falsi Positivi: controlla se la parola esatta rientra nella blacklist (es. 'CF')
                        if any(re.search(rf'\b{re.escape(b)}\b', val, re.IGNORECASE) for b in self.blacklist):
                            continue  # Salta questa parola ignorandola
                        # Evita la cattura di numeri d'indice a inizio riga (es. "015. Fatturazione")
                        if re.match(r'^\d+[\.\s]', val):
                            continue  # Salta per non corrompere gli indici numerici del testo
                        # Classifica la Persona (deve contenere uno spazio, quindi Nome + Cognome)
                        if ent.label_ == "PER" and " " in val:
                            unique_matches[val] = "Utente"  # Assegna il tag 'Utente'
                        # Classifica l'Azienda (limite di 4 parole per evitare che l'IA inglobi un'intera frase)
                        elif ent.label_ == "ORG" and len(val.split()) <= 4:
                            unique_matches[val] = "Azienda"  # Assegna il tag 'Azienda'
            except Exception as nlp_err:  # Intercetta problemi specifici della libreria spaCy
                print(f"[Avviso IA] Errore di analisi testuale: {nlp_err}")  # Stampa l'errore senza bloccare tutto

        except Exception as e:  # Gestore di tutti i crash generici
            print(f"[Avviso Sistema] Errore fatale durante l'estrazione: {e}")
            return text, {}  # In caso di errore critico, restituisce il testo invariato per sicurezza

        # Pulisce i risultati escludendo eventuali tag fittizi che presentano già parentesi quadre
        valid_matches = [(k, v) for k, v in unique_matches.items() if k and "[" not in k and "]" not in k]
        # ORDINA i risultati dal più lungo al più corto: fondamentale per non spezzare stringhe incluse in altre stringhe più grandi
        valid_matches.sort(key=lambda x: len(x[0]), reverse=True)

        for match_val, label in valid_matches:  # Scorre tutti i dati pronti per l'anonimizzazione
            if match_val in sanitized_text:  # Verifica un'ultima volta che la stringa esista nel testo attuale
                placeholder = get_tag(label)  # Ottiene il tag numerato (es. "[Email 3]")
                session_map[placeholder] = match_val  # Crea il collegamento bi-direzionale in memoria (Tag <-> Testo Reale)
                sanitized_text = sanitized_text.replace(match_val, placeholder)  # Effettua la sostituzione fisica nel testo

        return sanitized_text, session_map  # Restituisce il testo censurato e il dizionario per la futura decodifica

class CTRLController:  # Definisce la classe che controlla il flusso e gestisce la Clipboard (Appunti)
    def __init__(self):  # Costruttore del Controller
        self.engine = CTRLEngine()  # Istanzia il motore di oscuramento IA+Regex
        self.last_session_map = {}  # Memoria che conserva la mappa di conversione dell'ultima copia effettuata
        self.last_processed_text = ""  # Memorizza l'ultimo testo elaborato per evitare loop infiniti di copia-incolla
        self.is_active = True  # Variabile di stato per abilitare/disabilitare il sistema
        self.lock = threading.Lock()  # Semaforo che impedisce a due pressioni di Ctrl+C di sovrapporsi creando conflitti

    def log(self, message: str):  # Funzione di utilità per formattare gli output nella console
        timestamp = time.strftime("%H:%M:%S")  # Preleva l'ora esatta di sistema
        print(f"[{timestamp}] {message}")  # Stampa il log a video con il prefisso orario

    def reset_session(self):  # Nuova funzione: azzera la memoria tra una copia e l'altra di testi in chiaro
        self.last_session_map.clear()  # Svuota il dizionario dei vecchi tag
        self.last_processed_text = ""  # Svuota l'archivio testuale
        self.log("[RESET SESSIONE] Nuova copia rilevata. Contatori ripartiti da [Utente 1], [Azienda 1], ecc.")  # Avvisa l'operatore in console

    def read_clipboard_smart(self, max_attempts=5) -> str:  # Funzione robusta per leggere gli appunti ignorando blocchi momentanei di Windows/Mac
        time.sleep(0.08)  # Attesa vitale per far sì che il Sistema Operativo finisca fisicamente l'operazione di Copia
        for attempt in range(max_attempts):  # Riprova per N tentativi in caso di accessi negati da altre app
            try:
                current = pyperclip.paste()  # Tenta di prelevare il testo dagli appunti
                if current and isinstance(current, str):  # Se c'è del testo ed è formato stringa
                    return current  # Restituisce il testo con successo
            except Exception:  # Intercetta eventuali errori di accesso concorrente alla clipboard
                pass  # Ignora l'errore e passa al prossimo tentativo
            time.sleep(0.05 * (attempt + 1))  # Incrementa il tempo di attesa ad ogni fallimento
        return ""  # Se falliscono tutti i tentativi, restituisce una stringa vuota

    def process_clipboard(self):  # Funzione principale attivata alla pressione fisica di Ctrl+C
        if not self.lock.acquire(blocking=False):  # Controlla il semaforo: se è già occupato da un'altra esecuzione, si ferma
            return
        try:
            if not self.is_active:  # Verifica che il programma non sia stato messo in pausa
                return
            raw_text = self.read_clipboard_smart()  # Legge il contenuto copiato con la funzione intelligente
            if not raw_text or raw_text == self.last_processed_text:  # Blocca se non c'è testo o se è identico alla passata elaborazione
                return
            
            # ==== FASE 1: DE-ANONIMIZZAZIONE (RIPRISTINO) ====
            # Si attiva SOLO SE il testo copiato contiene delle parentesi quadre "[" e "]" e se esiste una mappa in memoria
            if "[" in raw_text and "]" in raw_text and self.last_session_map:
                unmasked_text = raw_text  # Prepara la variabile per il testo in chiaro
                for placeholder, original_val in self.last_session_map.items():  # Scorre ogni Tag registrato (es. [Email 1])
                    clean_tag = placeholder.strip("[]")  # Rimuove le parentesi quadre di protezione
                    parts = clean_tag.rsplit(" ", 1)  # Divide il nome della categoria dal suo numero d'indice
                    if len(parts) == 2:  # Se la divisione va a buon fine
                        label_name, index = parts  # Assegna le variabili
                        # Costruisce una Regex molto tollerante per trovare il tag anche se l'IA ci ha messo degli spazi extra in mezzo
                        pattern = rf'\[\s*{re.escape(label_name)}\s*[-_]?\s*{re.escape(index)}\s*\]'
                    else:  # Caso limite in cui il tag non abbia un indice numerico
                        pattern = rf'\[\s*{re.escape(clean_tag)}\s*\]'
                    # Sostituisce il Tag Regex trovato con il dato sensibile originale, ignorando Maiuscole/Minuscole
                    unmasked_text = re.sub(pattern, lambda _: original_val, unmasked_text, flags=re.IGNORECASE)
                
                if unmasked_text != raw_text:  # Se il testo ha subito modifiche (ovvero ha ripristinato dei dati)
                    self.last_processed_text = unmasked_text  # Registra il nuovo testo per impedire loop infiniti
                    try:
                        pyperclip.copy(unmasked_text)  # Sovrascrive gli appunti inserendo il testo in chiaro pronto da incollare!
                        self.log("Testo de-anonimizzato e ripristinato negli appunti.")  # Conferma in console
                    except pyperclip.PyperclipException:
                        self.log("Errore: Impossibile sovrascrivere gli appunti.")
                    return  # Ferma qui la funzione: essendo un ripristino, NON deve fare l'anonimizzazione sottostante.

            # ==== FASE 2: ANONIMIZZAZIONE (CENSURA) ====
            # Questa fase si avvia solo se il testo copiato è un nuovo testo "in chiaro" (o privo di tag della sessione corrente)
            self.reset_session()  # Azzera completamente la memoria della precedente sessione per far ripartire i contatori da 1
            masked, session_map = self.engine.mask(raw_text)  # Passa il testo al motore che cerca i dati sensibili
            
            if session_map:  # Se la mappa non è vuota (quindi ha trovato e censurato qualcosa)
                self.last_session_map = session_map  # Salva la nuova chiave di decriptazione nella memoria RAM
                self.last_processed_text = masked  # Registra il testo risultante oscurato
                try:
                    pyperclip.copy(masked)  # Sovrascrive gli appunti copiandoci il testo pieno di [Tag]
                    self.log(f"Elaborazione completata: protetti {len(session_map)} dati.")  # Mostra la quantità di dati blindati
                except pyperclip.PyperclipException:
                    self.log("Errore: Impossibile sovrascrivere gli appunti.")

        except Exception as e:  # Gestore globale di crash in fase di lettura/scrittura
            self.log(f"Errore imprevisto: {e}")
        finally:  # Avviene a prescindere da successi o errori
            self.lock.release()  # Rilascia il lucchetto, permettendo al sistema di elaborare un nuovo 'Ctrl+C'

if __name__ == "__main__":  # Controlla che questo file sia eseguito come programma principale e non importato come modulo
    controller = CTRLController()  # Crea l'istanza universale del Controller
    stop_event = threading.Event()  # Inizializza l'evento semaforico per permettere la chiusura sicura dei Thread in background
    
    # Stampa l'intestazione grafica e le istruzioni utente nel terminale
    print("\n=======================================================")
    print(" C.T.R.L. - Censor Text Restore Logic (Background Mode)")
    print("=======================================================")
    print("Stato: ATTIVO (con IA Potenziata e Auto-Reset Sessioni).")
    print("  • Premi 'Ctrl+C' per anonimizzare/ripristinare il testo negli appunti.")
    print("  • Premi 'Esc' per uscire dal programma.\n")

    def stop_program():  # Funzione triggerata dal tasto ESC
        print("\n[ESC] Chiusura del programma in corso...")  # Avviso utente
        stop_event.set()  # Sblocca il semaforo causando la terminazione a catena dei processi

    def start_listener():  # Funzione destinata a girare in background per ascoltare i tasti globali
        try:
            # Apre il listener della tastiera, associando 'Ctrl+C' al processamento appunti e 'ESC' all'uscita
            with keyboard.GlobalHotKeys({'<ctrl>+c': controller.process_clipboard, '<esc>': stop_program}) as listener:
                stop_event.wait()  # Blocca questo thread in attesa finché non viene premuto ESC (che setta lo stop_event)
                listener.stop()  # Quando riceve il segnale, spegne il listener fisicamente
        except Exception as e:
            print(f"Errore listener tastiera: {e}")  # Gestione errori di permessi per la lettura della tastiera

    # Avvia il listener in un "Thread Daemon" separato, così non blocca l'esecuzione del resto del codice
    listener_thread = threading.Thread(target=start_listener, daemon=True)
    listener_thread.start()  # Fa partire l'ascolto

    try:
        stop_event.wait()  # Blocca il Thread principale affinché la finestra del terminale non si chiuda istantaneamente
    except KeyboardInterrupt:  # Intercetta il comando di chiusura brutale (es. Ctrl+C premuto a lungo nel terminale)
        print("\nChiusura richiesta...")
    
    print("Arresto completato con successo.")  # Messaggio di addio
    sys.exit(0)  # Comando terminale che killa il processo, libera la RAM e chiude l'istanza Python