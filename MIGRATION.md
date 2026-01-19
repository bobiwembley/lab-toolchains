# 📦 Migration Guide - New Structure

The project has been reorganized for better clarity between application code and infrastructure.

## 🔄 Structure Changes

### Before (flat structure)
```
lab-toolchains/
├── agents/
├── services/
├── tools/
├── utils/
├── docs/
├── grafana/
├── tempo/
├── prometheus/
├── otel-collector/
├── docker-compose.observability.yml
├── streamlit_app.py
└── requirements.txt
```

### After (organized structure)
```
lab-toolchains/
├── app/                     # 📱 APPLICATION
│   ├── agents/
│   ├── services/
│   ├── tools/
│   ├── utils/
│   ├── docs/
│   ├── streamlit_app.py
│   ├── main.py
│   └── requirements.txt
├── observability/           # 🐳 INFRASTRUCTURE
│   ├── docker-compose.yml
│   ├── grafana/
│   ├── tempo/
│   ├── prometheus/
│   └── otel-collector/
├── examples/                # 💡 Examples
├── tests/                   # ✅ Tests
├── logs/                    # 📝 Logs
├── README.md
├── QUICKSTART.md
└── ARCHITECTURE.md
```

## 🔧 Code Adaptation

### Python Imports

**Before:**
```python
from agents.travel_agent import TravelAgent
from tools.travel_tools import create_all_tools
```

**After:**
```python
# Option 1: Add to PYTHONPATH
import sys
sys.path.insert(0, 'app')

from agents.travel_agent import TravelAgent
from tools.travel_tools import create_all_tools

# Option 2: Use PYTHONPATH env
# export PYTHONPATH="${PYTHONPATH}:${PWD}/app"
```

### Streamlit Commands

**Before:**
```bash
streamlit run streamlit_app.py
```

**After:**
```bash
streamlit run app/streamlit_app.py
```

### Docker Commands

**Before:**
```bash
docker-compose -f docker-compose.observability.yml up -d
./start-observability.sh
```

**After:**
```bash
cd observability
docker-compose up -d
# or
./start-observability.sh
```

### Documentation Paths

**Before:**
```bash
cat docs/OTLP_STATUS.md
```

**After:**
```bash
cat app/docs/OTLP_STATUS.md
```

## 📝 Removed Files

The following files were cleaned up as unnecessary or duplicates:

- ✅ **test_*.py** (at root) - Temporary test files
- ✅ **__pycache__/** (outside .venv) - Compiled Python files
- ✅ **travel_map.html** - Generated file
- ✅ Duplicate folders after migration to app/

## 🚀 Required Actions

If you have custom scripts or configurations:

1. **Update Python imports** with `sys.path.insert(0, 'app')`
2. **Adjust Streamlit paths** to `app/streamlit_app.py`
3. **Change Docker commands** to use `cd observability`
4. **Update documentation references** to `app/docs/`

## ✅ Verification

Test that everything works:

```bash
# Test 1: Python imports
python -c "import sys; sys.path.insert(0, 'app'); from agents.travel_agent import TravelAgent; print('✅ Imports OK')"

# Test 2: Streamlit
streamlit run app/streamlit_app.py &
sleep 5
curl http://localhost:8501 && echo "✅ Streamlit OK"
pkill -f streamlit

# Test 3: Docker
cd observability
docker-compose ps
cd ..
echo "✅ Docker OK"

# Test 4: Documentation
ls app/docs/OTLP_STATUS.md && echo "✅ Docs OK"
```

## 📚 Resources

- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [README.md](README.md) - Updated main documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [app/docs/](app/docs/) - Technical documentation

## ❓ FAQ

**Q: Why this reorganization?**  
A: Clearly separating application code (app/) from infrastructure (observability/) improves maintainability and facilitates deployment.

**Q: Do old scripts still work?**  
A: No, paths need to be adapted (see "Code Adaptation" section above).

**Q: What about old files?**  
A: They were automatically migrated or removed. Check with `git status`.

**Q: Does the application work differently?**  
A: No, only file organization changed. Code and features remain identical.
