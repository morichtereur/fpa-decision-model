.PHONY: install extract backtest test

install:  ; pip install -r requirements-dev.txt
extract:  ; python -m src.extract
backtest: ; python -m src.backtest
test:     ; python -m pytest tests/ -q
