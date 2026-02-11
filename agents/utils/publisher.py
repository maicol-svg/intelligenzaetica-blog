"""
Publisher per IntelligenzaEtica.blog
Gestisce il salvataggio e la pubblicazione degli articoli.
"""

import os
import re
import yaml
from datetime import datetime
from pathlib import Path
from typing import Optional
import subprocess


class ArticlePublisher:
    """Gestisce la pubblicazione degli articoli sul sito."""

    def __init__(self, base_path: Optional[str] = None):
        """
        Inizializza il publisher.

        Args:
            base_path: Path base del progetto. Se non fornito, usa la directory parent.
        """
        if base_path:
            self.base_path = Path(base_path)
        else:
            # Risali dalla cartella utils/
            self.base_path = Path(__file__).parent.parent.parent

        # Articoli pubblicati vanno in src/content/articles/ per Astro Content Collections
        self.content_path = self.base_path / "src" / "content" / "articles"
        self.drafts_path = self.base_path / "content" / "drafts"

        # Crea le directory se non esistono
        self.content_path.mkdir(parents=True, exist_ok=True)
        self.drafts_path.mkdir(parents=True, exist_ok=True)

    def parse_frontmatter(self, article: str) -> tuple[dict, str]:
        """
        Estrae il frontmatter YAML e il contenuto dall'articolo.

        Args:
            article: Articolo completo con frontmatter

        Returns:
            Tupla (frontmatter_dict, content)
        """
        # Pattern per frontmatter YAML (gestisce anche ```yaml blocks)
        pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
        match = re.match(pattern, article.strip(), re.DOTALL)

        if not match:
            # Prova pattern alternativo con ```yaml
            alt_pattern = r"^```yaml\s*\n(.*?)\n```\s*\n(.*)$"
            match = re.match(alt_pattern, article.strip(), re.DOTALL)

        if not match:
            # Fallback: estrai titolo dal contenuto e crea frontmatter
            print("⚠️  Frontmatter non trovato, generazione automatica...")
            content = article.strip()

            # Cerca un titolo (prima riga con # o prima riga)
            lines = content.split("\n")
            title = "Articolo senza titolo"
            for line in lines:
                if line.startswith("# "):
                    title = line[2:].strip()
                    break
                elif line.strip() and not line.startswith("#"):
                    title = line.strip()[:100]
                    break

            frontmatter = {
                "title": title,
                "description": title[:160],
                "author": "marco",
                "publishedAt": datetime.now().strftime("%Y-%m-%d"),
                "aiGenerated": True,
                "humanReview": False,
            }
            return frontmatter, content

        frontmatter_str = match.group(1)
        content = match.group(2).strip()

        try:
            frontmatter = yaml.safe_load(frontmatter_str)
        except yaml.YAMLError as e:
            raise ValueError(f"Errore nel parsing del frontmatter YAML: {e}")

        return frontmatter, content

    def generate_slug(self, title: str) -> str:
        """
        Genera uno slug URL-friendly dal titolo.

        Args:
            title: Titolo dell'articolo

        Returns:
            Slug formattato
        """
        # Converti in minuscolo
        slug = title.lower()

        # Rimuovi caratteri speciali italiani
        replacements = {
            "à": "a",
            "è": "e",
            "é": "e",
            "ì": "i",
            "ò": "o",
            "ù": "u",
            "'": "",
            "'": "",
            '"': "",
            """: "",
            """: "",
        }
        for old, new in replacements.items():
            slug = slug.replace(old, new)

        # Sostituisci spazi e caratteri non alfanumerici con trattini
        slug = re.sub(r"[^a-z0-9]+", "-", slug)

        # Rimuovi trattini multipli e agli estremi
        slug = re.sub(r"-+", "-", slug).strip("-")

        # Limita lunghezza
        if len(slug) > 60:
            slug = slug[:60].rsplit("-", 1)[0]

        return slug

    def save_article(
        self,
        article: str,
        category: Optional[str] = None,
        as_draft: bool = False,
    ) -> Path:
        """
        Salva un articolo nel filesystem.

        Args:
            article: Articolo completo con frontmatter
            category: Categoria (se non specificata, usa quella dal frontmatter)
            as_draft: Se True, salva come bozza invece che pubblicato

        Returns:
            Path del file salvato
        """
        frontmatter, content = self.parse_frontmatter(article)

        # Determina la categoria
        if category:
            frontmatter["category"] = category
        elif "category" not in frontmatter:
            raise ValueError("Categoria non specificata")

        cat = frontmatter["category"]

        # Genera slug e filename
        title = frontmatter.get("title", "untitled")
        slug = self.generate_slug(title)

        # Usa la data dal frontmatter o oggi
        pub_date = frontmatter.get("publishedAt", datetime.now().strftime("%Y-%m-%d"))
        if isinstance(pub_date, datetime):
            pub_date = pub_date.strftime("%Y-%m-%d")

        filename = f"{pub_date}-{slug}.md"

        # Determina il percorso
        if as_draft:
            save_dir = self.drafts_path / cat
        else:
            save_dir = self.content_path / cat

        save_dir.mkdir(parents=True, exist_ok=True)
        file_path = save_dir / filename

        # Ricostruisci l'articolo con frontmatter aggiornato
        frontmatter_str = yaml.dump(
            frontmatter, allow_unicode=True, default_flow_style=False, sort_keys=False
        )
        full_article = f"---\n{frontmatter_str}---\n\n{content}"

        # Salva il file
        file_path.write_text(full_article, encoding="utf-8")

        return file_path

    def publish_draft(self, draft_path: Path) -> Path:
        """
        Pubblica una bozza spostandola nella cartella articoli.

        Args:
            draft_path: Path della bozza

        Returns:
            Path del file pubblicato
        """
        if not draft_path.exists():
            raise FileNotFoundError(f"Bozza non trovata: {draft_path}")

        article = draft_path.read_text(encoding="utf-8")
        published_path = self.save_article(article, as_draft=False)

        # Rimuovi la bozza
        draft_path.unlink()

        return published_path

    def list_drafts(self) -> list[Path]:
        """
        Elenca tutte le bozze disponibili.

        Returns:
            Lista di Path delle bozze
        """
        drafts = []
        for md_file in self.drafts_path.rglob("*.md"):
            drafts.append(md_file)
        return sorted(drafts, key=lambda x: x.name, reverse=True)

    def list_articles(self, category: Optional[str] = None) -> list[Path]:
        """
        Elenca gli articoli pubblicati.

        Args:
            category: Filtra per categoria (opzionale)

        Returns:
            Lista di Path degli articoli
        """
        if category:
            search_path = self.content_path / category
        else:
            search_path = self.content_path

        articles = []
        for md_file in search_path.rglob("*.md"):
            articles.append(md_file)
        return sorted(articles, key=lambda x: x.name, reverse=True)

    def git_commit_and_push(self, message: str) -> bool:
        """
        Committa e pusha le modifiche su GitHub.

        Args:
            message: Messaggio di commit

        Returns:
            True se successo, False altrimenti
        """
        try:
            # Git add
            subprocess.run(
                ["git", "add", "."],
                cwd=self.base_path,
                check=True,
                capture_output=True,
            )

            # Git commit
            full_message = f"""{message}

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"""

            subprocess.run(
                ["git", "commit", "-m", full_message],
                cwd=self.base_path,
                check=True,
                capture_output=True,
            )

            # Git push
            subprocess.run(
                ["git", "push"],
                cwd=self.base_path,
                check=True,
                capture_output=True,
            )

            return True

        except subprocess.CalledProcessError as e:
            print(f"Errore Git: {e}")
            return False


# Esempio di utilizzo
if __name__ == "__main__":
    publisher = ArticlePublisher()

    print(f"Content path: {publisher.content_path}")
    print(f"Drafts path: {publisher.drafts_path}")

    # Test slug generation
    test_titles = [
        "L'Europa approva l'AI Act: cosa cambia",
        "Come usare ChatGPT per scrivere email professionali",
        "Perché l'IA non sostituirà i creativi (per ora)",
    ]

    for title in test_titles:
        print(f"'{title}' -> '{publisher.generate_slug(title)}'")
