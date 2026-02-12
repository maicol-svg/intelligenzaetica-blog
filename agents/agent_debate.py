#!/usr/bin/env python3
"""
Sistema di Dibattito tra Agenti - IntelligenzaEtica.blog

Simula una discussione tra gli agenti IA su topic specifici per
migliorare il blog attraverso prospettive diverse.

Uso:
    python agent_debate.py --topic "Miglioramenti al design del sito"
    python agent_debate.py --topic "Strategia contenuti Q1 2026" --rounds 3
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import yaml

# Carica variabili d'ambiente
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).parent))

from utils.claude_client import ClaudeClient


# Prospettive degli agenti
AGENT_PERSPECTIVES = {
    "marco": {
        "name": "Marco",
        "role": "Giornalista IA - News & Sport",
        "focus": "engagement, SEO, trending topics, metriche di traffico",
        "style": "pragmatico e orientato ai risultati",
        "prompt": """Sei Marco, giornalista specializzato in News, Tech e Sport per IntelligenzaEtica.blog.
Il tuo focus principale è: engagement degli utenti, SEO, trending topics e metriche.
Quando parli, considera sempre:
- Come aumentare il traffico e l'engagement
- Quali argomenti sono di tendenza
- Come ottimizzare per i motori di ricerca
- Dati e metriche concrete quando possibile
Stile: pragmatico, diretto, orientato ai risultati."""
    },
    "elena": {
        "name": "Elena",
        "role": "Giornalista IA - Tutorial & Lifestyle",
        "focus": "user experience, accessibilità, valore pratico per gli utenti",
        "style": "empatica e attenta alle esigenze degli utenti",
        "prompt": """Sei Elena, giornalista specializzata in Tutorial, Lifestyle e Salute per IntelligenzaEtica.blog.
Il tuo focus principale è: user experience, accessibilità e valore pratico.
Quando parli, considera sempre:
- L'esperienza dell'utente finale
- L'accessibilità per tutti (inclusi utenti con disabilità)
- Il valore pratico e applicabile dei contenuti
- La chiarezza e semplicità della comunicazione
Stile: empatica, pratica, attenta ai dettagli."""
    },
    "luca": {
        "name": "Luca",
        "role": "Giornalista IA - Etica & Creatività",
        "focus": "qualità contenuti, etica, profondità e creatività",
        "style": "riflessivo e filosofico",
        "prompt": """Sei Luca, giornalista specializzato in Etica, Psicologia e Creatività per IntelligenzaEtica.blog.
Il tuo focus principale è: qualità dei contenuti, etica e profondità.
Quando parli, considera sempre:
- Le implicazioni etiche delle scelte
- La qualità e profondità dei contenuti
- L'impatto sulla società e sugli utenti
- L'originalità e la creatività
Stile: riflessivo, profondo, filosofico ma accessibile."""
    },
    "alessandro": {
        "name": "Alessandro",
        "role": "Quality Controller & Moderatore",
        "focus": "sintesi, qualità, coerenza e fattibilità",
        "style": "rigoroso ma costruttivo",
        "prompt": """Sei Alessandro, Quality Controller e moderatore del dibattito per IntelligenzaEtica.blog.
Il tuo ruolo è: sintetizzare le discussioni, verificare la coerenza e valutare la fattibilità.
Quando parli:
- Riassumi i punti di consenso e disaccordo
- Valuta la fattibilità delle proposte
- Proponi compromessi quando ci sono divergenze
- Mantieni il focus sull'obiettivo
Stile: rigoroso, imparziale, costruttivo."""
    }
}


def load_config() -> dict:
    """Carica la configurazione."""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def generate_agent_response(
    client: ClaudeClient,
    agent_key: str,
    topic: str,
    context: str,
    round_num: int
) -> str:
    """Genera la risposta di un agente."""
    agent = AGENT_PERSPECTIVES[agent_key]

    prompt = f"""{agent['prompt']}

TOPIC DEL DIBATTITO: {topic}

CONTESTO DELLA DISCUSSIONE:
{context if context else "Questo è l'inizio della discussione."}

ROUND: {round_num}

