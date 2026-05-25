from parity_check.report.labels import endpoint_domain


def test_endpoint_domain_from_url():
    assert endpoint_domain("https://dev.cmp.xfin.net") == "dev.cmp.xfin.net"
    assert endpoint_domain("http://127.0.0.1:8080") == "127.0.0.1:8080"
