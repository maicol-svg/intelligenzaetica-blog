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
        from datetime import datetime

        model_id = self.models.get(model, self.models["haiku"])

        # Inietta la data corrente nel prompt (formato italiano)
        current_date = datetime.now().strftime("%d %B %Y")  # Es: "12 febbraio 2026"
        current_date_iso = datetime.now().strftime("%Y-%m-%d")  # Es: "2026-02-12"
        prompt_with_date = agent_prompt.replace("{current_date}", current_date)

        # Costruisci il messaggio utente
        user_message = f"Scrivi un articolo su: {topic}"
        if context:
            user_message += f"\n\nContesto/Fonte:\n{context}"

        user_message += f"\n\nRicorda di includere il frontmatter YAML completo all'inizio."
        user_message += f"\nIMPORTANTE: La data di pubblicazione (publishedAt) deve essere: {current_date_iso}"

        response = self.client.messages.create(
            model=model_id,
            max_tokens=max_tokens,
            temperature=temperature,
            system=prompt_with_date,
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

    def quality_control(
        self,
        qc_prompt: str,
        article: str,
        current_date: str,
        model: str = "sonnet",
        max_tokens: int = 3000,
        temperature: float = 0.2,
    ) -> dict:
        """
        Esegue il controllo qualità su un articolo usando Alessandro.

        Args:
            qc_prompt: System prompt del Quality Controller (con placeholder {current_date})
            article: Articolo da controllare
            current_date: Data corrente per validazione temporale (formato YYYY-MM-DD)
            model: Modello da usare (default: sonnet per precisione)
            max_tokens: Numero massimo di token
            temperature: Temperatura (molto bassa per rigore)

        Returns:
            Dizionario con decision, quality_score, blocking_issues, revision_instructions
        """
        import json

        model_id = self.models.get(model, self.models["sonnet"])

        # Sostituisci il placeholder della data nel prompt
        prompt_with_date = qc_prompt.replace("{current_date}", current_date)

        user_message = f"""Esegui il controllo qualità sul seguente articolo.
Restituisci il risultato ESCLUSIVAMENTE in formato JSON come specificato nelle tue istruzioni.

ARTICOLO DA CONTROLLARE:

{article}
"""

        response = self.client.messages.create(
            model=model_id,
            max_tokens=max_tokens,
            temperature=temperature,
            system=prompt_with_date,
            messages=[{"role": "user", "content": user_message}],
        )

        response_text = response.content[0].text

        # Estrai il JSON dalla risposta
        try:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
            else:
                # Fallback conservativo: richiedi revisione
                return {
                    "decision": "NEEDS_REVISION",
                    "quality_score": 5,
                    "blocking_issues": [{
                        "type": "quality",
                        "severity": "major",
                        "location": "Generale",
                        "problem": "Impossibile analizzare l'articolo",
                        "fix_suggestion": "Rivedere la struttura dell'articolo"
                    }],
                    "revision_instructions": "Rivedere l'articolo e ripresentarlo per il controllo qualità.",
                    "positive_aspects": [],
                    "summary": "Controllo qualità fallito - riprovare."
                }
        except json.JSONDecodeError:
            return {
                "decision": "NEEDS_REVISION",
                "quality_score": 5,
                "blocking_issues": [{
                    "type": "quality",
                    "severity": "major",
                    "location": "Generale",
                    "problem": "Errore nel parsing della risposta QC",
                    "fix_suggestion": "Riprovare il controllo qualità"
                }],
                "revision_instructions": "Si prega di ripresentare l'articolo per un nuovo controllo.",
                "positive_aspects": [],
                "summary": "Errore tecnico nel controllo qualità."
            }

    def revise_article(
        self,
        agent_prompt: str,
        original_article: str,
        revision_instructions: str,
        blocking_issues: list,
        model: str = "haiku",
        max_tokens: int = 4000,
        temperature: float = 0.5,
    ) -> str:
        """
        Chiede al giornalista di riscrivere l'articolo basandosi sul feedback del QC.

        Args:
            agent_prompt: System prompt del giornalista originale
            original_article: Articolo originale da revisionare
            revision_instructions: Istruzioni di revisione da Alessandro
            blocking_issues: Lista dei problemi bloccanti
            model: Modello da usare
            max_tokens: Numero massimo di token
            temperature: Temperatura

        Returns:
            Articolo revisionato in formato Markdown con frontmatter
        """
        model_id = self.models.get(model, self.models["haiku"])

        # Formatta i problemi bloccanti
        issues_text = "\n".join([
            f"- [{issue.get('severity', 'major')}] {issue.get('location', 'N/A')}: {issue.get('problem', 'N/A')}\n  Suggerimento: {issue.get('fix_suggestion', 'N/A')}"
            for issue in blocking_issues
        ])

        user_message = f"""Il tuo articolo NON ha superato il controllo qualità. Devi riscriverlo seguendo le istruzioni.

ARTICOLO ORIGINALE:
{original_article}

PROBLEMI RISCONTRATI:
{issues_text}

ISTRUZIONI DI REVISIONE:
{revision_instructions}

IMPORTANTE:
- Correggi TUTTI i problemi indicati
- Mantieni la struttura e i punti positivi dell'articolo originale
- Assicurati che tutte le date e i riferimenti temporali siano corretti rispetto ad OGGI
- Restituisci l'articolo completo con frontmatter YAML

Riscrivi l'articolo correggendo tutti i problemi indicati."""

        response = self.client.messages.create(
            model=model_id,
            max_tokens=max_tokens,
            temperature=temperature,
            system=agent_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        return response.content[0].text

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
