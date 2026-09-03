import re  # Importa il modulo delle espressioni regolari per la compilazione dei pattern di matching

# Blacklist globale contenente termini comuni italiani e inglesi da non scambiare mai per persone o aziende
GLOBAL_BLACKLIST = {
    # Termini burocratici, amministrativi e fiscali generali
    "codice", "fiscale", "cf", "iban", "partita", "iva", "vat", "email", "telefono", 
    "carta", "credito", "stato", "lavori", "server", "targa", "via", "piazza", 
    "fatturazione", "registrazione", "pratica", "protocollo", "dossier", "istanza",
    "documento", "allegato", "oggetto", "note", "invio", "inviare", "ricevuta",
    # Termini organizzativi, aziendali e ruoli generici
    "societa", "azienda", "spettabile", "egregio", "cortese", "cliente", "fornitore",
    "ufficio", "reparto", "direzione", "amministrazione", "sito", "web", "portale",
    # Termini inglesi comuni nell'IT e nella reportistica aziendale
    "company", "service", "support", "account", "user", "username", "password",
    "invoice", "order", "report", "system", "data", "file", "folder", "project"
}  # Definizione del set per ricerca ad altissima velocità O(1)

# Elenco completo ed esteso di titoli d'onore e professionali sia italiani che internazionali
TITLE_LIST = (
    r'Dott\.ssa|Dott\.?|Dottoressa|Dr\.ssa|Dr\.?|Prof\.ssa|Prof\.?|Avv\.?|Avvocato|'
    r'Ing\.?|Ingegnere|Arch\.?|Architetto|Geom\.?|Pres\.?|Presidente|Dir\.?|Direttore|'
    r'Gov\.?|Governatore|Gov|Sindaco|Assessore|Min\.?|Ministro|Cons\.?|Consigliere|'
    r'Sig\.na|Sig\.ra|Sig\.?|Signor|Signora|Signorina|Mr\.?|Mrs\.?|Ms\.?|Miss|'
    r'On\.?|Onorevole|Sen\.?|Senatore'
)  # Stringa contenente i prefissi professionali separati da OR quantificato

# Pattern per intercettare il nome completo sequenziale dopo il titolo d'onore
NAME_PATTERN = r'\s+[A-Za-zà-ÿ]+(?:[\'\s](?:di\s+|da\s+|de(?:l|ll\'|lla|i|gli|lle)?\s+|Mac|Mc|O\')?[A-Za-zà-ÿ]+)?'  # Cattura nomi semplici e composti con particelle patronimiche

# Pattern regex completo per Titoli + Nomi con flag case-insensitive esteso all'intero pattern
TITLES_REGEX = re.compile(r'\b(?:' + TITLE_LIST + r')' + NAME_PATTERN + r'(?!\w)', re.IGNORECASE)  # Compila il pattern assicurando confini di parola iniziali e finali

