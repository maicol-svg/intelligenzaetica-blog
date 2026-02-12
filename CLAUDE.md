# CLAUDE.md - Istruzioni per Claude Code

## Panoramica progetto
IntelligenzaEtica.blog è un giornale online italiano gestito da agenti IA, dedicato all'informazione etica sull'intelligenza artificiale.

## Struttura repository

```
intelligenzaetica.blog/
├── src/                    # Codice sorgente Astro
│   ├── pages/              # Pagine del sito
│   ├── layouts/            # Layout template
│   └── components/         # Componenti riutilizzabili
├── content/                # Articoli markdown
│   └── articles/           # Organizzati per categoria
├── agents/                 # Sistema agenti IA
│   ├── orchestrator.py     # Script principale
│   ├── prompts/            # Prompt per ogni agente
│   └── utils/              # Utility functions
├── public/                 # Asset statici
├── VISION.md               # Vision del progetto
├── PRD.md                  # Product Requirements
├── CHANGELOG.md            # Log modifiche
└── CLAUDE.md               # Questo file
```

## Comandi utili

```bash
# Sviluppo
npm run dev                 # Avvia server sviluppo
npm run build               # Build produzione
npm run preview             # Preview build

# Agenti
python agents/orchestrator.py generate   # Genera nuovo articolo
python agents/orchestrator.py review     # Review articoli in coda
python agents/orchestrator.py publish    # Pubblica articoli approvati
python agents/weekly_meeting.py          # Riunione editoriale settimanale
python agents/weekly_meeting.py --dry-run # Anteprima senza modifiche

# Deploy
git push origin main        # Trigger deploy automatico su Netlify
```

## Convenzioni codice

### Astro/Frontend
- Usare Tailwind CSS per styling
- Componenti in PascalCase (es. `ArticleCard.astro`)
- Pagine in kebab-case (es. `chi-siamo.astro`)
- Immagini ottimizzate con `@astrojs/image`

### Articoli (Markdown)
- Frontmatter YAML obbligatorio
- Naming: `YYYY-MM-DD-slug-articolo.md`
- Immagini in `/public/images/articles/`

Esempio frontmatter:
```yaml
---
title: "Titolo dell'articolo"
description: "Descrizione breve per SEO"
author: "marco"  # marco, elena, luca
category: "ia-etica"  # Categorie disponibili sotto
tags: ["tag1", "tag2"]
publishedAt: 2026-02-12
featuredImage: "/images/articles/nome-immagine.jpg"
aiGenerated: true
reviewedBy: "alessandro"  # Quality Controller
humanReview: false
---
```

### Categorie disponibili
- `ia-etica` - IA & Etica
- `tech` - Tech & Innovazione
- `tutorial` - Tutorial & Guide
- `finanza` - Finanza & Lavoro
- `psicologia` - Psicologia & IA
- `ecosostenibile` - IA Ecosostenibile
- `sport` - IA & Sport (analytics, performance, eSports)
- `salute` - IA & Salute (richiede review umana)
- `creativita` - IA & Creatività (arte, musica, scrittura)
- `quotidiano` - Vita Quotidiana (smart home, assistenti vocali)

### Python/Agenti
- Python 3.11+
- Type hints obbligatori
- Docstrings per funzioni pubbliche
- Config in `agents/config.yaml`

## Team agenti IA

| Agente | Ruolo | Specializzazioni | Stile |
|--------|-------|------------------|-------|
| Marco | News & Attualità | tech, finanza, sport | Informativo, dinamico |
| Elena | Tutorial & Lifestyle | tutorial, ecosostenibile, quotidiano, salute | Pratico, step-by-step |
| Luca | Etica & Creatività | ia-etica, psicologia, creativita | Riflessivo, approfondito |
| Sofia | Editor | editing, SEO | Preciso, ottimizzato |
| Alessandro | Quality Controller | QC, fact-checking, validazione temporale | Rigoroso, severo |

## Workflow pubblicazione

1. **Raccolta**: RSS/ricerca → topic disponibili
2. **Assegnazione**: Dispatcher → agente appropriato
3. **Scrittura**: Agente genera bozza
4. **Editing**: Sofia revisiona
5. **Quality Control**: Alessandro verifica (max 3 cicli)
6. **Review**: Automatico o manuale (se flag sensibile)
7. **Pubblicazione**: Commit → Deploy

### Riunione Editoriale Settimanale
Ogni lunedì, il sistema esegue `agents/weekly_meeting.py` per:
- Analizzare performance articoli settimana precedente
- Identificare categorie sottorappresentate
- Generare suggerimenti topic (10 nuovi argomenti)
- Aggiornare calendario editoriale

## Contenuti sensibili (richiedono review umana)

- Argomenti politici
- Temi religiosi
- Contenuti sulla salute
- Menzione persone specifiche
- Consigli finanziari diretti
- Opinioni forti/controverse

## Design system

### Colori
- Background: `#FAFAF8`
- Text Primary: `#2D2D2D`
- Text Secondary: `#6B6B6B`
- Accent: `#7C9A82` (verde salvia)
- Accent Dark: `#4A6850` (per contrasto WCAG AA)
- Accent Darker: `#3A5740` (per hover states)

### Font
- Titoli: Playfair Display
- Corpo: Inter

### Spacing
- Container: max 1200px
- Content: max 680px

## Obiettivi chiave

1. **Qualità**: Articoli originali, ben scritti, informativi
2. **SEO**: Ottimizzazione per ricerca organica
3. **AdSense**: Rispettare tutte le policy Google
4. **UX**: Design rilassante, focus leggibilità
5. **Trasparenza**: Disclosure chiara contenuti IA

## File da consultare

- `VISION.md` - Perché facciamo questo progetto
- `PRD.md` - Requisiti tecnici dettagliati
- `CHANGELOG.md` - Storico modifiche

## Note importanti

- Mai pubblicare senza disclosure IA
- Verificare fonti per fact-checking
- Rispettare copyright (no copy-paste)
- Testare su mobile prima di merge
- Mantenere Lighthouse score > 90

---

*Ultimo aggiornamento: Febbraio 2026*
