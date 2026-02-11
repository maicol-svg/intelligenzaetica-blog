#!/usr/bin/env python3
"""
Orchestrator per IntelligenzaEtica.blog
Gestisce il workflow completo di generazione e pubblicazione articoli.

Uso:
    python orchestrator.py generate --topic "Argomento" --category "tech"
    python orchestrator.py generate --topic "Argomento" --agent "luca"
    python orchestrator.py review --file "path/to/draft.md"
    python orchestrator.py publish --file "path/to/draft.md"
    python orchestrator.py list-drafts
    python orchestrator.py auto --count 2
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

import yaml

# Aggiungi il path per gli import locali
sys.path.insert(0, str(Path(__file__).parent))

from utils.claude_client import ClaudeClient
from utils.publisher import ArticlePublisher
from scheduler import PublishingScheduler


def load_config() -> dict:
    """Carica la configurazione dal file YAML."""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_agent_for_category(config: dict, category: str) -> str:
    """Determina l'agente appropriato per una categoria."""
    categories = config.get("categories", {})
    if category in categories:
        return categories[category].get("default_agent", "marco")
    return "marco"  # Default


def generate_article(
    topic: str,
    category: str,
    agent: str | None = None,
    context: str | None = None,
    as_draft: bool = True,
) -> Path:
    """
    Genera un nuovo articolo.

    Args:
        topic: Argomento dell'articolo
        category: Categoria dell'articolo
        agent: Nome dell'agente (opzionale, altrimenti usa default per categoria)
        context: Contesto aggiuntivo (es. fonte della notizia)
        as_draft: Se True, salva come bozza

    Returns:
        Path del file creato
    """
    config = load_config()
    client = ClaudeClient()
    publisher = ArticlePublisher()

    # Determina l'agente
    if not agent:
        agent = get_agent_for_category(config, category)

    agent_config = config["agents"].get(agent)
    if not agent_config:
        raise ValueError(f"Agente '{agent}' non trovato nella configurazione")

    print(f"📝 Generazione articolo con {agent_config['name']}...")
    print(f"   Argomento: {topic}")
    print(f"   Categoria: {category}")

    # Carica il prompt dell'agente
    agent_prompt = client.load_prompt(agent_config["prompt_file"])

    # Genera l'articolo
    article = client.generate_article(
        agent_prompt=agent_prompt,
        topic=topic,
        context=context,
        model="haiku",
        temperature=config["api"]["temperature"]["writer"],
    )

    # Salva l'articolo
    file_path = publisher.save_article(article, category=category, as_draft=as_draft)

    print(f"✅ Articolo salvato: {file_path}")
    return file_path


def review_article(file_path: Path, auto_fix: bool = True) -> dict:
    """
    Revisiona un articolo con l'editor Sofia.

    Args:
        file_path: Path dell'articolo da revisionare
        auto_fix: Se True, applica le correzioni automaticamente

    Returns:
        Risultato della revisione
    """
    config = load_config()
    client = ClaudeClient()
    publisher = ArticlePublisher()

    print(f"🔍 Revisione articolo: {file_path}")

    # Leggi l'articolo
    article = file_path.read_text(encoding="utf-8")

    # Carica il prompt dell'editor
    editor_prompt = client.load_prompt("prompts/sofia.md")

    # Revisiona
    result = client.edit_article(
        editor_prompt=editor_prompt,
        article=article,
        model="sonnet",
        temperature=config["api"]["temperature"]["editor"],
    )

    print(f"   Status: {result['status']}")
    print(f"   Quality Score: {result.get('quality_score', 'N/A')}/10")
    print(f"   SEO Score: {result.get('seo_score', 'N/A')}/10")

    if result.get("issues"):
        print("   Issues trovati:")
        for issue in result["issues"]:
            print(f"      - [{issue['severity']}] {issue['description']}")

    # Se approvato e auto_fix, aggiorna il file
    if auto_fix and result["status"] in ["approved", "needs_revision"]:
        revised = result.get("revised_article", article)
        if revised and revised != article:
            file_path.write_text(revised, encoding="utf-8")
            print(f"✅ Articolo aggiornato con le correzioni")

    if result["status"] == "needs_human_review":
        print(f"⚠️  Richiesta review umana: {result.get('human_review_reason', 'N/A')}")

    return result


