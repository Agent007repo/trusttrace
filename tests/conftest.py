import pytest


@pytest.fixture(autouse=True)
def record_identity(request, record_property):
    record_property("nodeid", request.node.nodeid)
    for marker in request.node.iter_markers("requirement"):
        record_property("requirement", marker.args[0])
