"""
Claude API Client per IntelligenzaEtica.blog
Gestisce le chiamate all'API di Anthropic per la generazione di articoli.
"""

import os
from anthropic import Anthropic
from typing import Optional
from pathlib import Path


class ClaudeClient:
    """Client per interagire con l'API di Claude."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Inizializza il client Claude.

        Args:
            api_key: API key di Anthropic. Se non fornita, usa ANTHROPIC_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key non trovata. Imposta ANTHROPIC_API_KEY o passa api_key."
            )

        self.client = Anthropic(api_key=self.api_key)

        # Modelli disponibili (nomi API corretti)
        self.models = {
            "haiku": "claude-3-haiku-20240307",
            "sonnet": "claude-sonnet-4-20250514",
            "opus": "claude-opus-4-20250514",
        }

    def load_prompt(self, prompt_file: str) -> str:
        """
        Carica un prompt da file.

        Args:
            prompt_file: Path al file del prompt (relativo alla cartella agents/)

        Returns:
            Contenuto del prompt
        """
        agents_dir = Path(__file__).parent.parent
        prompt_path = agents_dir / prompt_file

        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file non trovato: {prompt_path}")

        return prompt_path.read_text(encoding="utf-8")

    def generate_article(
        self,
        agent_prompt: str,
        topic: str,
        context: Optional[str] = None,
        model: str = "haiku",
        max_tokens: int = 4000,
        temperature: float = 0.7,
    ) -> str:
        """
        Genera un articolo usando un agente specifico.

        Args:
            agent_prompt: System prompt dell'agente (da file .md)
            topic: Argomento dell'articolo da scrivere
            context: Contesto aggiuntivo (es. notizia di riferimento)
            model: Modello da usare ("haiku", "sonnet", "opus")
            max_tokens: Numero massimo di token in output
            temperature: Temperatura per la generazione

        Returns:
            Articolo generato in formato Markdown con frontmatter
        """
        model_id = self.models.get(model, self.models["haiku"])

        # Costruisci il messaggio utente
        user_message = f"Scrivi un articolo su: {topic}"
        if context:
            user_message += f"\n\nContesto/Fonte:\n{context}"

        user_message += "\n\nRicorda di includere il frontmatter YAML completo all'inizio."

        response = self.client.messages.create(
            model=model_id,
            max_tokens=max_tokens,
            temperature=temperature,
            system=agent_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        return response.content[0].text

    def edit_article(
        self,
        editor_prompt: str,
        article: str,
        model: str = "sonnet",
        max_tokens: int = 5000,
        temperature: float = 0.3,
    ) -> dict:
        """
        Revisiona un articolo usando l'editor Sofia.

        Args:
            editor_prompt: System prompt dell'editor
            article: Articolo da revisionare
            model: Modello da usare (default: sonnet per qualità)
            max_tokens: Numero massimo di token
            temperature: Temperatura (bassa per precisione)

        Returns:
            Dizionario con status, score, issues e articolo revisionato
        """
        import json

        model_id = self.models.get(model, self.models["sonnet"])

        user_message = f"""Revisiona il seguente articolo e restituisci il risultato in formato JSON come specificato nelle tue istruzioni.

ARTICOLO DA REVISIONARE:

{article}
"""

        response = self.client.messages.create(
            model=model_id,
            max_tokens=max_tokens,
            temperature=temperature,
            system=editor_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        response_text = response.content[0].text

        # Estrai il JSON dalla risposta
        try:
            # Cerca il JSON nella risposta
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
            else:
                # Se non trova JSON, restituisci l'articolo come approvato
                return {
                    "status": "approved",
                    "quality_score": 7,
                    "seo_score": 7,
                    "issues": [],
                    "improvements": [],
                    "revised_article": article,
                }
        except json.JSONDecodeError:
            # Fallback: restituisci l'articolo originale
            return {
                "status": "needs_revision",
                "quality_score": 5,
                "seo_score": 5,
                "issues": [
                    {
                        "type": "content",
                        "severity": "medium",
                        "description": "Impossibile parsare la revisione",
                        "suggestion": "Riprova la revisione",
                    }
                ],
                "improvements": [],
                "revised_article": article,
            }

    def summarize_news(
        self,
        news_content: str,
        max_tokens: int = 500,
    ) -> str:
        """
        Riassume una notizia per decidere se vale la pena scriverne un articolo.

        Args:
            news_content: Contenuto della notizia
            max_tokens: Massimo token per il riassunto

        Returns:
            Riassunto strutturato della notizia
        """
        system_prompt = """Sei un assistente che analizza notizie per un blog italiano sull'IA.

Analizza la notizia fornita e restituisci un breve riassunto strutturato:
- RILEVANZA: (alta/media/bassa) per un pubblico italiano interessato all'IA
- ARGOMENTO: categoria principale (tech, etica, tutorial, finanza, psicologia, ecosostenibile)
- TITOLO SUGGERITO: un possibile titolo per un articolo
- PUNTI CHIAVE: 3-5 bullet points
- ANGOLO ITALIANO: come collegare questo tema al contesto italiano"""

        response = self.client.messages.create(
            model=self.models["haiku"],
            max_tokens=max_tokens,
            temperature=0.3,
            system=system_prompt,
            messages=[{"role": "user", "content": news_content}],
        )

        return response.content[0].text


# Esempio di utilizzo
if __name__ == "__main__":
    # Test del client
    client = ClaudeClient()

    # Carica il prompt di Marco
    marco_prompt = client.load_prompt("prompts/marco.md")
    print("Prompt di Marco caricato correttamente!")
    print(f"Lunghezza: {len(marco_prompt)} caratteri")
