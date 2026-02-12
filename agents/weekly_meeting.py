#!/usr/bin/env python3
"""
Riunione Editoriale Settimanale - IntelligenzaEtica.blog

Questo script simula una riunione settimanale tra gli agenti IA per:
1. Analizzare le performance della settimana precedente
2. Identificare trend e argomenti caldi
3. Pianificare i contenuti per la settimana successiva
4. Assegnare topic agli agenti

Uso:
    python weekly_meeting.py
    python weekly_meeting.py --dry-run  # Solo analisi, senza modifiche
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
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
from utils.publisher import ArticlePublisher


def load_config() -> dict:
    """Carica la configurazione."""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_recent_articles(publisher: ArticlePublisher, days: int = 7) -> list:
    """Recupera gli articoli pubblicati negli ultimi N giorni."""
    articles = publisher.list_articles()
    recent = []
    cutoff = datetime.now() - timedelta(days=days)

    for article_path in articles:
        try:
            content = article_path.read_text(encoding="utf-8")
            frontmatter, _ = publisher.parse_frontmatter(content)
            pub_date = frontmatter.get("publishedAt", "")
            if isinstance(pub_date, str):
                pub_date = datetime.strptime(pub_date, "%Y-%m-%d")
            if pub_date >= cutoff:
                recent.append({
                    "path": str(article_path),
                    "title": frontmatter.get("title", ""),
                    "category": frontmatter.get("category", ""),
                    "author": frontmatter.get("author", ""),
                    "date": pub_date.strftime("%Y-%m-%d"),
                })
        except Exception:
            continue

    return recent


def analyze_category_coverage(articles: list, config: dict) -> dict:
    """Analizza la copertura delle categorie."""
    categories = config.get("categories", {})
    coverage = {cat: 0 for cat in categories.keys()}

    for article in articles:
        cat = article.get("category", "")
        if cat in coverage:
            coverage[cat] += 1

    # Calcola categorie mancanti o sottorappresentate
    missing = []
    for cat, info in categories.items():
        expected = info.get("frequency_per_week", 1)
        actual = coverage.get(cat, 0)
        if actual < expected:
            missing.append({
                "category": cat,
                "label": info.get("label", cat),
                "expected": expected,
                "actual": actual,
                "deficit": expected - actual,
            })

    return {
        "coverage": coverage,
        "missing": sorted(missing, key=lambda x: x["deficit"], reverse=True),
    }


def generate_topic_suggestions(client: ClaudeClient, config: dict, coverage: dict) -> list:
    """Genera suggerimenti di topic per la settimana successiva."""

    categories = config.get("categories", {})
    missing_cats = coverage.get("missing", [])

    # Prioritizza le categorie mancanti
    priority_categories = [m["label"] for m in missing_cats[:5]]

    prompt = f"""Sei il coordinatore editoriale di IntelligenzaEtica.blog, un giornale italiano sull'intelligenza artificiale.

Data odierna: {datetime.now().strftime("%d %B %Y")}

Devi proporre 10 argomenti per articoli da pubblicare la prossima settimana.

CATEGORIE PRIORITARIE (hanno bisogno di più contenuti):
{', '.join(priority_categories) if priority_categories else 'Tutte le categorie sono ben coperte'}

TUTTE LE CATEGORIE DISPONIBILI:
{json.dumps({k: v.get('label', k) for k, v in categories.items()}, indent=2, ensure_ascii=False)}

REQUISITI:
1. Gli argomenti devono essere ATTUALI e rilevanti per febbraio 2026
2. Devono essere INTERESSANTI e COINVOLGENTI per il pubblico italiano
3. Coprire diverse categorie, con priorità a quelle mancanti
4. Includere mix di notizie, approfondimenti e tutorial
5. NON inventare notizie specifiche - proponi TEMI generali su cui scrivere

Rispondi con un JSON array di oggetti con questa struttura:
[
  {{
    "topic": "Titolo/tema dell'articolo",
    "category": "slug_categoria",
    "agent": "nome_agente",
    "priority": "high|medium|low",
    "angle": "Breve descrizione dell'angolazione da prendere"
  }}
]
"""

    response = client.client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=2000,
        temperature=0.7,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = response.content[0].text

    # Estrai JSON
    try:
        json_start = response_text.find("[")
        json_end = response_text.rfind("]") + 1
        if json_start != -1 and json_end > json_start:
            return json.loads(response_text[json_start:json_end])
    except json.JSONDecodeError:
        pass

    return []


def generate_meeting_report(
    recent_articles: list,
    coverage: dict,
    suggestions: list,
    config: dict,
) -> str:
    """Genera il report della riunione settimanale."""

    date = datetime.now().strftime("%d %B %Y")

    report = f"""# Riunione Editoriale Settimanale
**Data:** {date}

---

## Partecipanti
- **Marco** - Giornalista IA (News, Tech, Sport)
- **Elena** - Giornalista IA (Tutorial, Lifestyle, Salute)
- **Luca** - Giornalista IA (Etica, Creatività, Psicologia)
- **Alessandro** - Quality Controller (Moderatore)

