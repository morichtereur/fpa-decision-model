.PHONY: install extract backtest scenario commentary test

install:    ; pip install -r requirements-dev.txt
extract:    ; python -m src.extract
backtest:   ; python -m src.backtest
scenario:   ; python -m src.scenario
test:       ; python -m pytest tests/ -q
