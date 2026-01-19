"""
Main script - Interface interactive du chatbot de voyage
Lance une boucle de conversation avec le TravelAgent
"""

import sys
from dotenv import load_dotenv

from agents.travel_agent import TravelAgent
from agents.model_factory import ModelProvider
from tools.travel_tools import create_all_tools
from utils.logger import ContextLogger

logger = ContextLogger(__name__)
load_dotenv()


def print_welcome():
    """Affiche le message de bienvenue"""
    print("\n" + "="*70)
    print("🌍  WELCOME TO YOUR PROFESSIONAL TRAVEL ASSISTANT  ✈️")
    print("="*70)
    print("\nJe suis votre assistant de voyage personnel.")
    print("Je peux vous aider à planifier votre prochain voyage !")
    print("\nCommandes spéciales:")
    print("  - 'exit' ou 'quit' : Quitter l'application")
    print("  - 'reset' : Recommencer une nouvelle conversation")
    print("  - 'history' : Afficher le nombre de messages dans l'historique")
    print("  - 'help' : Afficher cette aide")
    print("\nExemples de requêtes:")
    print("  - 'Je veux aller à Tokyo en avril'")
    print("  - 'Quelles sont les meilleures destinations en Europe pour l'été ?'")
    print("  - 'Peux-tu me proposer un voyage romantique pour 2 personnes ?'")
    print("\n" + "-"*70 + "\n")


def print_help():
    """Affiche l'aide"""
    print("\n📖 AIDE - Commandes disponibles:")
    print("  • exit / quit  : Quitter l'application")
    print("  • reset        : Recommencer une nouvelle conversation")
    print("  • history      : Voir le nombre de messages échangés")
    print("  • help         : Afficher cette aide\n")


def main():
    """Point d'entrée principal - Boucle d'interaction chatbot"""
    
    # Afficher le message de bienvenue
    print_welcome()
    
    # Demander le choix du modèle
    print("Quel modèle souhaitez-vous utiliser ?")
    print("1. Claude (Anthropic) - Recommandé")
    print("2. Gemini (Google Vertex AI)")
    
    while True:
        choice = input("\nVotre choix (1 ou 2) [défaut: 1]: ").strip()
        if choice == "" or choice == "1":
            model_provider = ModelProvider.CLAUDE
            break
        elif choice == "2":
            model_provider = ModelProvider.GEMINI
            break
        else:
            print("❌ Choix invalide. Veuillez entrer 1 ou 2.")
    
    # Demander le mode (rapide ou complet)
    print("\nMode de recherche :")
    print("1. ⚡ Rapide - Essentiels uniquement (25-30s)")
    print("2. 📋 Complet - Tous les détails (45-50s)")
    
    while True:
        mode_choice = input("\nVotre choix (1 ou 2) [défaut: 2]: ").strip()
        if mode_choice == "1":
            fast_mode = True
            print("✅ Mode rapide sélectionné")
            break
        elif mode_choice == "" or mode_choice == "2":
            fast_mode = False
            print("✅ Mode complet sélectionné")
            break
        else:
            print("❌ Choix invalide. Veuillez entrer 1 ou 2.")
    
    try:
        # Initialiser les outils
        print("\n⚙️  Initialisation des outils de voyage...")
        tools = create_all_tools()
        
        # Créer l'agent
        print(f"🤖 Initialisation de l'agent avec {model_provider.value}...")
        agent = TravelAgent(
            tools=tools,
            model_provider=model_provider,
            temperature=0.5,
            fast_mode=fast_mode
        )
        
        logger.info(
            "✅ Travel Assistant ready",
            model_provider=model_provider.value,
            tools_count=len(tools),
            fast_mode=fast_mode
        )
        
        mode_text = "rapide ⚡" if fast_mode else "complet 📋"
        print(f"\n✅ Agent initialisé avec succès ({model_provider.value} - mode {mode_text})")
        print("💬 Vous pouvez maintenant commencer à discuter !\n")
        
        # Boucle d'interaction principale
        while True:
            try:
                # Récupérer l'entrée utilisateur
                user_input = input("\n👤 Vous: ").strip()
                
                # Vérifier les commandes spéciales
                if not user_input:
                    continue
                    
                if user_input.lower() in ["exit", "quit", "q"]:
                    print("\n👋 Au revoir ! Bon voyage ! ✈️\n")
                    logger.info("Application closed by user")
                    break
                
                if user_input.lower() == "reset":
                    agent.reset_conversation()
                    print("\n🔄 Conversation réinitialisée. Nouvelle conversation démarrée.\n")
                    continue
                
                if user_input.lower() == "history":
                    history_length = agent.get_conversation_length()
                    print(f"\n📊 Historique: {history_length} messages dans la conversation actuelle.\n")
                    continue
                
                if user_input.lower() == "help":
                    print_help()
                    continue
                
                # Traiter la requête avec l'agent
                print("\n🤖 Agent: ", end="", flush=True)
                
                try:
                    response = agent.chat(user_input)
                    print(response)
                    
                except Exception as e:
                    logger.error(
                        "❌ Error during chat",
                        error=str(e),
                        error_type=type(e).__name__,
                        exc_info=True
                    )
                    print(f"\n❌ Erreur: {str(e)}")
                    print("💡 Essayez de reformuler votre question ou tapez 'reset' pour recommencer.\n")
            
            except KeyboardInterrupt:
                print("\n\n⚠️  Interruption détectée. Tapez 'exit' pour quitter proprement.")
                continue
    
    except Exception as e:
        logger.error(
            "❌ Fatal error during initialization",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )
        print(f"\n❌ Erreur fatale lors de l'initialisation: {str(e)}")
        print("Vérifiez votre configuration (API keys, etc.) et réessayez.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
