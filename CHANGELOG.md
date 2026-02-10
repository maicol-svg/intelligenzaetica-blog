# Changelog - IntelligenzaEtica.blog

Tutte le modifiche rilevanti al progetto sono documentate in questo file.

Il formato è basato su [Keep a Changelog](https://keepachangelog.com/it/1.0.0/).

---

## [Unreleased]

### Da fare
- Setup progetto Astro
- Implementazione tema custom
- Sistema agenti IA
- Automazione pubblicazione
- Pagine policy (Privacy, Cookie, T&C)
- Richiesta Google AdSense

---

## [0.1.0] - 2025-02-10

### Aggiunto
- Documentazione iniziale del progetto
  - `VISION.md` - Vision e mission del progetto
  - `PRD.md` - Product Requirements Document
  - `CLAUDE.md` - Istruzioni per Claude Code
  - `CHANGELOG.md` - Questo file
- Piano di implementazione in `.claude/plans/`
- Definizione design system (palette verde salvia, typography)
- Definizione team agenti IA (Marco, Elena, Luca, Sofia)
- Definizione categorie (IA & Etica, Tech, Tutorial, Finanza, Psicologia, Ecosostenibile)

### Decisioni architetturali
- Stack: Astro + Tailwind CSS + Netlify
- Agenti: Claude API (Haiku per scrittura, Sonnet per editing)
- Storage: GitHub markdown files
- Automazione: GitHub Actions

---

## Template per nuove entry

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Aggiunto
- Nuove funzionalità

### Modificato
- Cambiamenti a funzionalità esistenti

### Deprecato
- Funzionalità che saranno rimosse

### Rimosso
- Funzionalità rimosse

### Corretto
- Bug fix

### Sicurezza
- Vulnerabilità corrette
```

---

## Legenda versioni

- **Major (X)**: Cambiamenti breaking o milestone importanti
- **Minor (Y)**: Nuove funzionalità retrocompatibili
- **Patch (Z)**: Bug fix e piccole modifiche

---

*Documento mantenuto secondo le best practice di versioning semantico.*
