#!/usr/bin/env python3
"""
IntelligenzaEtica.blog - Scheduler Pubblicazione
Gestisce il calendario editoriale e determina quali articoli generare.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Mapping giorni della settimana
GIORNI = {
    0: "lunedi",
    1: "martedi",
    2: "mercoledi",
    3: "giovedi",
    4: "venerdi",
    5: "sabato",
    6: "domenica"
}

# Mapping slot orari
SLOT_ORARI = {
    "mattina": (8, 10),   # 08:00-10:00
    "sera": (18, 20)      # 18:00-20:00
}


class PublishingScheduler:
    """Gestisce la pianificazione degli articoli."""

    def __init__(self, calendar_path: Optional[Path] = None):
        """
        Inizializza lo scheduler.

        Args:
            calendar_path: Path al file editorial_calendar.json
        """
        if calendar_path is None:
            calendar_path = Path(__file__).parent / "editorial_calendar.json"

        self.calendar_path = calendar_path
        self.calendar = self._load_calendar()

    def _load_calendar(self) -> dict:
        """Carica il calendario editoriale."""
        if self.calendar_path.exists():
            with open(self.calendar_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def get_today_schedule(self) -> list[dict]:
        """
        Ottiene il programma di oggi.

        Returns:
            Lista di slot con categoria e agente assegnato
        """
        oggi = datetime.now()
        giorno = GIORNI[oggi.weekday()]

        schedule = self.calendar.get("schedule", {}).get(giorno, [])
        return schedule

    def get_current_slot(self) -> Optional[dict]:
        """
        Determina lo slot corrente in base all'ora.

        Returns:
            Slot corrente o None se fuori orario
        """
        ora_corrente = datetime.now().hour
        oggi_schedule = self.get_today_schedule()

        for slot in oggi_schedule:
            slot_name = slot.get("slot", "")
            if slot_name in SLOT_ORARI:
                ora_inizio, ora_fine = SLOT_ORARI[slot_name]
                if ora_inizio <= ora_corrente < ora_fine:
                    return slot

        return None

    def get_next_article_to_generate(self) -> Optional[dict]:
        """
        Determina il prossimo articolo da generare.

        Logica:
        1. Controlla lo slot corrente
        2. Se siamo in uno slot, restituisce categoria/agente
        3. Altrimenti restituisce il prossimo slot programmato

        Returns:
            Dict con categoria, agente, topic (se disponibile)
        """
        # Prima controlla lo slot corrente
        current_slot = self.get_current_slot()
        if current_slot:
            return self._prepare_article_task(current_slot)

        # Se non siamo in uno slot, trova il prossimo
        return self._get_next_scheduled_slot()

    def _prepare_article_task(self, slot: dict) -> dict:
        """
        Prepara un task articolo dallo slot.

        Args:
            slot: Slot dal calendario

        Returns:
            Task pronto per l'orchestratore
        """
        categoria = slot.get("categoria", "")
        agente = slot.get("agente", "")

        # Cerca un topic disponibile per questa categoria
        topic = self._get_topic_for_category(categoria)

        return {
            "categoria": categoria,
            "agente": agente,
            "topic": topic,
            "slot": slot.get("slot", ""),
            "scheduled_time": datetime.now().isoformat()
        }

    def _get_topic_for_category(self, categoria: str) -> Optional[str]:
        """
        Ottiene un topic per la categoria specificata.

        Args:
            categoria: Nome della categoria

        Returns:
            Topic selezionato o None
        """
        topics_pool = self.calendar.get("topics_pool", {})
        category_topics = topics_pool.get(categoria, [])

        if category_topics:
            # Seleziona random e rimuovi dal pool
            topic = random.choice(category_topics)
            return topic

        return None

    def _get_next_scheduled_slot(self) -> Optional[dict]:
        """Trova il prossimo slot programmato."""
        oggi = datetime.now()
        ora_corrente = oggi.hour

        # Prima controlla gli slot rimanenti di oggi
        oggi_schedule = self.get_today_schedule()
        for slot in oggi_schedule:
            slot_name = slot.get("slot", "")
            if slot_name in SLOT_ORARI:
                ora_inizio, _ = SLOT_ORARI[slot_name]
                if ora_inizio > ora_corrente:
                    return self._prepare_article_task(slot)

        # Altrimenti prendi il primo slot di domani
        domani = (oggi.weekday() + 1) % 7
        giorno_domani = GIORNI[domani]
        domani_schedule = self.calendar.get("schedule", {}).get(giorno_domani, [])

        if domani_schedule:
            return self._prepare_article_task(domani_schedule[0])

        return None

    def mark_topic_used(self, categoria: str, topic: str) -> None:
        """
        Segna un topic come usato rimuovendolo dal pool.

        Args:
            categoria: Categoria del topic
            topic: Topic usato
        """
        if categoria in self.calendar.get("topics_pool", {}):
            topics = self.calendar["topics_pool"][categoria]
            if topic in topics:
                topics.remove(topic)
                self._save_calendar()

    def add_topic(self, categoria: str, topic: str) -> None:
        """
        Aggiunge un topic al pool.

        Args:
            categoria: Categoria del topic
            topic: Nuovo topic
        """
        if "topics_pool" not in self.calendar:
            self.calendar["topics_pool"] = {}

        if categoria not in self.calendar["topics_pool"]:
            self.calendar["topics_pool"][categoria] = []

        if topic not in self.calendar["topics_pool"][categoria]:
            self.calendar["topics_pool"][categoria].append(topic)
            self._save_calendar()

    def _save_calendar(self) -> None:
        """Salva il calendario su file."""
        with open(self.calendar_path, "w", encoding="utf-8") as f:
            json.dump(self.calendar, f, ensure_ascii=False, indent=2)

    def get_weekly_stats(self) -> dict:
        """
        Ottiene statistiche settimanali.

        Returns:
            Dict con conteggio articoli per categoria
        """
        stats = {}
        schedule = self.calendar.get("schedule", {})

        for giorno, slots in schedule.items():
            for slot in slots:
                cat = slot.get("categoria", "unknown")
                stats[cat] = stats.get(cat, 0) + 1

        return stats

    def should_generate_now(self) -> bool:
        """
        Verifica se dobbiamo generare un articolo ora.

        Returns:
            True se siamo in uno slot di pubblicazione
        """
        return self.get_current_slot() is not None


def main():
    """Test dello scheduler."""
    scheduler = PublishingScheduler()

    print("=== IntelligenzaEtica.blog - Scheduler ===\n")

    # Info giorno corrente
    oggi = datetime.now()
    print(f"Oggi: {GIORNI[oggi.weekday()].capitalize()} {oggi.strftime('%d/%m/%Y %H:%M')}")

    # Schedule di oggi
    print("\n--- Programma di oggi ---")
    today_schedule = scheduler.get_today_schedule()
    if today_schedule:
        for slot in today_schedule:
            print(f"  [{slot['slot'].upper()}] {slot['categoria']} -> {slot['agente']}")
    else:
        print("  Nessun articolo programmato")

    # Slot corrente
    print("\n--- Slot corrente ---")
    current = scheduler.get_current_slot()
    if current:
        print(f"  Attivo: {current['categoria']} ({current['agente']})")
    else:
        print("  Nessuno slot attivo")

    # Prossimo articolo
    print("\n--- Prossimo articolo ---")
    next_article = scheduler.get_next_article_to_generate()
    if next_article:
        print(f"  Categoria: {next_article['categoria']}")
        print(f"  Agente: {next_article['agente']}")
        print(f"  Topic: {next_article.get('topic', 'Da generare')}")
    else:
        print("  Nessun articolo in coda")

    # Statistiche settimanali
    print("\n--- Statistiche settimanali ---")
    stats = scheduler.get_weekly_stats()
    for cat, count in sorted(stats.items()):
        print(f"  {cat}: {count} articoli")


if __name__ == "__main__":
    main()
