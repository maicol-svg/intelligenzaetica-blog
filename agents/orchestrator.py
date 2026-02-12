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

Workflow con Quality Control:
    1. Giornalista scrive l'articolo
    2. Sofia (Editor) revisiona per stile e SEO
    3. Alessandro (QC) controlla qualità, fatti, date
    4. Se QC fallisce → torna al giornalista per revisione
    5. Ciclo si ripete max 3 volte
    6. Dopo 3 fallimenti → review umana
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
from utils.image_fetcher import ImageFetcher
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


def quality_control_article(
    article: str,
    client: ClaudeClient,
    config: dict,
) -> dict:
    """
    Esegue il controllo qualità su un articolo usando Alessandro.

    Args:
        article: Articolo da controllare
        client: Client Claude
        config: Configurazione

    Returns:
        Risultato del QC con decision, quality_score, blocking_issues, etc.
    """
    qc_config = config.get("quality_control", {})
    if not qc_config.get("enabled", True):
        # QC disabilitato, approva automaticamente
        return {
            "decision": "APPROVED",
            "quality_score": 8,
            "blocking_issues": [],
            "positive_aspects": ["Quality control disabilitato"],
            "summary": "Articolo approvato (QC disabilitato)."
        }

    # Carica il prompt di Alessandro
    qc_prompt = client.load_prompt("prompts/alessandro.md")

    # Data corrente per validazione temporale
    current_date = datetime.now().strftime("%d %B %Y")  # Es: "12 febbraio 2026"

    result = client.quality_control(
        qc_prompt=qc_prompt,
        article=article,
        current_date=current_date,
        model="sonnet",
        temperature=0.2,
    )

    return result


def revision_loop(
    article: str,
    agent: str,
    client: ClaudeClient,
    publisher: ArticlePublisher,
    config: dict,
) -> tuple[str, dict]:
    """
    Ciclo di revisione: se QC fallisce, manda al giornalista per correzioni.

    Args:
        article: Articolo da revisionare
        agent: Nome dell'agente giornalista originale
        client: Client Claude
        publisher: Publisher per parsing
        config: Configurazione

    Returns:
        Tupla (articolo_finale, qc_result)
    """
    qc_config = config.get("quality_control", {})
    max_cycles = qc_config.get("max_revision_cycles", 3)

    agent_config = config["agents"].get(agent)
    agent_prompt = client.load_prompt(agent_config["prompt_file"])

    current_article = article

    for cycle in range(max_cycles):
        print(f"\n🔍 Quality Control - Ciclo {cycle + 1}/{max_cycles}")

        # Esegui QC
        qc_result = quality_control_article(current_article, client, config)

        decision = qc_result.get("decision", "NEEDS_REVISION")
        quality_score = qc_result.get("quality_score", 0)

        print(f"   Decisione: {decision}")
        print(f"   Quality Score: {quality_score}/10")

        if decision == "APPROVED":
            print("✅ Articolo approvato da Alessandro!")
            return current_article, qc_result

        if decision == "REJECTED":
            print("❌ Articolo RIFIUTATO - Richiede riscrittura completa")
            rejection_reason = qc_result.get("rejection_reason", "Qualità insufficiente")
            print(f"   Motivo: {rejection_reason}")

            # Per REJECTED, proviamo comunque una revisione
            blocking_issues = qc_result.get("blocking_issues", [])
            revision_instructions = qc_result.get(
                "revision_instructions",
                f"L'articolo è stato rifiutato: {rejection_reason}. Riscrivi completamente."
            )

        else:  # NEEDS_REVISION
            print("⚠️  Articolo richiede revisione")
            blocking_issues = qc_result.get("blocking_issues", [])
            revision_instructions = qc_result.get("revision_instructions", "Correggi i problemi indicati.")

            if blocking_issues:
                print("   Problemi bloccanti:")
                for issue in blocking_issues[:3]:  # Mostra max 3
                    print(f"      - [{issue.get('severity')}] {issue.get('problem', 'N/A')[:60]}...")

        # Se è l'ultimo ciclo, non revisionare - vai a human review
        if cycle == max_cycles - 1:
            print(f"\n⚠️  Raggiunto limite massimo di revisioni ({max_cycles})")
            qc_result["decision"] = "NEEDS_HUMAN_REVIEW"
            qc_result["human_review_reason"] = f"Articolo non approvato dopo {max_cycles} revisioni"
            return current_article, qc_result

        # Chiedi al giornalista di revisionare
        print(f"\n📝 Invio articolo a {agent_config['name']} per revisione...")

        revised_article = client.revise_article(
            agent_prompt=agent_prompt,
            original_article=current_article,
            revision_instructions=revision_instructions,
            blocking_issues=blocking_issues,
            model="haiku",
            temperature=0.5,
        )

        current_article = revised_article
        print(f"   ✅ {agent_config['name']} ha revisionato l'articolo")

    # Fallback (non dovrebbe arrivarci)
    return current_article, qc_result


