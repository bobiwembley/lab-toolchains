"""
Exemple simple d'utilisation du mode chatbot
Démontre une conversation progressive sans l'interface complète
"""

from agents.travel_agent import TravelAgent
from agents.model_factory import ModelProvider
from tools.travel_tools import create_all_tools


def demo_chatbot():
    """Démonstration du mode chatbot avec une conversation scriptée"""
    
    print("="*70)
    print("🎬 DÉMONSTRATION DU MODE CHATBOT")
    print("="*70)
    print()
    
    # Initialiser l'agent
    print("⚙️  Initialisation de l'agent...")
    tools = create_all_tools()
    agent = TravelAgent(
        tools=tools,
        model_provider=ModelProvider.CLAUDE,
        temperature=0.5
    )
    print("✅ Agent prêt !\n")
    
    # Simulation d'une conversation progressive
    conversation = [
        "Bonjour !",
        "Je veux faire un voyage",
        "Au Japon",
        "Plus précisément à Tokyo",
        "En avril prochain",
    ]
    
    print("📝 Scénario: Conversation progressive où l'utilisateur affine sa demande\n")
    print("-"*70)
    
    for i, message in enumerate(conversation, 1):
        print(f"\n👤 Utilisateur [{i}]: {message}")
        print(f"   └─ Historique: {agent.get_conversation_length()} messages")
        
        response = agent.chat(message)
        
        # Afficher seulement les 200 premiers caractères de la réponse
        response_preview = response[:200] + "..." if len(response) > 200 else response
        print(f"\n🤖 Agent: {response_preview}")
        print("-"*70)
    
    print(f"\n📊 Statistiques finales:")
    print(f"   • Total de messages dans l'historique: {agent.get_conversation_length()}")
    print(f"   • Tours de conversation: {len(conversation)}")
    
    # Démonstration du reset
    print("\n🔄 Démonstration du reset...")
    agent.reset_conversation()
    print(f"   • Historique après reset: {agent.get_conversation_length()} messages")
    
    print("\n✅ Démonstration terminée !")


def demo_multi_turn_context():
    """Démonstration de la conservation du contexte"""
    
    print("\n" + "="*70)
    print("🎬 DÉMONSTRATION DU CONTEXTE MULTI-TOURS")
    print("="*70)
    print()
    
    tools = create_all_tools()
    agent = TravelAgent(
        tools=tools,
        model_provider=ModelProvider.CLAUDE,
        temperature=0.5
    )
    
    print("📝 Scénario: L'utilisateur fait référence aux messages précédents\n")
    print("-"*70)
    
    # Tour 1
    print("\n👤 Tour 1: Je veux aller à Tokyo")
    response1 = agent.chat("Je veux aller à Tokyo")
    print(f"🤖 Agent: [Réponse sur Tokyo]")
    
    # Tour 2 - Référence implicite
    print("\n👤 Tour 2: Quels sont les meilleurs quartiers ?")
    print("   (L'agent doit comprendre qu'on parle de Tokyo)")
    response2 = agent.chat("Quels sont les meilleurs quartiers ?")
    print(f"🤖 Agent: [Réponse sur les quartiers de Tokyo]")
    
    # Tour 3 - Autre référence
    print("\n👤 Tour 3: Et pour y aller ?")
    print("   (L'agent doit comprendre qu'on parle de transport vers Tokyo)")
    response3 = agent.chat("Et pour y aller ?")
    print(f"🤖 Agent: [Réponse sur le transport]")
    
    print(f"\n✅ Contexte maintenu sur {agent.get_conversation_length()} messages !")


if __name__ == "__main__":
    # Choisir quelle démo exécuter
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "context":
        demo_multi_turn_context()
    else:
        demo_chatbot()
        
        # Demander si on veut voir la démo du contexte
        print("\n💡 Pour voir la démo du contexte, lancez:")
        print("   python examples/demo_chatbot.py context")
