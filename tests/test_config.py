from src import config as C


def test_paths_are_under_root():
    assert C.RAW == C.DATA / "raw"
    assert C.FACTS == C.DATA / "facts"


def test_scope_is_fixed_to_one_company():
    assert C.COMPANY == "Henkel AG & Co. KGaA"
    assert C.SEGMENTS == ["Adhesive Technologies", "Consumer Brands"]
    assert C.FISCAL_YEARS == [2023, 2024, 2025]
