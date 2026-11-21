import pytest

from autosales import clustering, segmentation
from autosales.data import build_customer_features, build_order_lines, build_order_summary, load_raw


@pytest.fixture(scope="session")
def lines():
    return build_order_lines(load_raw())


@pytest.fixture(scope="session")
def orders(lines):
    return build_order_summary(lines)


@pytest.fixture(scope="session")
def customers(lines, orders):
    cust = segmentation.add_rfm(build_customer_features(lines, orders))
    cust, _, _ = clustering.fit_clusters(cust)
    return cust