def generate_article(
    topic: str,
    category: str,
    agent: str | None = None,
    context: str | None = None,
    as_draft: bool = True,
    fetch_image: bool = True,
    skip_qc: bool = False,
) -> tuple[Path, dict]:
    """
    Genera un nuovo articolo con ciclo completo di QC.

    Args:
        topic: Argomento dell'articolo
        category: Categoria dell'articolo
        agent: Nome dell'agente (opzionale, altrimenti usa default per categoria)
        context: Contesto aggiuntivo (es. fonte della notizia)
        as_draft: Se True, salva come bozza
        fetch_image: Se True, recupera un'immagine da Unsplash
        skip_qc: Se True, salta il controllo qualità

    Returns:
        Tupla (Path del file creato, risultato QC)
    """
    config = load_config()
    client = ClaudeClient()
    publisher = ArticlePublisher()
    image_fetcher = ImageFetcher()

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

    print("✅ Articolo generato")

    # Quality Control con ciclo di revisione
    qc_result = {"decision": "APPROVED", "quality_score": 8}

    if not skip_qc:
        final_article, qc_result = revision_loop(
            article=article,
            agent=agent,
            client=client,
            publisher=publisher,
            config=config,
        )
        article = final_article

        if qc_result.get("decision") == "NEEDS_HUMAN_REVIEW":
            print("\n⚠️  ATTENZIONE: Articolo richiede review umana prima della pubblicazione")
            as_draft = True  # Forza come draft

    # Salva l'articolo
    file_path = publisher.save_article(article, category=category, as_draft=as_draft)

    # Recupera immagine da Unsplash
    if fetch_image:
        print("🖼️  Ricerca immagine...")

        # Estrai titolo dal file salvato per generare slug coerente
        frontmatter, _ = publisher.parse_frontmatter(file_path.read_text(encoding="utf-8"))
        title = frontmatter.get("title", topic)
        slug = publisher.generate_slug(title)

        image_info = image_fetcher.get_image_for_article(
            title=title,
            category=category,
            slug=slug,
        )

        if image_info:
            # Aggiorna il file con l'immagine nel frontmatter
            article_content = file_path.read_text(encoding="utf-8")
            frontmatter, content = publisher.parse_frontmatter(article_content)

            frontmatter["featuredImage"] = image_info["path"]
            frontmatter["imageCredit"] = f"Photo by {image_info['author']}"
            frontmatter["imageCreditUrl"] = image_info["author_url"]

            # Aggiungi flag di review umana se necessario
            if qc_result.get("decision") == "NEEDS_HUMAN_REVIEW":
                frontmatter["humanReview"] = True
                frontmatter["qcNotes"] = qc_result.get("summary", "Richiede review umana")

            # Riscrivi il file con frontmatter aggiornato
            frontmatter_str = yaml.dump(
                frontmatter, allow_unicode=True, default_flow_style=False, sort_keys=False
            )
            updated_article = f"---\n{frontmatter_str}---\n\n{content}"
            file_path.write_text(updated_article, encoding="utf-8")

            print(f"✅ Immagine aggiunta: {image_info['path']}")
        else:
            print("⚠️  Nessuna immagine trovata (articolo salvato senza immagine)")

    print(f"✅ Articolo salvato: {file_path}")

    # Stampa riepilogo QC
    print(f"\n📊 Riepilogo Quality Control:")
    print(f"   Decisione: {qc_result.get('decision', 'N/A')}")
    print(f"   Quality Score: {qc_result.get('quality_score', 'N/A')}/10")
    if qc_result.get("positive_aspects"):
        print(f"   Aspetti positivi: {', '.join(qc_result['positive_aspects'][:3])}")

    return file_path, qc_result


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


