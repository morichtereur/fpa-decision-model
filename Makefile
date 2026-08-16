.PHONY: install extract backtest scenario report test

install:    ; pip install -r requirements-dev.txt
extract:    ; python -m src.extract
backtest:   ; python -m src.backtest
scenario:   ; python -m src.scenario
report:     ; python -m src.report
test:       ; python -m pytest tests/ -q
