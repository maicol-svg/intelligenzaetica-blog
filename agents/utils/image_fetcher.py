"""
Image Fetcher per IntelligenzaEtica.blog
Recupera immagini royalty-free da Unsplash per gli articoli.
"""

import os
import re
import hashlib
from pathlib import Path
from typing import Optional
from datetime import datetime

import httpx


class ImageFetcher:
    """Client per recuperare immagini da Unsplash."""

    UNSPLASH_API_URL = "https://api.unsplash.com"

    # Mapping categorie -> keyword di ricerca Unsplash
    CATEGORY_KEYWORDS = {
        "ia-etica": ["artificial intelligence ethics", "AI robot", "technology ethics"],
        "tech": ["artificial intelligence", "technology", "computer science", "digital"],
        "tutorial": ["coding", "programming", "laptop computer", "developer"],
        "finanza": ["finance technology", "fintech", "stock market", "digital banking"],
        "psicologia": ["mental health", "psychology", "mindfulness", "brain"],
        "ecosostenibile": ["sustainable technology", "green energy", "environment", "solar panel"],
    }

    def __init__(self, api_key: Optional[str] = None, base_path: Optional[Path] = None):
        """
        Inizializza il fetcher.

        Args:
            api_key: Unsplash API Access Key. Se non fornita, usa UNSPLASH_ACCESS_KEY env var.
            base_path: Path base del progetto.
        """
        self.api_key = api_key or os.getenv("UNSPLASH_ACCESS_KEY")

        if base_path:
            self.base_path = Path(base_path)
        else:
            self.base_path = Path(__file__).parent.parent.parent

        self.images_path = self.base_path / "public" / "images" / "articles"
        self.images_path.mkdir(parents=True, exist_ok=True)

    def _extract_keywords_from_title(self, title: str) -> list[str]:
        """
        Estrae keyword rilevanti dal titolo dell'articolo.

        Args:
            title: Titolo dell'articolo

        Returns:
            Lista di keyword per la ricerca
        """
        # Rimuovi parole comuni italiane
        stopwords = {
            "il", "lo", "la", "i", "gli", "le", "un", "uno", "una",
            "di", "a", "da", "in", "con", "su", "per", "tra", "fra",
            "come", "cosa", "che", "chi", "cui", "quale", "quanto",
            "e", "o", "ma", "se", "perché", "quando", "dove",
            "non", "più", "anche", "solo", "tutto", "molto", "poco",
            "essere", "avere", "fare", "dire", "vedere", "sapere",
            "nel", "nella", "nei", "nelle", "del", "della", "dei", "delle",
            "al", "alla", "ai", "alle", "dal", "dalla", "dai", "dalle",
        }

        # Pulisci e tokenizza
        title_clean = re.sub(r"[^\w\s]", " ", title.lower())
        words = [w for w in title_clean.split() if w not in stopwords and len(w) > 2]

        # Traduci keyword comuni italiano -> inglese per Unsplash
        translations = {
            "intelligenza": "intelligence",
            "artificiale": "artificial",
            "tecnologia": "technology",
            "futuro": "future",
            "robot": "robot",
            "algoritmo": "algorithm",
            "algoritmi": "algorithm",
            "machine": "machine",
            "learning": "learning",
            "dati": "data",
            "digitale": "digital",
            "sostenibile": "sustainable",
            "energia": "energy",
            "clima": "climate",
            "ambiente": "environment",
            "finanza": "finance",
            "soldi": "money",
            "investimenti": "investment",
            "psicologia": "psychology",
            "mente": "mind",
            "cervello": "brain",
            "salute": "health",
            "lavoro": "work",
            "azienda": "business",
            "impresa": "business",
        }

        keywords = []
        for word in words[:5]:  # Max 5 keyword
            translated = translations.get(word, word)
            keywords.append(translated)

        return keywords

    def search_image(
        self,
        query: str,
        orientation: str = "landscape",
        per_page: int = 1,
    ) -> Optional[dict]:
        """
        Cerca un'immagine su Unsplash.

        Args:
            query: Query di ricerca
            orientation: Orientamento (landscape, portrait, squarish)
            per_page: Numero di risultati

        Returns:
            Dict con info immagine o None
        """
        if not self.api_key:
            print("⚠️  UNSPLASH_ACCESS_KEY non configurata, skip immagine")
            return None

        try:
            response = httpx.get(
                f"{self.UNSPLASH_API_URL}/search/photos",
                params={
                    "query": query,
                    "orientation": orientation,
                    "per_page": per_page,
                },
                headers={
                    "Authorization": f"Client-ID {self.api_key}",
                },
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()

            if data.get("results"):
                photo = data["results"][0]
                return {
                    "id": photo["id"],
                    "url": photo["urls"]["regular"],  # 1080px width
                    "url_small": photo["urls"]["small"],  # 400px width
                    "url_thumb": photo["urls"]["thumb"],  # 200px width
                    "download_url": photo["links"]["download"],
                    "author": photo["user"]["name"],
                    "author_url": photo["user"]["links"]["html"],
                    "description": photo.get("description") or photo.get("alt_description", ""),
                    "unsplash_url": photo["links"]["html"],
                }

            return None

        except Exception as e:
            print(f"❌ Errore ricerca Unsplash: {e}")
            return None

    def download_image(self, image_url: str, filename: str) -> Optional[Path]:
        """
        Scarica un'immagine e la salva localmente.

        Args:
            image_url: URL dell'immagine
            filename: Nome del file (senza estensione)

        Returns:
            Path del file salvato o None
        """
        try:
            response = httpx.get(image_url, timeout=30.0, follow_redirects=True)
            response.raise_for_status()

            # Determina estensione dal content-type
            content_type = response.headers.get("content-type", "image/jpeg")
            ext = "jpg" if "jpeg" in content_type else "png" if "png" in content_type else "jpg"

            file_path = self.images_path / f"{filename}.{ext}"
            file_path.write_bytes(response.content)

            return file_path

        except Exception as e:
            print(f"❌ Errore download immagine: {e}")
            return None

    def get_image_for_article(
        self,
        title: str,
        category: str,
        slug: str,
    ) -> Optional[dict]:
        """
        Ottiene e scarica un'immagine appropriata per un articolo.

        Args:
            title: Titolo dell'articolo
            category: Categoria dell'articolo
            slug: Slug dell'articolo (per il nome file)

        Returns:
            Dict con path locale e info attribuzione, o None
        """
        if not self.api_key:
            print("⚠️  UNSPLASH_ACCESS_KEY non configurata")
            return None

        # Costruisci query di ricerca
        keywords = self._extract_keywords_from_title(title)
        category_keywords = self.CATEGORY_KEYWORDS.get(category, ["technology"])

        # Prova prima con keyword dal titolo + categoria
        queries_to_try = [
            " ".join(keywords[:3] + category_keywords[:1]),  # Keyword titolo + 1 categoria
            " ".join(category_keywords[:2]),  # Solo categoria
            "artificial intelligence technology",  # Fallback generico
        ]

        image_info = None
        for query in queries_to_try:
            print(f"🔍 Ricerca immagine: '{query}'")
            image_info = self.search_image(query)
            if image_info:
                break

        if not image_info:
            print("⚠️  Nessuna immagine trovata")
            return None

        # Genera nome file univoco
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{date_str}-{slug}"

        # Scarica l'immagine
        print(f"📥 Download immagine: {image_info['id']}")
        local_path = self.download_image(image_info["url"], filename)

        if not local_path:
            return None

        # Path relativo per il frontmatter
        relative_path = f"/images/articles/{local_path.name}"

        return {
            "path": relative_path,
            "local_path": str(local_path),
            "author": image_info["author"],
            "author_url": image_info["author_url"],
            "unsplash_url": image_info["unsplash_url"],
            "description": image_info["description"],
        }

    def trigger_download_tracking(self, download_url: str) -> None:
        """
        Notifica Unsplash del download (richiesto dalle loro linee guida).

        Args:
            download_url: URL di tracking download
        """
        if not self.api_key:
            return

        try:
            httpx.get(
                download_url,
                headers={"Authorization": f"Client-ID {self.api_key}"},
                timeout=5.0,
            )
        except Exception:
            pass  # Non critico


# Test
if __name__ == "__main__":
    fetcher = ImageFetcher()

    print("=== Test Image Fetcher ===\n")

    # Test estrazione keyword
    test_title = "Come l'intelligenza artificiale sta rivoluzionando la finanza"
    keywords = fetcher._extract_keywords_from_title(test_title)
    print(f"Titolo: {test_title}")
    print(f"Keywords: {keywords}")

    # Test ricerca (solo se API key configurata)
    if fetcher.api_key:
        print("\n--- Test ricerca Unsplash ---")
        result = fetcher.search_image("artificial intelligence")
        if result:
            print(f"Trovata: {result['description'][:50]}...")
            print(f"Autore: {result['author']}")
    else:
        print("\n⚠️  Configura UNSPLASH_ACCESS_KEY per testare la ricerca")