def auto_generate(count: int = 2, publish: bool = False, skip_qc: bool = False):
    """
    Genera automaticamente articoli per diverse categorie.

    Args:
        count: Numero di articoli da generare
        publish: Se True, pubblica automaticamente dopo QC approvato
        skip_qc: Se True, salta il controllo qualità
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
    if skip_qc:
        print("⚠️  Quality Control disabilitato!")

    results = {"approved": 0, "needs_human_review": 0, "failed": 0}

    for i, topic_data in enumerate(sample_topics[:count]):
        print(f"\n{'='*60}")
        print(f"📰 Articolo {i + 1}/{count}")
        print(f"{'='*60}")

        try:
            # Genera con ciclo QC integrato
            draft_path, qc_result = generate_article(
                topic=topic_data["topic"],
                category=topic_data["category"],
                as_draft=True,
                skip_qc=skip_qc,
            )

            decision = qc_result.get("decision", "APPROVED")

            if decision == "APPROVED":
                results["approved"] += 1

                # Pubblica se richiesto e approvato dal QC
                if publish:
                    print("\n📤 Pubblicazione articolo approvato...")
                    publish_article(draft_path, commit=False)

            elif decision == "NEEDS_HUMAN_REVIEW":
                results["needs_human_review"] += 1
                print(f"⚠️  Articolo salvato come bozza - richiede review umana")

            else:
                results["failed"] += 1
                print(f"❌ Articolo non approvato: {decision}")

        except Exception as e:
            print(f"❌ Errore: {e}")
            results["failed"] += 1
            continue

    # Riepilogo finale
    print(f"\n{'='*60}")
    print("📊 RIEPILOGO GENERAZIONE")
    print(f"{'='*60}")
    print(f"   ✅ Approvati: {results['approved']}")
    print(f"   ⚠️  Review umana: {results['needs_human_review']}")
    print(f"   ❌ Falliti: {results['failed']}")

    # Commit unico se pubblicati
    if publish and results["approved"] > 0:
        publisher = ArticlePublisher()
        success = publisher.git_commit_and_push(
            f"📝 Nuovo articolo pubblicato automaticamente"
        )
        if success:
            print("\n✅ Modifiche pushate su GitHub")
        else:
            print("\n⚠️  Errore nel push su GitHub")

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
    gen_parser.add_argument(
        "--skip-qc", action="store_true", help="Salta il controllo qualità (non raccomandato)"
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
    auto_parser.add_argument(
        "--skip-qc", action="store_true", help="Salta il controllo qualità (non raccomandato)"
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

        file_path, qc_result = generate_article(
            topic=topic,
            category=category,
            agent=agent,
            context=args.context,
            as_draft=not args.publish,
            skip_qc=args.skip_qc,
        )

        # Se pubblicazione richiesta e approvato, pubblica
        if args.publish and qc_result.get("decision") == "APPROVED":
            publish_article(file_path, commit=True)

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
        auto_generate(count=args.count, publish=args.publish, skip_qc=args.skip_qc)


if __name__ == "__main__":
    main()
