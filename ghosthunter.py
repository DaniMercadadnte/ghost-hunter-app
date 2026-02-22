import os
import sys
import time
import random
from datetime import datetime
from pathlib import Path

import streamlit as st
from instagrapi import Client
from instagrapi.exceptions import (
    TwoFactorRequired, 
    ChallengeRequired, 
    BadPassword, 
    FeedbackRequired, 
    LoginRequired,
    PleaseWaitFewMinutes, 
    RateLimitError, 
    SentryBlock
)

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Ghost Hunter Cloud", page_icon="👻", layout="wide")

# CSS PERSONALIZZATO PER EVITARE SCHERMATA NERA E MIGLIORARE L'UI
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stApp {
        background-color: #f5f7f9;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background-color: #0095f6;
        color: white;
        font-weight: bold;
        border: none;
    }
    .stTextInput>div>div>input {
        border-radius: 10px;
    }
    div.stExpander {
        border-radius: 10px;
        background-color: white;
    }
    /* Centrare il box di login */
    .login-box {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        background-color: white;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# PASSWORD PER ACCEDERE AL SITO
SITE_PASSWORD = "segreto_personale"

class InstagramCloudManager:
    def __init__(self):
        self.sessions_dir = "sessions"
        Path(self.sessions_dir).mkdir(exist_ok=True)
        if 'client' not in st.session_state:
            st.session_state.client = Client()
        self.client = st.session_state.client

    def get_session_file(self, username):
        return os.path.join(self.sessions_dir, f"{username}_session.json")

    def login(self, username, password, sessionid):
        status = st.empty()
        status.info("Connessione ai server Instagram...")
        
        session_file = self.get_session_file(username)
        success = False

        if sessionid:
            try:
                self.client.login_by_sessionid(sessionid)
                success = True
                status.success("Login tramite SessionID riuscito!")
            except Exception as e:
                st.warning(f"SessionID non valido: {e}")

        if not success and password:
            try:
                self.client.set_device({"app_version": "269.0.0.18.75", "android_version": 26, "android_release": "8.0.0", "dpi": "480dpi", "resolution": "1080x1920", "manufacturer": "Samsung", "device": "SM-G960F", "model": "Galaxy S9", "cpu": "exynos9810", "version_code": "314665256"})
                self.client.login(username, password)
                success = True
            except (TwoFactorRequired, ChallengeRequired):
                st.error("❌ Instagram richiede una verifica (2FA o Challenge). Usa il metodo Session ID.")
                return False
            except Exception as e:
                st.error(f"Errore Login: {e}")
                return False

        if success:
            st.session_state.user_id = self.client.user_id
            st.session_state.logged_in = True
            try:
                self.client.dump_settings(session_file)
            except: pass
            return True
        
        return False

    def process_data(self, auto_unfollow, limit_vip, log_container):
        try:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("Recupero lista Follower (Pazienta)...")
            time.sleep(random.uniform(3, 6))
            followers = self.client.user_followers(st.session_state.user_id)
            log_container.success(f"✅ Follower scaricati: {len(followers)}")
            
            status_text.text("Recupero lista Following...")
            time.sleep(random.uniform(5, 8))
            following = self.client.user_following(st.session_state.user_id)
            log_container.success(f"✅ Following scaricati: {len(following)}")

            follower_ids = set(followers.keys())
            following_ids = set(following.keys())
            ghost_ids = list(following_ids - follower_ids)
            total = len(ghost_ids)
            
            st.markdown(f"### 📊 Risultato: {total} persone non ti seguono")
            
            removed_count = 0
            
            for i, uid in enumerate(ghost_ids, 1):
                if uid not in following: continue
                
                user = following[uid]
                username = user.username
                action = "Analisi..."
                
                skip = False
                if limit_vip > 0:
                    try:
                        info = self.client.user_info(uid)
                        if info.follower_count > limit_vip:
                            action = f"🛡️ VIP SALVATO ({info.follower_count} fol.)"
                            skip = True
                    except: pass
                
                if not skip and auto_unfollow:
                    try:
                        wait = random.uniform(25, 55)
                        status_text.text(f"Pausa di sicurezza per @{username}: {int(wait)}s...")
                        time.sleep(wait)
                        
                        self.client.user_unfollow(uid)
                        action = "🗑️ UNFOLLOW EFFETTUATO"
                        removed_count += 1
                    except Exception:
                        action = f"❌ ERRORE API (Blocco temporaneo)"
                elif not skip:
                    action = "👻 GHOST RILEVATO"

                log_container.text(f"[{i}/{total}] @{username} -> {action}")
                progress_bar.progress(i/total)
                
            status_text.empty()
            st.success(f"✨ Operazione completata! Rimossi: {removed_count}")
            
        except Exception as e:
            st.error(f"Errore critico durante l'elaborazione: {e}")

def main():
    # --- LOGICA DI ACCESSO ---
    if 'site_access' not in st.session_state:
        st.session_state.site_access = False

    if not st.session_state.site_access:
        # Layout centrato per il login
        _, col_mid, _ = st.columns([1, 2, 1])
        with col_mid:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown("## 🔐 Ghost Hunter Access")
            pwd = st.text_input("Inserisci la Password del sito", type="password")
            if st.button("Sblocca Pannello"):
                if pwd == SITE_PASSWORD:
                    st.session_state.site_access = True
                    st.rerun()
                else:
                    st.error("Password errata.")
        return

    # --- APP REALE ---
    st.title("👻 Ghost Hunter Pro")
    manager = InstagramCloudManager()

    with st.sidebar:
        st.header("🔑 Login Instagram")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        sessionid = st.text_input("Session ID")

        with st.expander("❓ Guida al Session ID"):
            st.markdown("""
            1. Apri Instagram sul PC e loggati.
            2. Premi `F12`.
            3. Vai su **Application** -> **Cookies**.
            4. Seleziona `www.instagram.com`.
            5. Copia il valore di **sessionid**.
            """)
        
        if st.button("Esegui Connessione"):
            if username:
                if manager.login(username, password, sessionid):
                    st.success("Connesso!")
            else:
                st.error("Username obbligatorio.")

    if 'logged_in' in st.session_state and st.session_state.logged_in:
        st.info(f"Connesso come: **{username}**")
        
        col1, col2 = st.columns(2)
        with col1:
            auto_unfollow = st.checkbox("Abilita Unfollow Automatico", value=False)
        with col2:
            limit_vip = st.number_input("Soglia VIP (Protezione)", value=5000)
            
        if st.button("🚀 AVVIA SCANSIONE"):
            log_box = st.empty()
            manager.process_data(auto_unfollow, limit_vip, log_box)
    else:
        st.warning("Esegui il login dalla barra laterale.")

if __name__ == "__main__":
    is_streamlit_run = any("streamlit" in arg.lower() for arg in sys.argv)
    if not is_streamlit_run:
        print(f"\n👉  python -m streamlit run {os.path.basename(__file__)}\n")
    else:
        main()