def publish_article(file_path: Path, commit: bool = True) -> Path:
    """
    Pubblica un articolo (sposta da drafts a content e committa).

    Args:
        file_path: Path della bozza da pubblicare
        commit: Se True, committa e pusha su GitHub

    Returns:
        Path dell'articolo pubblicato
    """
    publisher = ArticlePublisher()

    print(f"📤 Pubblicazione articolo: {file_path}")

    # Pubblica
    published_path = publisher.publish_draft(file_path)
    print(f"✅ Articolo pubblicato: {published_path}")

    # Commit e push
    if commit:
        article_name = published_path.stem
        success = publisher.git_commit_and_push(
            f"content: Pubblica articolo '{article_name}'"
        )
        if success:
            print("✅ Modifiche pushate su GitHub")
        else:
            print("⚠️  Errore nel push su GitHub")

    return published_path


def list_drafts():
    """Elenca tutte le bozze disponibili."""
    publisher = ArticlePublisher()
    drafts = publisher.list_drafts()

    if not drafts:
        print("📭 Nessuna bozza trovata")
        return

    print(f"📋 Bozze disponibili ({len(drafts)}):")
    for draft in drafts:
        print(f"   - {draft.relative_to(publisher.drafts_path)}")


def auto_generate(count: int = 2, publish: bool = False):
    """
    Genera automaticamente articoli per diverse categorie.

    Args:
        count: Numero di articoli da generare
        publish: Se True, pubblica automaticamente dopo la revisione
    """
    config = load_config()

    # Topic di esempio (in produzione verrebbero da RSS o altre fonti)
    sample_topics = [
        {
            "topic": "Le nuove funzionalità di Claude 3.5 e come cambiano il modo di lavorare",
            "category": "tech",
        },
        {
            "topic": "Guida pratica: come creare presentazioni professionali con l'IA",
            "category": "tutorial",
        },
        {
            "topic": "L'impatto dell'IA generativa sulla creatività umana",
            "category": "ia-etica",
        },
        {
            "topic": "Come l'intelligenza artificiale sta rivoluzionando la finanza personale",
            "category": "finanza",
        },
        {
            "topic": "IA e benessere mentale: opportunità e rischi da conoscere",
            "category": "psicologia",
        },
        {
            "topic": "5 modi in cui l'IA aiuta a combattere il cambiamento climatico",
            "category": "ecosostenibile",
        },
    ]

    print(f"🤖 Generazione automatica di {count} articoli...")

    for i, topic_data in enumerate(sample_topics[:count]):
        print(f"\n--- Articolo {i + 1}/{count} ---")

        try:
            # Genera
            draft_path = generate_article(
                topic=topic_data["topic"],
                category=topic_data["category"],
                as_draft=True,
            )

            # Revisiona
            review_result = review_article(draft_path, auto_fix=True)

            # Pubblica se richiesto e approvato
            if publish and review_result["status"] == "approved":
                publish_article(draft_path, commit=True)

        except Exception as e:
            print(f"❌ Errore: {e}")
            continue

    print("\n✅ Generazione completata!")


