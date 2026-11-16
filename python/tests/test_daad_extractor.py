"""Unit tests for the DAAD listing-only funding_programmes parser."""

from __future__ import annotations

from pathlib import Path

from scrapagents.extractors.daad.extractor import (
    parse_catalogue_nuxt,
    parse_listing_page,
    parse_teaser_articles,
    parse_thematic_page,
    programme_slug_from_url,
)

FIXTURES = Path(__file__).parent / "fixtures" / "daad"
SITE = "https://www.daad.de"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_programme_slug_from_url_uses_last_segment():
    assert (
        programme_slug_from_url(
            "https://www.daad.de/de/infos-services-fuer-hochschulen/weiterfuehrende-infos-zu-daad-foerderprogrammen/african-excellence-fachzentren-afrika/",
            "ignored",
        )
        == "african-excellence-fachzentren-afrika"
    )


def test_catalogue_nuxt_emits_language_prefixed_ids():
    listing = (
        f"{SITE}/de/infos-services-fuer-hochschulen/"
        "weiterfuehrende-infos-zu-daad-foerderprogrammen/"
    )
    records = parse_catalogue_nuxt(_read("catalogue_de.html"), listing_url=listing, site=SITE)
    assert len(records) == 2
    assert records[0]["programme_id"].startswith("de:")
    assert records[0]["page_kind"] == "catalogue_programme"
    assert records[0]["language"] == "de"
    assert records[0]["listing_url"] == listing
    assert records[0]["source_url"].startswith(SITE)
    assert records[0]["title"]
    ids = [r["programme_id"] for r in records]
    assert len(ids) == len(set(ids))


def test_hei_teasers_skip_external_hosts():
    listing = f"{SITE}/en/information-services-for-higher-education-institutions/"
    records = parse_teaser_articles(_read("hei_en.html"), listing_url=listing, site=SITE)
    assert len(records) >= 2
    assert all(r["language"] == "en" for r in records)
    assert all(r["page_kind"] == "thematic_initiative" for r in records)
    assert all("dwih-netzwerk.de" not in r["source_url"] for r in records)
    assert all(r["programme_id"].startswith("en:") for r in records)


def test_thematic_page_one_grain():
    listing = (
        f"{SITE}/en/information-services-for-higher-education-institutions/"
        "expertise-on-subjects-countries-regions/campus-initiative-international-academic-experts/"
    )
    records = parse_thematic_page(_read("campus_en.html"), listing_url=listing, site=SITE)
    assert len(records) == 1
    assert records[0]["programme_slug"] == "campus-initiative-international-academic-experts"
    assert records[0]["programme_id"] == "en:campus-initiative-international-academic-experts"
    assert records[0]["source_url"] == listing


def test_parse_listing_page_routes():
    cat = parse_listing_page(
        _read("catalogue_de.html"),
        listing_url=f"{SITE}/de/infos-services-fuer-hochschulen/weiterfuehrende-infos-zu-daad-foerderprogrammen/",
        site=SITE,
    )
    assert len(cat) == 2
    assert cat[0]["page_kind"] == "catalogue_programme"

    hub = parse_listing_page(
        _read("hei_en.html"),
        listing_url=f"{SITE}/en/information-services-for-higher-education-institutions/",
        site=SITE,
    )
    assert hub and hub[0]["page_kind"] == "thematic_initiative"

    campus = parse_listing_page(
        _read("campus_en.html"),
        listing_url=(
            f"{SITE}/en/information-services-for-higher-education-institutions/"
            "expertise-on-subjects-countries-regions/campus-initiative-international-academic-experts/"
        ),
        site=SITE,
    )
    assert len(campus) == 1
