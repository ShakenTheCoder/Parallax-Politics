from app.services.wikidata_glossary import (
    _account,
    _commons_source,
    _official_account,
    _values,
)


def test_wikidata_account_urls_are_constructed_from_claims() -> None:
    account = _account("X", "example_handle", "https://www.wikidata.org/wiki/Q1")

    assert account["url"] == "https://x.com/example_handle"
    assert account["verification"] == "claimed_on_wikidata"
    assert account["source_url"] == "https://www.wikidata.org/wiki/Q1"


def test_official_youtube_handle_uses_handle_url() -> None:
    account = _official_account("YouTube", "ExampleChannel", "https://senate.gov.ph")

    assert account["url"] == "https://www.youtube.com/@ExampleChannel"
    assert account["verification"] == "listed_by_official_source"


def test_commons_source_points_to_file_page() -> None:
    source = _commons_source(
        "http://commons.wikimedia.org/wiki/Special:FilePath/Raffy%20Tulfo%20RK.jpg"
    )

    assert source == "https://commons.wikimedia.org/wiki/File:Raffy%20Tulfo%20RK.jpg"


def test_name_filter_limits_external_query_values() -> None:
    values, reverse = _values({"Nic Torre"})

    assert "Nicolas Torre" in values
    assert "Raffy Tulfo" not in values
    assert reverse["nicolas torre"] == "Nic Torre"
