"""
Application web Streamlit pour l'agent de voyage intelligent
Interface moderne avec chat, préférences et visualisations
"""

import streamlit as st
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Configuration de la page
st.set_page_config(
    page_title="✈️ Travel Agent Pro",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé pour un design moderne
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    .preference-section {
        background: white;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        border-left: 4px solid #667eea;
    }
    div[data-testid="stExpander"] {
        background: white;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    </style>
""", unsafe_allow_html=True)

load_dotenv()

# Import de l'agent et des outils
from agents.travel_agent_claude import ClaudeTravelAgent
from agents.travel_agent_gemini import GeminiTravelAgent
from agents.model_factory import ModelProvider
from tools import (
    search_flights, search_hotels, search_vacation_rentals,
    find_nearby_attractions, find_cultural_activities,
    recommend_restaurants, create_visit_itinerary,
    generate_travel_map, calculate_total_cost, get_destination_context,
    recommend_best_package, get_airport_code
)


@st.cache_resource
def create_agent(_model_provider):
    """Créer l'agent selon le provider choisi (mis en cache pour performance)"""
    tools = [
        get_airport_code,  # Nouvel outil en premier
        search_flights, search_hotels, search_vacation_rentals,
        find_nearby_attractions, find_cultural_activities,
        recommend_restaurants, create_visit_itinerary,
        generate_travel_map, calculate_total_cost, get_destination_context,
        recommend_best_package
    ]
    
    if _model_provider == "claude":
        return ClaudeTravelAgent(tools=tools, temperature=0.5)
    else:  # gemini
        return GeminiTravelAgent(tools=tools, temperature=0.5)


def initialize_session_state():
    """Initialiser l'état de la session"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'model_provider' not in st.session_state:
        st.session_state.model_provider = "gemini"  # Gemini 2.0 Flash: rapide et économique
    if 'agent' not in st.session_state:
        st.session_state.agent = create_agent(st.session_state.model_provider)
    if 'trip_data' not in st.session_state:
        st.session_state.trip_data = {}


def _render_chat_interface():
    """Rendre l'interface de chat"""
    # Initialisation explicite et forcée de la session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'model_provider' not in st.session_state:
        st.session_state.model_provider = "gemini"
    if 'trip_data' not in st.session_state:
        st.session_state.trip_data = {}
    
    # Forcer la création de l'agent si absent - CREATION DIRECTE sans cache
    if 'agent' not in st.session_state or st.session_state.agent is None:
        tools = [
            get_airport_code, search_flights, search_hotels, search_vacation_rentals,
            find_nearby_attractions, find_cultural_activities,
            recommend_restaurants, create_visit_itinerary,
            generate_travel_map, calculate_total_cost, get_destination_context,
            recommend_best_package
        ]
        if st.session_state.model_provider == "claude":
            st.session_state.agent = ClaudeTravelAgent(tools=tools, temperature=0.5)
        else:
            st.session_state.agent = GeminiTravelAgent(tools=tools, temperature=0.5)
    
    st.markdown("### 💬 Discutez avec votre agent de voyage")
    
    # Afficher l'historique des messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Input utilisateur
    if prompt := st.chat_input("Posez votre question (ex: 'Je veux aller à Osaka en septembre')"):
        # Ajouter le message utilisateur
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Ajouter les préférences comme CONTEXTE DISPONIBLE (pas comme instructions forcées)
        # L'agent décide lui-même ce qui est pertinent selon la demande
        departure_str = st.session_state.departure.strftime('%d/%m/%Y')
        return_str = st.session_state['return'].strftime('%d/%m/%Y')
        cultural_prefs = ', '.join(st.session_state.cultural) if st.session_state.cultural else 'art, histoire'
        cuisine_prefs = ', '.join(st.session_state.cuisine) if st.session_state.cuisine else 'cuisine locale'
        
        enriched_prompt = f"""DEMANDE UTILISATEUR:
{prompt}

CONTEXTE DISPONIBLE (utilise si pertinent):
- Profil: {st.session_state.travelers} voyageur(s), départ {st.session_state.origin}
- Dates configurées: {departure_str} → {return_str}
- Destination pré-remplie: {st.session_state.get('destination', 'non définie')}
- Intérêts: {cultural_prefs}
- Cuisine: {cuisine_prefs} ({st.session_state.budget})

💡 Consigne: Privilégie les détails explicites de la demande. Utilise le contexte seulement pour compléter ce qui manque."""
        
        # Réponse de l'agent
        with st.chat_message("assistant"):
            # Conteneur pour afficher la progression
            status_container = st.empty()
            
            try:
                # Afficher progression pendant l'attente
                progress_text = "🔍 Recherche en cours... Patience, l'agent collecte des données réelles (vols, hôtels, activités)"
                status_container.info(progress_text)
                
                # Progress bar pour montrer que ça travaille
                progress_bar = st.progress(0)
                
                # Lancer l'agent dans un thread pour pouvoir afficher la progression
                import threading
                import time
                
                # Capturer l'agent AVANT le thread pour éviter les problèmes de session state
                agent = st.session_state.agent
                
                result = {"response": None, "error": None, "duration": 0}
                
                def run_agent():
                    try:
                        start = time.time()
                        result["response"] = agent.plan_trip(enriched_prompt)
                        result["duration"] = time.time() - start
                    except Exception as e:
                        result["error"] = str(e)
                
                # Démarrer l'agent
                agent_thread = threading.Thread(target=run_agent)
                agent_thread.start()
                
                # Animer la progress bar pendant que l'agent travaille
                progress = 0
                while agent_thread.is_alive():
                    progress = min(progress + 0.01, 0.95)  # Max 95% jusqu'à la fin
                    progress_bar.progress(progress)
                    time.sleep(0.5)
                
                agent_thread.join()
                progress_bar.progress(1.0)
                
                # Vérifier les résultats
                if result["error"]:
                    raise Exception(result["error"])
                
                response = result["response"]
                duration = result["duration"]
                
                # Effacer le statut et la progress bar
                status_container.empty()
                progress_bar.empty()
                
                if response:
                    # Afficher la réponse dans le chat (pas dans un empty())
                    st.markdown(response)
                    st.caption(f"⏱️ Temps de traitement: {duration:.1f}s")
                    st.session_state.messages.append({"role": "assistant", "content": response})
                else:
                    st.warning("⚠️ Aucune réponse reçue de l'agent")
                
                
                # Détecter et afficher automatiquement la carte si elle a été générée
                import os
                import glob
                
                # Chercher tous les fichiers HTML récemment créés (dernière minute)
                html_files = glob.glob(os.path.join(os.getcwd(), '*travel_map.html'))
                if html_files:
                    # Prendre le plus récent
                    latest_map = max(html_files, key=os.path.getmtime)
                    import time
                    # Vérifier si créé dans les 2 dernières minutes
                    if time.time() - os.path.getmtime(latest_map) < 120:
                        st.divider()
                        st.subheader("🗺️ Carte interactive de votre voyage")
                        with open(latest_map, 'r', encoding='utf-8') as f:
                            map_html = f.read()
                        st.components.v1.html(map_html, height=600, scrolling=True)
                        st.caption(f"📁 Carte sauvegardée: {os.path.basename(latest_map)}")
                        
            except Exception as e:
                status_container.empty()
                error_msg = f"❌ Erreur: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                
                # Afficher le traceback complet pour debug
                import traceback
                with st.expander("🔍 Détails de l'erreur (debug)"):
                    st.code(traceback.format_exc())
    
    # Boutons d'action rapide
    st.divider()
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🗺️ Créer un itinéraire", use_container_width=True):
            if st.session_state.get('destination'):
                dest = st.session_state.destination
                days = (st.session_state['return'] - st.session_state.departure).days
                cultural_list = st.session_state.cultural + ['food', 'attractions']
                interests = ','.join(cultural_list)
                quick_prompt = f"Crée-moi un itinéraire de {days} jours à {dest} avec mes intérêts: {interests}"
                st.session_state.messages.append({"role": "user", "content": quick_prompt})
                st.rerun()
            else:
                st.warning("Veuillez d'abord définir une destination")
    
    with col2:
        if st.button("🍽️ Recommander des restaurants", use_container_width=True):
            if st.session_state.get('destination'):
                dest = st.session_state.destination
                cuisines = ', '.join(st.session_state.cuisine)
                quick_prompt = f"Recommande-moi des restaurants à {dest} (cuisine: {cuisines}, budget: {st.session_state.budget})"
                st.session_state.messages.append({"role": "user", "content": quick_prompt})
                st.rerun()
            else:
                st.warning("Veuillez d'abord définir une destination")
    
    with col3:
        if st.button("🎨 Trouver des activités", use_container_width=True):
            if st.session_state.get('destination'):
                dest = st.session_state.destination
                interests = ', '.join(st.session_state.cultural)
                quick_prompt = f"Trouve-moi des activités culturelles à {dest} (intérêts: {interests})"
                st.session_state.messages.append({"role": "user", "content": quick_prompt})
                st.rerun()
            else:
                st.warning("Veuillez d'abord définir une destination")
    
    with col4:
        if st.button("🔄 Nouvelle conversation", use_container_width=True):
            st.session_state.messages = []
            st.rerun()


def _render_trip_summary():
    """Afficher le résumé du voyage"""
    st.markdown("### 📊 Résumé de votre voyage")
    
    if st.session_state.get('destination'):
        # Cards avec informations du voyage
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class='metric-card'>
                <h3 style='color: #667eea; margin: 0;'>🎯 Destination</h3>
                <p style='font-size: 1.5em; font-weight: bold; margin: 10px 0;'>{}</p>
            </div>
            """.format(st.session_state.destination), unsafe_allow_html=True)
        
        with col2:
            days = (st.session_state['return'] - st.session_state.departure).days
            st.markdown("""
            <div class='metric-card'>
                <h3 style='color: #667eea; margin: 0;'>📅 Durée</h3>
                <p style='font-size: 1.5em; font-weight: bold; margin: 10px 0;'>{} jours</p>
            </div>
            """.format(days), unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class='metric-card'>
                <h3 style='color: #667eea; margin: 0;'>👥 Voyageurs</h3>
                <p style='font-size: 1.5em; font-weight: bold; margin: 10px 0;'>{}</p>
            </div>
            """.format(st.session_state.travelers), unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div class='metric-card'>
                <h3 style='color: #667eea; margin: 0;'>💰 Budget</h3>
                <p style='font-size: 1.5em; font-weight: bold; margin: 10px 0;'>{}</p>
            </div>
            """.format(st.session_state.budget), unsafe_allow_html=True)
        
        st.divider()
        
        # Informations détaillées
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🎨 Centres d'intérêt")
            for interest in st.session_state.cultural:
                st.markdown(f"- {interest.capitalize()}")
        
        with col2:
            st.markdown("#### 🍽️ Préférences culinaires")
            for cuisine in st.session_state.cuisine:
                st.markdown(f"- {cuisine.capitalize()}")
        
        st.divider()
        
        # Dates
        st.markdown("#### 📆 Planning")
        st.write(f"**Départ :** {st.session_state.departure.strftime('%d/%m/%Y')}")
        st.write(f"**Retour :** {st.session_state['return'].strftime('%d/%m/%Y')}")
        st.write(f"**Depuis :** {st.session_state.origin}")
        
    else:
        st.info("👆 Configurez d'abord votre voyage dans la barre latérale pour voir le résumé")
        st.markdown("""
        ### Comment utiliser Travel Agent Pro ?
        
        1. **Remplissez vos préférences** dans la barre latérale
        2. **Discutez avec l'agent** dans l'onglet Chat
        3. **Utilisez les boutons rapides** pour des actions courantes
        4. **Consultez ce résumé** pour voir votre plan de voyage
        """)


def _render_about_section():
    """Section À propos"""
    st.markdown("### ℹ️ À propos de Travel Agent Pro")
    
    st.markdown("""
    **Travel Agent Pro** est votre assistant voyage intelligent propulsé par l'intelligence artificielle.
    
    #### 🚀 Fonctionnalités
    
    - **Recherche de vols** en temps réel via SerpAPI (Google Flights)
    - **Hébergements variés** : hôtels classiques et locations Airbnb
    - **Activités culturelles** personnalisées selon vos goûts
    - **Restaurants** recommandés avec avis et photos (Travel Advisor API)
    - **Itinéraires sur mesure** jour par jour
    - **Cartes interactives** avec tous vos points d'intérêt
    - **Calculs de budget** automatiques
    
    #### 🔧 Technologies
    
    - **Claude AI (Anthropic)** : Agent conversationnel intelligent
    - **SerpAPI** : Données de vols en temps réel
    - **RapidAPI** : Locations Airbnb + Restaurants
    - **OpenStreetMap** : Géolocalisation et attractions
    - **Streamlit** : Interface web interactive
    - **LangChain** : Orchestration des outils IA
    
    #### 📊 Outils disponibles (9)
    
    1. `search_flights` - Recherche de vols
    2. `search_hotels` - Recherche d'hôtels
    3. `search_vacation_rentals` - Locations de vacances
    4. `find_nearby_attractions` - Lieux touristiques
    5. `find_cultural_activities` - Musées et galeries
    6. `recommend_restaurants` - Recommandations culinaires
    7. `create_visit_itinerary` - Planification jour par jour
    8. `generate_travel_map` - Carte interactive
    9. `calculate_total_cost` - Estimation budgétaire
    
    ---
    
    💡 **Astuce** : Plus vous remplissez vos préférences dans la barre latérale,
    plus les recommandations seront personnalisées !
    """)


def main():
    """Interface principale"""
    initialize_session_state()
    
    # En-tête avec design amélioré
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style='text-align: center; padding: 20px 0;'>
            <h1 style='color: #667eea; font-size: 3em; margin: 0;'>✈️ Travel Agent Pro</h1>
            <p style='color: #666; font-size: 1.2em;'>Votre assistant voyage intelligent propulsé par l'IA</p>
            <p style='color: #999; font-size: 0.9em;'>Claude AI • SerpAPI • RapidAPI • OpenStreetMap</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Création d'onglets pour une meilleure organisation
    tab1, tab2, tab3 = st.tabs(["💬 Chat Assistant", "📊 Résumé du voyage", "ℹ️ À propos"])
    
    with tab1:
        # Zone de chat principale
        _render_chat_interface()
    
    with tab2:
        # Résumé du voyage avec métriques
        _render_trip_summary()
    
    with tab3:
        # Informations sur l'application
        _render_about_section()
    
    # Sidebar avec préférences
    with st.sidebar:
        st.header("⚙️ Préférences de voyage")
        
        # ====== NOUVEAU: Sélection du modèle AI ======
        with st.expander("🤖 Modèle AI", expanded=True):
            model_choice = st.radio(
                "Choisissez votre modèle",
                options=["claude", "gemini"],
                format_func=lambda x: {
                    "claude": "🧠 Claude Sonnet 4 (Anthropic)",
                    "gemini": "⚡ Gemini 2.0 Flash (Google)"
                }[x],
                key="model_choice",
                help="Claude: Meilleur raisonnement, plus cher. Gemini: Rapide, 98% moins cher."
            )
            
            # Afficher les infos du modèle sélectionné
            if model_choice == "claude":
                st.info("""
                **Claude Sonnet 4**  
                💰 $0.069 / recherche  
                ✨ Raisonnement avancé  
                📊 Planification complexe
                """)
            else:
                st.success("""
                **Gemini 2.0 Flash**  
                💰 $0.0016 / recherche (-98%)  
                ⚡ Ultra rapide  
                🎯 Bon pour usage fréquent
                """)
            
            # Bouton pour changer de modèle
            if model_choice != st.session_state.model_provider:
                if st.button("🔄 Changer de modèle", use_container_width=True):
                    st.session_state.model_provider = model_choice
                    st.session_state.agent = create_agent(model_choice)
                    st.success(f"✅ Modèle changé: {model_choice.upper()}")
                    st.rerun()
        
        # Informations de base
        with st.expander("📋 Informations de base", expanded=True):
            origin = st.text_input("🛫 Ville de départ", value="Paris", key="origin")
            destination = st.text_input("🎯 Destination", value="", key="destination")
            
            col1, col2 = st.columns(2)
            with col1:
                default_departure = datetime.now() + timedelta(days=60)
                departure_date = st.date_input("📅 Départ", value=default_departure, key="departure")
            with col2:
                default_return = default_departure + timedelta(days=7)
                return_date = st.date_input("📅 Retour", value=default_return, key="return")
            
            travelers = st.number_input("👥 Nombre de voyageurs", min_value=1, max_value=10, value=2, key="travelers")
        
        # Préférences culturelles
        with st.expander("🎨 Préférences culturelles"):
            cultural_interests = st.multiselect(
                "Centres d'intérêt",
                ["art", "history", "science", "architecture", "performing_arts"],
                default=["art", "history"],
                key="cultural"
            )
            st.caption("Les musées et activités seront filtrés selon vos goûts")
        
        # Préférences culinaires
        with st.expander("🍽️ Préférences culinaires"):
            cuisine_types = st.multiselect(
                "Types de cuisine",
                ["local", "french", "italian", "asian", "american", "fusion"],
                default=["local"],
                key="cuisine"
            )
            budget_level = st.select_slider(
                "Budget restaurant",
                options=["$", "$$", "$$$", "$$$$"],
                value="$$",
                key="budget"
            )
            st.caption(f"$ = < 15€/pers | $$$$ = > 60€/pers")
        
        # Statistiques
        st.divider()
        st.markdown("### 📊 Système")
        
        # Afficher le modèle actif
        model_name = "Claude Sonnet 4" if st.session_state.model_provider == "claude" else "Gemini 2.0 Flash"
        st.info(f"🤖 **Modèle actif**: {model_name}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("🔧 Outils", "11")
        with col2:
            st.metric("🔌 APIs", "7")
        st.caption("🤖 Claude/Gemini  \n✈️ Amadeus  \n🏨 Booking.com  \n🏠 Airbnb  \n🗺️ OpenStreetMap")


if __name__ == "__main__":
    # Vérifier la clé API
    if not os.getenv("ANTHROPIC_API_KEY"):
        st.error("❌ ANTHROPIC_API_KEY manquante dans .env")
        st.stop()
    
    main()

