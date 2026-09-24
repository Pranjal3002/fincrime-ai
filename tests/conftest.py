import pandas as pd
import pytest

from fincrime_ai.features import build_features
from fincrime_ai.ingestion import generate
from fincrime_ai.rules import apply_rules
from fincrime_ai.screening import EntityMatcher
from fincrime_ai.settings import controls


@pytest.fixture(scope="session")
def raw():
    return generate(2500, 42, 100, 100)


@pytest.fixture(scope="session")
def features(raw):
    customers, cp, tx, watch = raw
    matcher = EntityMatcher(watch)
    screened = pd.DataFrame(
        [
            {
                "counterparty_id": int(row.counterparty_id),
                **matcher.screen(row.counterparty_name, row.country),
            }
            for row in cp.itertuples()
        ]
    )
    return apply_rules(
        build_features(tx, customers, cp, screened, controls()), controls()
    )