# Lista ordinata per priorità di contesa contenente tuple con Tag associato e Regex compilata
RIGID_PATTERNS = [
    # ------------------- 1. IDENTIFICATIVI HARDWARE, RETI E RETI AVANZATE -------------------
    (
        "IMEI",  # Tag di identificazione univoca dispositivi mobili
        re.compile(r'\b\d{15}\b')  # Corrisponde esattamente a 15 cifre numeriche contigue
    ),
    (
        "VIN",  # Tag per il numero di telaio dei veicoli
        re.compile(r'\b[A-HJ-NPR-Z0-9]{17}\b', re.IGNORECASE)  # Codice alfanumerico di 17 caratteri escludendo I, O, Q
    ),
    (
        "Indirizzo MAC",  # Tag per l'indirizzo fisico di rete
        re.compile(r'\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b', re.IGNORECASE)  # 6 coppie esadecimali separate da due punti o trattino
    ),
    (
        "IPv6",  # Tag per indirizzi IP di nuova generazione
        re.compile(r'\b(?:[0-9a-fA-F]{1,4}:){1,7}:[0-9a-fA-F]{1,4}\b|\b(?:[0-9a-fA-F]{1,4}:){1,7}:|\b:(?::[0-9a-fA-F]{1,4}){1,7}\b', re.IGNORECASE)  # Struttura esadecimale IPv6 anche compressa
    ),
    (
        "Indirizzo IP",  # Tag per indirizzi IP v4
        re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b')  # 4 ottetti decimali da 0 a 255
    ),
    (
        "API Key",  # Tag per chiavi segrete ed authentication token
        re.compile(r'\b(?:sk_live_|pk_live_|api_key=|bearer\s+)[a-zA-Z0-9_\-]{16,}\b', re.IGNORECASE)  # Prefissi standard seguiti da stringa alfanumerica
    ),

    # ------------------- 2. IDENTIFICATIVI PERSONALI, VEICOLI E FISCALI -------------------
    (
        "Codice Fiscale",  # Tag per il Codice Fiscale italiano
        re.compile(r'(?<![A-Z0-9])[A-Z]{6}\d{2}[A-EHLMPR-T]\d{2}[A-Z]\d{3}[A-Z](?![A-Z0-9])', re.IGNORECASE)  # Confini alfanumerici negativi per evitare falsi match su Hash
    ),
    (
        "Carta d'Identità",  # Tag per il numero di carta d'identità elettronica/cartacea
        re.compile(r'(?<![A-Z0-9])[A-Z]{2}\d{5}[A-Z]{2}(?![A-Z0-9])', re.IGNORECASE)  # 2 lettere, 5 cifre, 2 lettere isolate da confini negativi
    ),
    (
        "Targa",  # Tag per targhe automobilistiche italiane ed europee
        re.compile(r'(?<![A-Z0-9])[A-Z]{2}\s?\d{3}\s?[A-Z]{2}(?![A-Z0-9])', re.IGNORECASE)  # Formato AA000AA isolato negativamente da cifre o lettere
    ),

    # ------------------- 3. DATI FINANZIARI E AZIENDALI -------------------
    (
        "IBAN",  # Tag per coordinate bancarie IBAN
        re.compile(r'\bIT\d{2}[A-Z]\d{10}[0-9A-Z]{12}\b|\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){3,6}(?:\s?[A-Z0-9]{1,4})?\b', re.IGNORECASE)  # Formato italiano a 27 caratteri o internazionale a blocchi
    ),
    (
        "Carta di Credito",  # Tag per numeri di carte di pagamento con validazione prefissi
        re.compile(r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|6(?:011|5[0-9]{2})[0-9]{12}|3[47][0-9]{13}|(?:5[0678]\d{2}|6\d{3})\d{8,15})\b|\b(?:\d{4}[-\s]?){3}\d{4}\b', re.IGNORECASE)  # Validazione Visa, Mastercard, Amex, Maestro e raggruppamenti a 4 cifre
    ),
    (
        "Partita IVA",  # Tag per Partita IVA italiana ed europea
        re.compile(r'\b(?:P\.?\s*IVA|Partita\s+IVA|VAT)?\s*[:\.]?\s*(?:IT)?\d{11}\b', re.IGNORECASE)  # Prefisso IT esplicito o anticipato da keyword esplicita + 11 cifre
    ),
    (
        "Azienda",  # Tag per il riconoscimento di ragioni sociali e forme giuridiche
        re.compile(r'\b[A-Z0-9À-ÿ][A-Za-z0-9À-ÿ&\.\'-]+(?:\s+[A-Za-z0-9À-ÿ&\.\'-]+){0,4}\s+(?:S\.r\.l\.s\.|S\.p\.A\.|S\.r\.l\.|S\.n\.c\.|S\.a\.s\.|S\.u\.r\.l\.|S\.a\.p\.a\.|Soc\.?\s*Coop\.?|SpA|Srls|Srl|Surl|Snc|Sas|GmbH|LLC|Ltd|Inc\.?)(?!\w)', re.IGNORECASE)  # Ancorato ai suffissi societari per massimo 4-5 parole antecedenti
    ),

    # ------------------- 4. CONTATTI E CREDENZIALI -------------------
    (
        "Email",  # Tag per indirizzi di posta elettronica
        re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', re.IGNORECASE)  # Identifica la struttura standard utente@dominio.estensione
    ),
    (
        "Indirizzo",  # Tag per indirizzi fisici e viabilità
        re.compile(r'\b(?:Via|Viale|Corso|Piazza|Piazzale|Largo|Vicolo|Strada|Borgo)\s+[A-Za-zàèéìòù\s\']+\s+\d{1,4}(?:[/\-][A-Za-z0-9]+)?(?:\s*,?\s*\d{5})?(?:\s+[A-Za-zàèéìòù\s\']+)?(?:\s*\([A-Z]{2}\))?\b', re.IGNORECASE)  # Qualificatore di strada seguito da nome, numero civico ed eventuale CAP/Provincia
    ),
    (
        "Telefono",  # Tag per numeri di rete fissa e mobile
        re.compile(r'\b(?:(?:\+|00)39\s?)?(?:3\d{2}[\s.-]?\d{6,7}|0\d{1,4}[\s.-]?\d{5,8})\b', re.IGNORECASE)  # Prefisso italiano +39, cellulari con 3 o numeri fissi con 0
    ),
    (
        "Credenziali",  # Tag per coppie o singole combinazioni di login e password
        re.compile(r'\b(?:Username|User|Password|Pass|Pwd)\s*:\s*[^\s,;\n]+', re.IGNORECASE)  # Intercetta parole chiave seguite da due punti e dal valore esatto fino a spazio/punteggiatura
    )
]  # Fine della struttura dei pattern rigidi