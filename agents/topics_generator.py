#!/usr/bin/env python3
"""
IntelligenzaEtica.blog - Topics Generator
Raccoglie topic da RSS feed e fonti web per alimentare il calendario editoriale.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import feedparser
import httpx

# Feed RSS per categoria
RSS_FEEDS = {
    "ia-etica": [
        "https://www.technologyreview.com/feed/",
        "https://www.wired.it/feed/rss",
        "https://artificialintelligence-news.com/feed/",
    ],
    "tech": [
        "https://www.theverge.com/rss/index.xml",
        "https://techcrunch.com/feed/",
        "https://www.wired.it/feed/rss",
        "https://www.hwupgrade.it/rss/news.xml",
    ],
    "tutorial": [
        "https://dev.to/feed",
        "https://realpython.com/atom.xml",
        "https://towardsdatascience.com/feed",
    ],
    "finanza": [
        "https://www.milanofinanza.it/rss",
        "https://www.ilsole24ore.com/rss/economia.xml",
    ],
    "psicologia": [
        "https://www.stateofmind.it/feed/",
        "https://www.lescienze.it/rss/mente_e_cervello/all/rss2.0.xml",
    ],
    "ecosostenibile": [
        "https://www.rinnovabili.it/feed/",
        "https://www.greenme.it/feed/",
    ]
}

# Keywords per filtrare articoli rilevanti per IA
AI_KEYWORDS = [
    r"\bIA\b", r"\bAI\b", r"intelligenza artificiale",
    r"machine learning", r"deep learning", r"neural network",
    r"ChatGPT", r"GPT", r"Claude", r"Gemini", r"Copilot",
    r"large language model", r"LLM", r"transformer",
    r"algoritm", r"automazion", r"robot", r"chatbot",
    r"generativ", r"sintetic", r"deepfake",
]


class TopicsGenerator:
    """Genera topic da fonti esterne."""

    def __init__(self, calendar_path: Optional[Path] = None):
        """
        Inizializza il generatore.

        Args:
            calendar_path: Path al calendario editoriale
        """
        if calendar_path is None:
            calendar_path = Path(__file__).parent / "editorial_calendar.json"

        self.calendar_path = calendar_path
        self.calendar = self._load_calendar()

    def _load_calendar(self) -> dict:
        """Carica il calendario."""
        if self.calendar_path.exists():
            with open(self.calendar_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"topics_pool": {}}

    def _save_calendar(self) -> None:
        """Salva il calendario."""
        with open(self.calendar_path, "w", encoding="utf-8") as f:
            json.dump(self.calendar, f, ensure_ascii=False, indent=2)

    def _is_ai_related(self, text: str) -> bool:
        """
        Verifica se il testo è correlato all'IA.

        Args:
            text: Testo da verificare

        Returns:
            True se contiene keyword IA
        """
        text_lower = text.lower()
        for keyword in AI_KEYWORDS:
            if re.search(keyword, text_lower, re.IGNORECASE):
                return True
        return False

    def fetch_rss_topics(self, categoria: str, limit: int = 10) -> list[dict]:
        """
        Recupera topic da feed RSS per una categoria.

        Args:
            categoria: Categoria target
            limit: Numero massimo di topic

        Returns:
            Lista di topic con titolo e link
        """
        feeds = RSS_FEEDS.get(categoria, [])
        topics = []

        for feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)

                for entry in feed.entries[:20]:
                    title = entry.get("title", "")
                    summary = entry.get("summary", "")
                    link = entry.get("link", "")

                    # Filtra per rilevanza IA (tranne tutorial che ha topic più generici)
                    if categoria != "tutorial":
                        if not self._is_ai_related(title + " " + summary):
                            continue

                    # Evita duplicati
                    if any(t["title"] == title for t in topics):
                        continue

                    topics.append({
                        "title": title,
                        "summary": summary[:200] if summary else "",
                        "link": link,
                        "source": feed.feed.get("title", feed_url),
                        "fetched_at": datetime.now().isoformat()
                    })

                    if len(topics) >= limit:
                        break

            except Exception as e:
                print(f"Errore fetching {feed_url}: {e}")
                continue

            if len(topics) >= limit:
                break

        return topics[:limit]

    def generate_topic_from_news(self, news: dict, categoria: str) -> str:
        """
        Trasforma una news in un topic per articolo originale.

        Args:
            news: Dict con title, summary, link
            categoria: Categoria dell'articolo

        Returns:
            Topic riformulato per articolo originale
        """
        # Il topic deve essere originale, non un riassunto della news
        title = news.get("title", "")

        # Riformula come angolo di analisi
        prefixes = {
            "ia-etica": "Analisi etica: ",
            "tech": "Novità tech: ",
            "tutorial": "Guida pratica: ",
            "finanza": "Impatto finanziario: ",
            "psicologia": "Prospettiva psicologica: ",
            "ecosostenibile": "Sostenibilità e IA: "
        }

        prefix = prefixes.get(categoria, "")

        # Pulizia e riformulazione
        topic = f"{prefix}{title}"

        return topic

    def refill_topics_pool(self, min_topics: int = 5) -> dict:
        """
        Riempie il pool di topic per categorie sotto soglia.

        Args:
            min_topics: Soglia minima per categoria

        Returns:
            Report delle operazioni
        """
        report = {"added": {}, "errors": []}

        for categoria in RSS_FEEDS.keys():
            current_topics = self.calendar.get("topics_pool", {}).get(categoria, [])

            if len(current_topics) < min_topics:
                needed = min_topics - len(current_topics)
                print(f"\n{categoria}: serve {needed} topic...")

                try:
                    news_items = self.fetch_rss_topics(categoria, limit=needed * 2)

                    added = 0
                    for news in news_items:
                        topic = self.generate_topic_from_news(news, categoria)

                        # Evita duplicati
                        if topic not in current_topics:
                            if categoria not in self.calendar["topics_pool"]:
                                self.calendar["topics_pool"][categoria] = []

                            self.calendar["topics_pool"][categoria].append(topic)
                            current_topics.append(topic)
                            added += 1

                            if added >= needed:
                                break

                    report["added"][categoria] = added
                    print(f"  Aggiunti {added} topic")

                except Exception as e:
                    report["errors"].append(f"{categoria}: {str(e)}")
                    print(f"  Errore: {e}")

        self._save_calendar()
        return report

    def get_topic_stats(self) -> dict:
        """
        Statistiche sui topic disponibili.

        Returns:
            Dict con conteggio per categoria
        """
        stats = {}
        topics_pool = self.calendar.get("topics_pool", {})

        for categoria, topics in topics_pool.items():
            stats[categoria] = len(topics)

        return stats

    def add_manual_topic(self, categoria: str, topic: str) -> bool:
        """
        Aggiunge un topic manualmente.

        Args:
            categoria: Categoria target
            topic: Topic da aggiungere

        Returns:
            True se aggiunto, False se duplicato
        """
        if "topics_pool" not in self.calendar:
            self.calendar["topics_pool"] = {}

        if categoria not in self.calendar["topics_pool"]:
            self.calendar["topics_pool"][categoria] = []

        if topic in self.calendar["topics_pool"][categoria]:
            return False

        self.calendar["topics_pool"][categoria].append(topic)
        self._save_calendar()
        return True


def main():
    """Test del generatore topic."""
    generator = TopicsGenerator()

    print("=== IntelligenzaEtica.blog - Topics Generator ===\n")

    # Statistiche attuali
    print("--- Topic disponibili ---")
    stats = generator.get_topic_stats()
    for cat, count in sorted(stats.items()):
        status = "OK" if count >= 5 else "BASSO"
        print(f"  {cat}: {count} topic [{status}]")

    # Refill se richiesto
    print("\n--- Verifica e refill topic ---")
    report = generator.refill_topics_pool(min_topics=5)

    if report["added"]:
        print("\nTopic aggiunti:")
        for cat, count in report["added"].items():
            if count > 0:
                print(f"  {cat}: +{count}")

    if report["errors"]:
        print("\nErrori:")
        for err in report["errors"]:
            print(f"  {err}")

    # Statistiche finali
    print("\n--- Topic finali ---")
    stats = generator.get_topic_stats()
    total = sum(stats.values())
    print(f"  Totale: {total} topic")
    for cat, count in sorted(stats.items()):
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    main()