def main():
    parser = argparse.ArgumentParser(
        description="Orchestrator per IntelligenzaEtica.blog"
    )
    subparsers = parser.add_subparsers(dest="command", help="Comando da eseguire")

    # Comando: generate
    gen_parser = subparsers.add_parser("generate", help="Genera un nuovo articolo")
    gen_parser.add_argument("--topic", "-t", help="Argomento dell'articolo (se omesso, prende dallo scheduler)")
    gen_parser.add_argument(
        "--category",
        "-c",
        choices=["ia-etica", "tech", "tutorial", "finanza", "psicologia", "ecosostenibile"],
        help="Categoria dell'articolo (se omesso, prende dallo scheduler)",
    )
    gen_parser.add_argument("--agent", "-a", help="Agente da usare (opzionale)")
    gen_parser.add_argument("--context", help="Contesto aggiuntivo")
    gen_parser.add_argument(
        "--publish", action="store_true", help="Pubblica direttamente"
    )
    gen_parser.add_argument(
        "--from-scheduler", action="store_true", help="Usa lo scheduler per determinare cosa generare"
    )

    # Comando: review
    rev_parser = subparsers.add_parser("review", help="Revisiona un articolo")
    rev_parser.add_argument("--file", "-f", help="Path dell'articolo (se omesso, revisiona tutti i drafts)")
    rev_parser.add_argument(
        "--no-fix", action="store_true", help="Non applicare correzioni automatiche"
    )

    # Comando: publish
    pub_parser = subparsers.add_parser("publish", help="Pubblica un articolo")
    pub_parser.add_argument("--file", "-f", help="Path della bozza (se omesso, pubblica tutti gli approvati)")
    pub_parser.add_argument(
        "--no-commit", action="store_true", help="Non committare su GitHub"
    )

    # Comando: list-drafts
    subparsers.add_parser("list-drafts", help="Elenca le bozze disponibili")

    # Comando: auto
    auto_parser = subparsers.add_parser(
        "auto", help="Genera automaticamente articoli"
    )
    auto_parser.add_argument(
        "--count", "-n", type=int, default=2, help="Numero di articoli"
    )
    auto_parser.add_argument(
        "--publish", action="store_true", help="Pubblica automaticamente"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "generate":
        topic = args.topic
        category = args.category
        agent = args.agent

        # Se mancano topic o category, usa lo scheduler
        if not topic or not category:
            scheduler = PublishingScheduler()
            next_article = scheduler.get_next_article_to_generate()

            if next_article:
                if not category:
                    category = next_article.get("categoria")
                if not topic:
                    topic = next_article.get("topic")
                if not agent:
                    agent = next_article.get("agente")
                print(f"📅 Usando scheduler: {category} -> {agent}")
            else:
                print("❌ Nessun articolo programmato e nessun topic fornito")
                return

        if not topic:
            print("❌ Topic richiesto (--topic) o non disponibile nello scheduler")
            return

        generate_article(
            topic=topic,
            category=category,
            agent=agent,
            context=args.context,
            as_draft=not args.publish,
        )

    elif args.command == "review":
        if args.file:
            review_article(Path(args.file), auto_fix=not args.no_fix)
        else:
            # Revisiona tutti i drafts
            publisher = ArticlePublisher()
            drafts = publisher.list_drafts()
            if not drafts:
                print("📭 Nessuna bozza da revisionare")
            else:
                print(f"🔍 Revisione di {len(drafts)} bozze...")
                for draft in drafts:
                    try:
                        review_article(draft, auto_fix=not args.no_fix)
                    except Exception as e:
                        print(f"❌ Errore revisione {draft}: {e}")

    elif args.command == "publish":
        if args.file:
            publish_article(Path(args.file), commit=not args.no_commit)
        else:
            # Pubblica tutti i drafts approvati (dopo review)
            publisher = ArticlePublisher()
            drafts = publisher.list_drafts()
            if not drafts:
                print("📭 Nessuna bozza da pubblicare")
            else:
                print(f"📤 Pubblicazione di {len(drafts)} bozze...")
                for draft in drafts:
                    try:
                        publish_article(draft, commit=False)
                    except Exception as e:
                        print(f"❌ Errore pubblicazione {draft}: {e}")
                # Commit unico alla fine
                if not args.no_commit:
                    success = publisher.git_commit_and_push("content: Pubblicazione batch articoli")
                    if success:
                        print("✅ Modifiche pushate su GitHub")
                    else:
                        print("⚠️  Errore nel push su GitHub")

    elif args.command == "list-drafts":
        list_drafts()

    elif args.command == "auto":
        auto_generate(count=args.count, publish=args.publish)


if __name__ == "__main__":
    main()
