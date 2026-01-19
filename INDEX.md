# 📚 Documentation Index - lab-toolchains

## 🚀 Where to Start?

### First Time Use
1. **[QUICKSTART.md](QUICKSTART.md)** ⭐ - Quick start (5 min)
2. **[SUMMARY.md](SUMMARY.md)** - Complete project overview
3. **[README.md](README.md)** - Detailed main documentation

### Migration from Old Version
1. **[MIGRATION.md](MIGRATION.md)** - Migration guide
2. **[QUICKSTART.md](QUICKSTART.md)** - New commands

## 📖 Documentation by Theme

### 🏗️ Architecture & Design
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed system architecture
- **[SUMMARY.md](SUMMARY.md)** - Current architecture summary
- **[README.md](README.md)** - Components overview

### 💻 Development
- **[QUICKSTART.md](QUICKSTART.md)** - Setup & basic commands
- **[app/docs/IMPROVEMENTS_SUMMARY.md](app/docs/IMPROVEMENTS_SUMMARY.md)** - Complete optimization history
- **[app/docs/INTENT_DETECTION.md](app/docs/INTENT_DETECTION.md)** - Deep dive: Semantic intent detection
- **[README.md](README.md)** - API and programmatic usage

### 📊 Observability (OpenTelemetry / Grafana)
- **[app/docs/OTLP_STATUS.md](app/docs/OTLP_STATUS.md)** ⭐ - Current Phase 1 status + Phase 2 roadmap
- **[app/docs/OTLP_INTEGRATION.md](app/docs/OTLP_INTEGRATION.md)** - Complete OpenTelemetry guide
- **[app/docs/OTLP_EXAMPLES.md](app/docs/OTLP_EXAMPLES.md)** - Instrumentation code examples
- **[observability/check_otlp.sh](observability/check_otlp.sh)** - Diagnostic script

### 🧹 Project & Maintenance
- **[MIGRATION.md](MIGRATION.md)** - Migration guide (structure)
- **[SUMMARY.md](SUMMARY.md)** - Project status & summary
- **[README.md](README.md)** - Known issues & troubleshooting

## 🎯 By Use Case

### "I want to test quickly"
1. [QUICKSTART.md](QUICKSTART.md) → "Quick Installation" section
2. `streamlit run app/streamlit_app.py`

### "I want to understand the architecture"
1. [SUMMARY.md](SUMMARY.md) → "Current Architecture" section
2. [ARCHITECTURE.md](ARCHITECTURE.md) → Complete diagrams
3. [app/docs/IMPROVEMENTS_SUMMARY.md](app/docs/IMPROVEMENTS_SUMMARY.md) → History

### "I want to setup observability"
1. [app/docs/OTLP_STATUS.md](app/docs/OTLP_STATUS.md) → Understand current state
2. [app/docs/OTLP_INTEGRATION.md](app/docs/OTLP_INTEGRATION.md) → Complete guide
3. `cd observability && ./start-observability.sh` → Launch

### "I want to develop / contribute"
1. [QUICKSTART.md](QUICKSTART.md) → Environment setup
2. [ARCHITECTURE.md](ARCHITECTURE.md) → Understand patterns
3. [app/docs/IMPROVEMENTS_SUMMARY.md](app/docs/IMPROVEMENTS_SUMMARY.md) → See history
4. [app/docs/INTENT_DETECTION.md](app/docs/INTENT_DETECTION.md) → Technical deep dive

### "I have a problem"
1. [QUICKSTART.md](QUICKSTART.md) → "Troubleshooting" section
2. [README.md](README.md) → "Known Issues" section
3. [app/docs/OTLP_STATUS.md](app/docs/OTLP_STATUS.md) → Observability limitations

## 📂 File Structure

### At Root
```
├── README.md              # Main documentation (overview)
├── QUICKSTART.md          # Quick start (5 min)
├── SUMMARY.md             # Complete executive summary
├── MIGRATION.md           # Migration guide
├── ARCHITECTURE.md        # Detailed system architecture
└── INDEX.md               # This file
```

