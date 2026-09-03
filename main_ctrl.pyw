import time
import sys
import threading
import re
import pyperclip
from pynput import keyboard
import pystray
from PIL import Image, ImageDraw

# Importa la classe del motore di anonimizzazione sviluppata nel file ctrl_engine.py
from ctrl_engine import CTRLEngine


class CTRLController:
    def __init__(self):
        self.engine = CTRLEngine()
        self.last_session_map = {}
        self.last_processed_text = ""
        self.is_active = False  
        self.lock = threading.Lock()
        self.tray_icon = None
        self.listener = None
        
        # --- SCORCIATOIA FISSA ---
        # Puoi cambiare '<ctrl>+c' con qualsiasi combinazione, es: '<ctrl>+<shift>+x'
        self.current_hotkey = '<ctrl>+c' 
        
        # --- OTTIMIZZAZIONE ICONA ---
        # Carica il file JPG una sola volta all'avvio e lo tiene pronto in RAM
        try:
            raw_image = Image.open("Gemini_Generated_Image_t6hhm7t6hhm7t6hh_2.jpg").convert("RGBA")
        except Exception:
            # Fallback in caso di immagine mancante
            raw_image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
            draw_fallback = ImageDraw.Draw(raw_image)
            draw_fallback.rectangle([8, 8, 56, 56], fill=(40, 40, 40, 255))

        # Ridimensiona l'immagine base e la salva in memoria
        self.base_image = raw_image.resize((64, 64), Image.Resampling.LANCZOS)

    def log(self, message: str):
        print(f"[{time.strftime('%H:%M:%S')}] {message}")

    def create_tray_image(self) -> Image.Image:
        # Lavora direttamente sull'immagine pre-caricata in RAM (Nessun caricamento dal disco!)
        img = self.base_image.copy()
        draw = ImageDraw.Draw(img)

        # Disegna il pallino di stato
        dot_color = (0, 230, 118, 255) if self.is_active else (255, 23, 68, 255)
        draw.ellipse([44, 44, 60, 60], fill=dot_color, outline=(20, 20, 20, 255), width=2)

        return img

    def toggle_state(self, icon=None, item=None):
        self.is_active = not self.is_active
        if self.tray_icon:
            self.tray_icon.icon = self.create_tray_image()
        
        stato_str = "ATTIVO" if self.is_active else "IN PAUSA"
        self.log(f"Sistema {stato_str}.")

    def start_hotkey_listener(self):
        if self.listener is not None:
            self.listener.stop()

        try:
            self.listener = keyboard.GlobalHotKeys({
                self.current_hotkey: self.process_clipboard
            })
            self.listener.start()
            self.log(f"Listener tastiera in ascolto su: {self.current_hotkey}")
        except Exception as e:
            self.log(f"[Errore Listener] Impossibile avviare la combinazione: {e}")

    def reset_session(self):
        self.last_session_map.clear()
        self.last_processed_text = ""

    def read_clipboard_smart(self, max_attempts=15) -> str:
        for _ in range(max_attempts):
            try:
                current = pyperclip.paste()
                if current and isinstance(current, str) and current != self.last_processed_text:
                    return current
            except Exception:
                pass
            time.sleep(0.01)
        return pyperclip.paste()

    def process_clipboard(self):
        if not self.is_active:
            return

        if not self.lock.acquire(blocking=True, timeout=0.5):
            return

        try:
            raw_text = self.read_clipboard_smart()
            if not raw_text or not raw_text.strip():
                return

            # FASE 1: RIPRISTINO
            has_valid_tags = False
            if self.last_session_map:
                has_valid_tags = any(tag in raw_text for tag in self.last_session_map.keys())

            if has_valid_tags:
                unmasked_text = raw_text
                for placeholder, original_val in self.last_session_map.items():
                    if placeholder in unmasked_text:
                        unmasked_text = unmasked_text.replace(placeholder, original_val)

                if unmasked_text != raw_text:
                    self.last_processed_text = unmasked_text
                    pyperclip.copy(unmasked_text)
                    self.log("✅ Testo ripristinato con successo.")
                    return

            if raw_text == self.last_processed_text:
                return

            # FASE 2: CENSURA
            self.reset_session()
            masked, session_map = self.engine.mask(raw_text)

            if session_map:
                self.last_session_map = session_map
                self.last_processed_text = masked
                pyperclip.copy(masked)
                self.log(f"🛡️ Dati protetti: {len(session_map)}")
            else:
                self.last_processed_text = raw_text

        except Exception as e:
            self.log(f"[Errore] Imprevisto: {e}")
        finally:
            self.lock.release()


if __name__ == "__main__":
    controller = CTRLController()
    
    print("\n========================================================")
    print(" C.T.R.L. - Sistema Avviato (Ottimizzato)")
    print("========================================================")

    def stop_program(icon=None, item=None):
        print("\n[Chiusura] Arresto dell'applicazione in corso...")
        if controller.listener:
            controller.listener.stop()
        if controller.tray_icon:
            controller.tray_icon.stop()

    controller.start_hotkey_listener()

    # Menu ultra-semplificato
    tray_menu = pystray.Menu(
        pystray.MenuItem("▶/⏸ Attiva o Metti in Pausa", controller.toggle_state, default=True),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("⏏ Chiudi programma", stop_program)
    )

    controller.tray_icon = pystray.Icon(
        name="CTRL_Background",
        icon=controller.create_tray_image(),
        title="C.T.R.L.",
        menu=tray_menu
    )

    try:
        controller.tray_icon.run()  
    except KeyboardInterrupt:
        stop_program()