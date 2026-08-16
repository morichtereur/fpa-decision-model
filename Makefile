.PHONY: install extract backtest scenario report commentary test api web web-install

install:      ; pip install -r requirements-dev.txt
extract:      ; python -m src.extract
backtest:     ; python -m src.backtest
scenario:     ; python -m src.scenario
report:       ; python -m src.report
commentary:   ; python -m api.generate_commentary
test:         ; python -m pytest tests/ -q

# Interactive FP&A Decision Cockpit (api/ + web/) — see README "Run the cockpit".
api:          ; uvicorn api.main:app --reload --port 8000
web-install:  ; cd web && npm install
web:          ; cd web && npm run dev
