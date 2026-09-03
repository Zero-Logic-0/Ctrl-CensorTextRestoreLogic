import re  # Importa il modulo delle espressioni regolari per la manipolazione avanzata del testo
import sys  # Importa le funzionalità di sistema per l'interruzione pulita in caso di errori critici
import spacy  # Importa la libreria di elaborazione del linguaggio naturale (NLP)

# Importazione dei pattern compilati e delle strutture dati dal file di configurazione
from config_tags import GLOBAL_BLACKLIST, TITLES_REGEX, RIGID_PATTERNS


class CTRLEngine:
    # Classe principale del motore responsabile del parsing ibrido (Regex + NLP) e della mascheratura

    def __init__(self):
        # Inizializza il motore caricando la configurazione e il modello linguistico
        self.rigid_patterns = RIGID_PATTERNS  # Assegna la lista delle regex rigide precompilate
        self.titles_regex = TITLES_REGEX  # Assegna la regex compilata per il matching dei titoli professionali
        self.blacklist = GLOBAL_BLACKLIST  # Assegna il set di blacklist per il filtraggio rapido
        
        try:
            # Tenta il caricamento del modello linguistico italiano avanzato di spaCy
            self.nlp = spacy.load("it_core_news_lg")  # Carica il modello grande per la massima accuratezza NLP
        except OSError:
            # Eccezione sollevata se il modello non risulta installato nell'ambiente Python
            print("\n[ERRORE CRITICO] Modello spaCy 'it_core_news_lg' non trovato!")  # Notifica l'errore all'utente
            print("Esegui il seguente comando nel terminale: python -m spacy download it_core_news_lg\n")  # Istruzione di ripristino
            sys.exit(1)  # Chiusura immediata dell'applicazione per mancanza di dipendenze fondamentali

    def mask(self, text: str) -> tuple[str, dict]:
        # Metodo principale per l'anonimizzazione del testo e la generazione della mappa di ripristino
        
        if not text or len(text) > 100000:
            # Check di sicurezza per evitare blocchi della memoria su testi nulli o troppo lunghi (>100KB)
            return text, {}  # Ritorna il testo inalterato e una mappa di sessione vuota

        sanitized_text = text  # Copia del testo originale su cui verranno applicati i rimpiazzi
        session_map = {}  # Dizionario che memorizzerà il mapping { '[Tag N]': 'Valore_Originale' }
        counters = {}  # Dizionario contatore per numerare i tag progressivamente per ogni categoria
        unique_matches = {}  # Mappa ausiliaria per eliminare duplicati e assegnare categorie { 'Valore': 'Tag_Nome' }

        def get_tag(category_name: str) -> str:
            # Funzione helper interna per formattare e incrementare i tag numerati
            counters[category_name] = counters.get(category_name, 0) + 1  # Incrementa il contatore per la categoria specificata
            return f"[{category_name} {counters[category_name]}]"  # Ritorna la stringa formattata es. [Utente 1]

        try:
            # ------------------- 1. RICONOSCIMENTO TRAMITE REGEX RIGIDE -------------------
            for label, pattern in self.rigid_patterns:
                # Scansiona tutte le regole rigide in ordine di priorità
                for m in pattern.finditer(sanitized_text):
                    # Cerca tutte le corrispondenze nel testo
                    val = m.group().strip()  # Estrae la stringa trovata rimuovendo spazi ai margini
                    if val and val not in unique_matches:
                        # Se il valore è valido e non ancora censurato da una regola a priorità superiore
                        unique_matches[val] = label  # Assegna la categoria corrispondente al valore

            # ------------------- 2. RICONOSCIMENTO TRAMITE TITOLI PROFESSIONALI -------------------
            for m in self.titles_regex.finditer(sanitized_text):
                # Cerca combinazioni di Titoli Professionali + Nome/Cognome
                val = m.group().strip()  # Estrae il nome completo preceduto dal titolo
                if val and val not in unique_matches:
                    # Registra la corrispondenza se non intercettata da regole precedenti
                    unique_matches[val] = "Contatto"  # Assegna la categoria 'Contatto'

            # ------------------- 3. ANALISI SEMANTICA NLP TRAMITE SPACY -------------------
            doc = self.nlp(sanitized_text)  # Analizza il testo con la pipeline NLP di spaCy
            for ent in doc.ents:
                # Cicla su tutte le entità nominate (NER) estratte dall'IA
                val = ent.text.strip()  # Normalizza il testo dell'entità trovata
                
                if not val or val in unique_matches:
                    # Salta entità vuote o già censurate da regex a priorità più alta
                    continue
                
                # FILTRAGGIO RIGOROSO BLACKLIST: Scarta l'entità SOLO SE coincide ESATTAMENTE con un elemento della blacklist
                if val.lower() in self.blacklist:
                    # Confronta la stringa intera convertita in minuscolo con gli elementi del set
                    continue  # Ignora l'entità poiché presente in blacklist
                
                if re.match(r'^\d+[\.\s]', val):
                    # Evita di mascherare elenchi puntati numerati che la NER potrebbe scambiare per entità
                    continue

                if ent.label_ == "PER" and len(val) > 2:
                    # Accetta persone e mononimi di lunghezza superiore a 2 caratteri
                    unique_matches[val] = "Utente"  # Assegna il tag 'Utente'
                elif ent.label_ == "ORG" and len(val.split()) <= 4:
                    # Accetta organizzazioni/aziende fluide composte da un massimo di 4 parole
                    unique_matches[val] = "Azienda"  # Assegna il tag 'Azienda'

        except Exception as e:
            # Gestione sicura delle eccezioni durante il processo di estrazione
            print(f"[Avviso CTRLEngine] Errore imprevisto durante l'analisi: {e}")  # Registra l'errore su console
            return text, {}  # Ritorna il testo originale senza modifiche per evitare danneggiamenti

        # Filtra i match validi rimuovendo eventuali valori che contengono già parentesi quadre per prevenire loop
        valid_matches = [(k, v) for k, v in unique_matches.items() if k and "[" not in k and "]" not in k]
        
        # ORDINAMENTO DECRESCENTE PER LUNGHEZZA: Previene il problema delle sottostringhe durante la sostituzione
        valid_matches.sort(key=lambda x: len(x[0]), reverse=True)  # Ordina dal testo più lungo a quello più corto

        # ------------------- 4. SOSTITUZIONE SICURA SUI CONFINI DI PAROLA -------------------
        for match_val, label in valid_matches:
            # Cicla sulle corrispondenze individuate ed ordinate
            if match_val in sanitized_text:
                # Verifica che il valore sia ancora presente nel testo aggiornato
                placeholder = get_tag(label)  # Genera un nuovo tag univoco es. [Utente 1]
                session_map[placeholder] = match_val  # Salva nel dizionario di sessione il mapping inverso
                
                # Sostituzione sicura ancorata esclusivamente ai confini di parola (\b) per evitare corruzioni
                pattern = rf'\b{re.escape(match_val)}\b'  # Escapa i caratteri speciali della stringa e impone \b
                sanitized_text = re.sub(pattern, placeholder, sanitized_text)  # Esegue la sostituzione accurata

        return sanitized_text, session_map  # Restituisce la coppia composta dal testo mascherato e la mappa di ripristino