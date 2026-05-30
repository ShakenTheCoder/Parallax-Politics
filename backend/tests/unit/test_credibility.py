from app.search.credibility import credibility_for, domain_of, is_primary


def test_primary_sources_score_highest():
    assert credibility_for("https://senate.gov.ph/x") >= 0.95
    assert credibility_for("https://comelec.gov.ph/y") >= 0.95
    assert is_primary("https://senate.gov.ph/x")


def test_established_outlets():
    assert 0.7 <= credibility_for("https://www.rappler.com/foo") <= 0.95
    assert 0.7 <= credibility_for("https://newsinfo.inquirer.net/bar") <= 0.95


def test_unknown_domain_low_default():
    assert credibility_for("https://random.example/x") < 0.5


def test_subdomain_inherits_with_discount():
    parent = credibility_for("https://gmanetwork.com/x")
    sub = credibility_for("https://blogs.gmanetwork.com/y")
    assert sub < parent and sub > 0.0


def test_domain_of_strips_www():
    assert domain_of("https://www.rappler.com/x") == "rappler.com"