### In app/docs/
```
app/docs/
├── IMPROVEMENTS_SUMMARY.md   # Optimization history
├── INTENT_DETECTION.md       # Intent detection deep dive
├── OTLP_INTEGRATION.md       # Complete OpenTelemetry guide
├── OTLP_STATUS.md            # Phase 1 status + Roadmap
└── OTLP_EXAMPLES.md          # Instrumentation code examples
```

### Useful Scripts
```
observability/
├── start-observability.sh    # Launch Grafana stack
├── check_otlp.sh             # OTLP diagnostic
└── docker-compose.yml        # Infrastructure config
```

## 🔗 Quick Links

### Main Documentation
- [README.md](README.md) - Main entry point
- [SUMMARY.md](SUMMARY.md) - Complete summary in 1 page

### Practical Guides
- [QUICKSTART.md](QUICKSTART.md) - 5 min setup
- [MIGRATION.md](MIGRATION.md) - Old structure migration

### Technical Documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- [app/docs/INTENT_DETECTION.md](app/docs/INTENT_DETECTION.md) - Intent detection
- [app/docs/OTLP_STATUS.md](app/docs/OTLP_STATUS.md) - Observability

## 🎓 Recommended Learning Path

### Level 1: Discovery (30 min)
1. [SUMMARY.md](SUMMARY.md) - Overview (10 min)
2. [QUICKSTART.md](QUICKSTART.md) - Setup & test (15 min)
3. Test web application (5 min)

### Level 2: Understanding (2h)
1. [README.md](README.md) - Detailed features (30 min)
2. [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture (30 min)
3. [app/docs/IMPROVEMENTS_SUMMARY.md](app/docs/IMPROVEMENTS_SUMMARY.md) - Optimizations (30 min)
4. [app/docs/INTENT_DETECTION.md](app/docs/INTENT_DETECTION.md) - Deep dive (30 min)

### Level 3: Mastery (4h)
1. Setup observability (1h) - [app/docs/OTLP_INTEGRATION.md](app/docs/OTLP_INTEGRATION.md)
2. Analyze source code (2h)
3. Experiment with custom prompts (1h)

### Level 4: Contribution (variable)
1. Understand Phase 2 roadmap - [app/docs/OTLP_STATUS.md](app/docs/OTLP_STATUS.md)
2. Identify improvement area
3. Implement & test

## 💡 Tips

- **Beginner?** Start with [QUICKSTART.md](QUICKSTART.md)
- **In a hurry?** Read [SUMMARY.md](SUMMARY.md) (5 min)
- **Technical?** Go to [ARCHITECTURE.md](ARCHITECTURE.md)
- **Observability?** See [app/docs/OTLP_STATUS.md](app/docs/OTLP_STATUS.md)
- **Migration?** Check [MIGRATION.md](MIGRATION.md)

## 🔍 Quick Search

| Looking for... | File |
|----------------|------|
| Basic commands | [QUICKSTART.md](QUICKSTART.md) |
| Project status | [SUMMARY.md](SUMMARY.md) |
| Detailed architecture | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Optimizations done | [app/docs/IMPROVEMENTS_SUMMARY.md](app/docs/IMPROVEMENTS_SUMMARY.md) |
| Intent detection | [app/docs/INTENT_DETECTION.md](app/docs/INTENT_DETECTION.md) |
| Grafana setup | [app/docs/OTLP_INTEGRATION.md](app/docs/OTLP_INTEGRATION.md) |
| Observability status | [app/docs/OTLP_STATUS.md](app/docs/OTLP_STATUS.md) |
| Troubleshooting | [QUICKSTART.md](QUICKSTART.md) + [README.md](README.md) |
| Migration | [MIGRATION.md](MIGRATION.md) |

---

**Last updated:** January 19, 2026  
**Maintained by:** Lab-toolchains team