---

## 1. Performance Settimana Precedente

**Articoli pubblicati:** {len(recent_articles)}

### Per categoria:
"""

    for cat, count in coverage.get("coverage", {}).items():
        label = config.get("categories", {}).get(cat, {}).get("label", cat)
        report += f"- **{label}**: {count} articoli\n"

    report += "\n### Categorie da potenziare:\n"

    for missing in coverage.get("missing", [])[:5]:
        report += f"- **{missing['label']}**: {missing['actual']}/{missing['expected']} (deficit: {missing['deficit']})\n"

    report += """
---

## 2. Piano Editoriale Settimana Prossima

### Argomenti proposti:

"""

    for i, topic in enumerate(suggestions, 1):
        cat_label = config.get("categories", {}).get(topic.get("category", ""), {}).get("label", topic.get("category", ""))
        report += f"""#### {i}. {topic.get('topic', 'N/A')}
- **Categoria:** {cat_label}
- **Assegnato a:** {topic.get('agent', 'N/A').capitalize()}
- **Priorità:** {topic.get('priority', 'medium')}
- **Angolo:** {topic.get('angle', 'N/A')}

"""

    report += """---

## 3. Decisioni e Note

- [ ] Verificare disponibilità immagini per gli articoli
- [ ] Coordinare con Alessandro per QC tempestivo
- [ ] Monitorare trend sui social per opportunità last-minute

---

*Report generato automaticamente dal sistema IntelligenzaEtica.blog*
"""

    return report


def run_weekly_meeting(dry_run: bool = False):
    """Esegue la riunione settimanale."""

    print("=" * 60)
    print("RIUNIONE EDITORIALE SETTIMANALE")
    print(f"Data: {datetime.now().strftime('%d %B %Y')}")
    print("=" * 60)

    config = load_config()
    client = ClaudeClient()
    publisher = ArticlePublisher()

    # 1. Analizza articoli recenti
    print("\n1. Analisi articoli settimana precedente...")
    recent_articles = get_recent_articles(publisher, days=7)
    print(f"   Articoli trovati: {len(recent_articles)}")

    # 2. Analizza copertura categorie
    print("\n2. Analisi copertura categorie...")
    coverage = analyze_category_coverage(recent_articles, config)

    missing = coverage.get("missing", [])
    if missing:
        print("   Categorie da potenziare:")
        for m in missing[:3]:
            print(f"      - {m['label']}: {m['actual']}/{m['expected']}")
    else:
        print("   Tutte le categorie sono ben coperte!")

    # 3. Genera suggerimenti topic
    print("\n3. Generazione suggerimenti topic...")
    suggestions = generate_topic_suggestions(client, config, coverage)
    print(f"   Topic suggeriti: {len(suggestions)}")

    # 4. Genera report
    print("\n4. Generazione report riunione...")
    report = generate_meeting_report(recent_articles, coverage, suggestions, config)

    # 5. Salva report
    report_path = Path(__file__).parent / "weekly_report.md"

    if not dry_run:
        report_path.write_text(report, encoding="utf-8")
        print(f"\n   Report salvato: {report_path}")

        # Aggiorna calendario editoriale con i topic suggeriti
        calendar_path = Path(__file__).parent / "editorial_calendar.json"
        if calendar_path.exists():
            with open(calendar_path, "r", encoding="utf-8") as f:
                calendar = json.load(f)
        else:
            calendar = {"topics_pool": {}}

        # Aggiungi topic suggeriti al pool
        for topic in suggestions:
            cat = topic.get("category", "tech")
            if cat not in calendar.get("topics_pool", {}):
                calendar["topics_pool"][cat] = []

            # Evita duplicati
            existing_topics = [t.get("topic", "") for t in calendar["topics_pool"][cat]]
            if topic.get("topic", "") not in existing_topics:
                calendar["topics_pool"][cat].append({
                    "topic": topic.get("topic", ""),
                    "agent": topic.get("agent", ""),
                    "priority": topic.get("priority", "medium"),
                    "added_date": datetime.now().strftime("%Y-%m-%d"),
                    "source": "weekly_meeting",
                })

        with open(calendar_path, "w", encoding="utf-8") as f:
            json.dump(calendar, f, ensure_ascii=False, indent=2)

        print(f"   Calendario aggiornato: {calendar_path}")
    else:
        print("\n   [DRY RUN] Report non salvato")
        print("\n--- ANTEPRIMA REPORT ---\n")
        print(report[:2000] + "...\n")

    print("\n" + "=" * 60)
    print("RIUNIONE COMPLETATA")
    print("=" * 60)

    return suggestions


def main():
    parser = argparse.ArgumentParser(
        description="Riunione Editoriale Settimanale IntelligenzaEtica.blog"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Solo analisi, senza salvare modifiche",
    )

    args = parser.parse_args()
    run_weekly_meeting(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
