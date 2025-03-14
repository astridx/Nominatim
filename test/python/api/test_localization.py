# SPDX-License-Identifier: GPL-3.0-or-later
#
# This file is part of Nominatim. (https://nominatim.org)
#
# Copyright (C) 2025 by the Nominatim developer community.
# For a full list of authors see the git log.
"""
Test functions for adapting results to the user's locale.
"""
import pytest

from nominatim_api import Locales
from nominatim_api import Configuration


def test_display_name_empty_names():
    loc = Locales(['en', 'de'])

    assert loc.display_name(None) == ''
    assert loc.display_name({}) == ''


def test_display_name_none_localized():
    loc = Locales()

    assert loc.display_name({}) == ''
    assert loc.display_name({'name:de': 'DE', 'name': 'ALL'}) == 'ALL'
    assert loc.display_name({'ref': '34', 'name:de': 'DE'}) == '34'


def test_output_names_none_localized():
    loc = Locales()

    expected_tags = [
        'name', '_place_name', 'brand', '_place_brand', 'official_name', '_place_official_name',
        'short_name', '_place_short_name', 'ref', '_place_ref'
    ]

    assert loc.name_tags == expected_tags, f'Expected {expected_tags}, but got {loc.name_tags}'


def test_output_names_none_localized_and_custom_output_names(monkeypatch):
    custom_config = {
        'prio1': {
            'with_lang': ['name', 'entrance'],
            'without_lang': ['name', 'brand', 'test_tag']
        },
        'prio2': {
            'with_lang': ['official_name', 'short_name', 'alt_name'],
            'without_lang': []
        }
    }

    def mock_load_sub_configuration(self, _filename):
        return custom_config

    monkeypatch.setattr(Configuration, 'load_sub_configuration', mock_load_sub_configuration)
    loc = Locales()

    expected_tags = [
        'name', '_place_name', 'brand', '_place_brand', 'test_tag', '_place_test_tag'
    ]

    assert loc.name_tags == expected_tags, f'Expected {expected_tags}, but got {loc.name_tags}'


def test_display_name_localized():
    loc = Locales(['en', 'de'])

    assert loc.display_name({}) == ''
    assert loc.display_name({'name:de': 'DE', 'name': 'ALL'}) == 'DE'
    assert loc.display_name({'ref': '34', 'name:de': 'DE'}) == 'DE'


def test_output_names_localized():
    loc = Locales(['en', 'es'])

    expected_tags = [
        'name:en', '_place_name:en', 'name:es', '_place_name:es', 'name', '_place_name', 'brand',
        '_place_brand', 'official_name:en', '_place_official_name:en', 'official_name:es',
        '_place_official_name:es', 'short_name:en', '_place_short_name:en', 'short_name:es',
        '_place_short_name:es', 'official_name', '_place_official_name', 'short_name',
        '_place_short_name', 'ref', '_place_ref'
    ]

    assert loc.name_tags == expected_tags, f'Expected {expected_tags}, but got {loc.name_tags}'


def test_output_names_localized_and_custom_output_names(monkeypatch):
    custom_config = {
        'prio1': {
            'with_lang': ['name', 'entrance'],
            'without_lang': ['name', 'brand', 'test_tag']
        },
        'prio2': {
            'with_lang': ['official_name', 'short_name', 'alt_name'],
            'without_lang': []
        }
    }

    def mock_load_sub_configuration(self, _filename):
        return custom_config

    monkeypatch.setattr(Configuration, 'load_sub_configuration', mock_load_sub_configuration)
    loc = Locales(['en', 'es'])

    expected_tags = [
        'name:en', '_place_name:en', 'name:es', '_place_name:es', 'entrance:en',
        '_place_entrance:en', 'entrance:es', '_place_entrance:es', 'name', '_place_name',
        'brand', '_place_brand', 'test_tag', '_place_test_tag', 'official_name:en',
        '_place_official_name:en', 'official_name:es', '_place_official_name:es',
        'short_name:en', '_place_short_name:en', 'short_name:es', '_place_short_name:es',
        'alt_name:en', '_place_alt_name:en', 'alt_name:es', '_place_alt_name:es'
    ]

    assert loc.name_tags == expected_tags, f'Expected {expected_tags}, but got {loc.name_tags}'


def test_display_name_preference():
    loc = Locales(['en', 'de'])

    assert loc.display_name({}) == ''
    assert loc.display_name({'name:de': 'DE', 'name:en': 'EN'}) == 'EN'
    assert loc.display_name({'official_name:en': 'EN', 'name:de': 'DE'}) == 'DE'


@pytest.mark.parametrize('langstr,langlist',
                         [('fr', ['fr']),
                          ('fr-FR', ['fr-FR', 'fr']),
                          ('de,fr-FR', ['de', 'fr-FR', 'fr']),
                          ('fr,de,fr-FR', ['fr', 'de', 'fr-FR']),
                          ('en;q=0.5,fr', ['fr', 'en']),
                          ('en;q=0.5,fr,en-US', ['fr', 'en-US', 'en']),
                          ('en,fr;garbage,de', ['en', 'de'])])
def test_from_language_preferences(langstr, langlist):
    assert Locales.from_accept_languages(langstr).languages == langlist
