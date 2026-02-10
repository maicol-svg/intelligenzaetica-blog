# PRD - IntelligenzaEtica.blog

## Product Requirements Document
**Versione**: 1.0
**Data**: Febbraio 2025
**Status**: In sviluppo

---

## 1. Overview

### 1.1 Descrizione prodotto
Blog/giornale online italiano gestito da agenti IA, focalizzato su informazione etica e consapevole riguardo l'intelligenza artificiale.

### 1.2 Obiettivi
- Pubblicare 2+ articoli originali al giorno
- Ottenere approvazione Google AdSense
- Creare una community di lettori interessati all'IA etica

---

## 2. Requisiti Funzionali

### 2.1 Frontend (Sito Web)

#### Homepage
- [ ] Hero section con articolo in evidenza
- [ ] Griglia articoli recenti per categoria
- [ ] Sidebar/sezione newsletter signup
- [ ] Footer con link policy e contatti

#### Pagina Articolo
- [ ] Titolo, data, autore (agente IA)
- [ ] Contenuto formattato (markdown)
- [ ] Card autore con bio e avatar
- [ ] Disclosure "Articolo scritto da IA"
- [ ] Articoli correlati
- [ ] Spazio per ads (Google AdSense)

#### Pagine Statiche (obbligatorie per AdSense)
- [ ] Chi Siamo - presentazione progetto e team IA
- [ ] Contatti - form contatto o email
- [ ] Privacy Policy - GDPR compliant
- [ ] Cookie Policy - informativa cookies
- [ ] Termini e Condizioni

#### Archivio/Categorie
- [ ] Pagina per ogni categoria
- [ ] Paginazione articoli
- [ ] Filtri per data/tag

### 2.2 Sistema Agenti IA

#### Agenti Copywriter (3)
- [ ] Marco: News & Attualità IA
- [ ] Elena: Tutorial & Guide
- [ ] Luca: Etica, Psicologia, Opinioni

#### Agente Editor (1)
- [ ] Sofia: Revisione, fact-check, SEO

#### Funzionalità agenti
- [ ] Prompt system personalizzati per stile
- [ ] Generazione articoli da fonti RSS
- [ ] Generazione articoli da ricerca web
- [ ] Generazione contenuti originali (tutorial)
- [ ] Revisione e editing automatico
- [ ] Scoring qualità articolo

### 2.3 Sistema di Automazione

#### Raccolta fonti
- [ ] RSS aggregator configurabile
- [ ] Integrazione ricerca web
- [ ] Calendario editoriale

#### Workflow pubblicazione
- [ ] Dispatcher assegnazione topic
- [ ] Pipeline scrittura → editing → review
- [ ] Sistema alert per contenuti sensibili
- [ ] Commit automatico su GitHub
- [ ] Deploy automatico su Netlify

#### Supervisione
- [ ] Dashboard stato articoli
- [ ] Notifiche email per review umana
- [ ] Log attività agenti

---

## 3. Requisiti Non-Funzionali

### 3.1 Performance
- Lighthouse score > 90
- First Contentful Paint < 1.5s
- Time to Interactive < 3s

### 3.2 SEO
- Meta tags ottimizzati
- Sitemap XML automatica
- Schema.org markup per articoli
- URL SEO-friendly

### 3.3 Accessibilità
- WCAG 2.1 AA compliance
- Contrasto colori adeguato
- Navigation keyboard-friendly
- Alt text per immagini

### 3.4 Sicurezza
- HTTPS obbligatorio
- CSP headers
- Sanitizzazione input form
- Rate limiting API

### 3.5 Google AdSense Requirements
- Contenuti originali e di valore
- Navigazione chiara
- Pagine policy complete
- Nessun contenuto proibito
- Minimo 20-30 articoli
- Traffico organico (no bot)

---

## 4. Stack Tecnologico

### Frontend
- **Framework**: Astro
- **Styling**: Tailwind CSS
- **Hosting**: Netlify (free tier)

### Backend/Automazione
- **Runtime**: Python 3.11+
- **API IA**: Claude API (Haiku + Sonnet)
- **Storage**: GitHub (markdown files)
- **Scheduler**: GitHub Actions

### Servizi esterni
- Google AdSense (monetizzazione)
- Google Analytics (tracking)
- RSS feeds (fonti notizie)

---

## 5. Design System

### Palette colori
```
Background: #FAFAF8 (crema caldo)
Text: #2D2D2D (grigio scuro)
Accent: #7C9A82 (verde salvia)
```

### Typography
- Titoli: Playfair Display (serif)
- Corpo: Inter (sans-serif)
- Size corpo: 18-20px, line-height 1.7

### Spacing
- Container max: 1200px
- Content max: 680px
- Padding base: 24px

---

## 6. Milestones

### M1: Setup base
- Progetto Astro inizializzato
- Tema custom implementato
- Deploy su Netlify

### M2: Sistema agenti
- Script orchestratore funzionante
- Prompt agenti definiti
- Primo articolo generato

### M3: Automazione
- RSS aggregator attivo
- Workflow automatizzato
- Sistema alert operativo

### M4: Lancio
- 20+ articoli pubblicati
- Pagine policy complete
- Richiesta Google AdSense

---

## 7. Metriche di successo

| Metrica | Target M1 | Target M3 | Target M6 |
|---------|-----------|-----------|-----------|
| Articoli pubblicati | 10 | 100 | 300 |
| Traffico mensile | - | 500 | 5000 |
| AdSense approvato | No | Si | Si |
| Bounce rate | - | <70% | <60% |

---

## 8. Rischi e Mitigazioni

| Rischio | Probabilità | Impatto | Mitigazione |
|---------|-------------|---------|-------------|
| Rifiuto AdSense | Media | Alto | Contenuti qualità, policy complete |
| Costi API elevati | Bassa | Medio | Uso Haiku, ottimizzazione prompt |
| Contenuti low-quality | Media | Alto | Editor IA + review umana |
| Problemi legali IA | Bassa | Alto | Disclosure chiara, consulenza legale |

---

*Documento creato: Febbraio 2025*
*Ultimo aggiornamento: Febbraio 2025*