Esprimi la tua opinione sul topic in modo conciso (2-3 paragrafi).
Se è il round 1, introduci la tua posizione.
Se è un round successivo, rispondi ai punti sollevati dagli altri.
"""

    response = client.client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=500,
        temperature=0.7,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content[0].text


def generate_synthesis(
    client: ClaudeClient,
    topic: str,
    full_discussion: str
) -> str:
    """Alessandro sintetizza la discussione."""
    agent = AGENT_PERSPECTIVES["alessandro"]

    prompt = f"""{agent['prompt']}

TOPIC DEL DIBATTITO: {topic}

DISCUSSIONE COMPLETA:
{full_discussion}

Come moderatore, fornisci una SINTESI FINALE che includa:
1. **Punti di consenso**: Su cosa sono tutti d'accordo?
2. **Punti di divergenza**: Dove ci sono opinioni diverse?
3. **Raccomandazioni finali**: Quali azioni concrete suggerisci?
4. **Prossimi passi**: Cosa fare nell'immediato?

Sii conciso ma completo.
"""

    response = client.client.messages.create(
        model="claude-3-haiku-20240307",  # Usa Haiku per consistenza
        max_tokens=1000,
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content[0].text


def run_debate(topic: str, rounds: int = 2, save_output: bool = True):
    """Esegue il dibattito tra agenti."""

    print("=" * 70)
    print("DIBATTITO TRA AGENTI - IntelligenzaEtica.blog")
    print(f"Data: {datetime.now().strftime('%d %B %Y, %H:%M')}")
    print(f"Topic: {topic}")
    print(f"Round: {rounds}")
    print("=" * 70)

    client = ClaudeClient()

    # Agenti partecipanti (escludiamo Alessandro che farà la sintesi)
    participants = ["marco", "elena", "luca"]

    full_discussion = ""
    debate_output = f"# Dibattito: {topic}\n\n"
    debate_output += f"**Data:** {datetime.now().strftime('%d %B %Y, %H:%M')}\n\n"
    debate_output += "---\n\n"

    for round_num in range(1, rounds + 1):
        print(f"\n--- ROUND {round_num} ---\n")
        debate_output += f"## Round {round_num}\n\n"

        round_context = full_discussion

        for agent_key in participants:
            agent = AGENT_PERSPECTIVES[agent_key]
            print(f"{agent['name']} ({agent['role']}):")

            try:
                response = generate_agent_response(
                    client, agent_key, topic, round_context, round_num
                )

                print(f"{response}\n")

                full_discussion += f"\n### {agent['name']}:\n{response}\n"
                debate_output += f"### {agent['name']}\n\n{response}\n\n"

            except Exception as e:
                print(f"Errore generando risposta per {agent['name']}: {e}")
                continue

    # Sintesi finale di Alessandro
    print("\n--- SINTESI FINALE (Alessandro) ---\n")
    debate_output += "---\n\n## Sintesi Finale (Alessandro - Moderatore)\n\n"

    try:
        synthesis = generate_synthesis(client, topic, full_discussion)
        print(synthesis)
        debate_output += synthesis + "\n"
    except Exception as e:
        print(f"Errore generando sintesi: {e}")
        synthesis = "Errore nella generazione della sintesi."

    print("\n" + "=" * 70)
    print("DIBATTITO COMPLETATO")
    print("=" * 70)

    # Salva output
    if save_output:
        output_path = Path(__file__).parent / "debate_output.md"
        output_path.write_text(debate_output, encoding="utf-8")
        print(f"\nOutput salvato: {output_path}")

    return {
        "topic": topic,
        "rounds": rounds,
        "discussion": full_discussion,
        "synthesis": synthesis,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Sistema di Dibattito tra Agenti IA"
    )
    parser.add_argument(
        "--topic",
        type=str,
        required=True,
        help="Topic da discutere"
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=2,
        help="Numero di round di discussione (default: 2)"
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Non salvare l'output su file"
    )

    args = parser.parse_args()

    run_debate(
        topic=args.topic,
        rounds=args.rounds,
        save_output=not args.no_save
    )


if __name__ == "__main__":
    main()
