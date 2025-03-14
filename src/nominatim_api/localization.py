# SPDX-License-Identifier: GPL-3.0-or-later
#
# This file is part of Nominatim. (https://nominatim.org)
#
# Copyright (C) 2024 by the Nominatim developer community.
# For a full list of authors see the git log.
"""
Helper functions for localizing names of results.
"""
import re
import json

from pathlib import Path
from typing import Mapping, List, Optional, Union
from .logging import log
from .config import Configuration


class Locales:
    """ Helper class for localization of names.

        It takes a list of language prefixes in their order of preferred
        usage.
    """

    def __init__(self, langs: Optional[List[str]] = None,
                 project_dir: Optional[Union[str, Path]] = None,
                 environ: Optional[Mapping[str, str]] = None):
        self.config = Configuration(project_dir, environ)
        self.languages = langs or []

        try:
            self.output_names_config = (
                self.config.load_sub_configuration('', config='OUTPUT_NAMES_CONFIG')
            )
        except KeyError:
            self.output_names_config = (
                json.loads("""{"prio1": {"with_lang": "name,brand,fallback",
                             "without_lang": "name"},
                             "prio2": {"with_lang": "official_name,short_name,ref",
                             "without_lang": "official_name,short_name"}}""")
            )

        self.name_tags: List[str] = []

        log().var_dump('Output name tags list 1', self.name_tags)

        log().section('<h1>Localization</h1>')
        log().var_dump('Output names', self.output_names_config)

        for prio in self.output_names_config:
            for lang_key in self.output_names_config[prio]:
                self.output_names_config[prio][lang_key] = (
                    self.output_names_config[prio][lang_key].split(",")
                )

        # Build the list of supported tags. It is currently hard-coded.
        self._add_lang_tags(*self.output_names_config["prio1"]["with_lang"])
        self._add_tags(*self.output_names_config["prio1"]["without_lang"])
        self._add_lang_tags(*self.output_names_config["prio2"]["with_lang"])
        self._add_tags(*self.output_names_config["prio2"]["without_lang"])

        log().var_dump('Output name tags list 2', self.name_tags)

    def __bool__(self) -> bool:
        return len(self.languages) > 0

    def _add_tags(self, *tags: str) -> None:
        for tag in tags:
            self.name_tags.append(tag)
            self.name_tags.append(f"_place_{tag}")

    def _add_lang_tags(self, *tags: str) -> None:
        for tag in tags:
            for lang in self.languages:
                self.name_tags.append(f"{tag}:{lang}")
                self.name_tags.append(f"_place_{tag}:{lang}")

    def display_name(self, names: Optional[Mapping[str, str]]) -> str:
        """ Return the best matching name from a dictionary of names
            containing different name variants.

            If 'names' is null or empty, an empty string is returned. If no
            appropriate localization is found, the first name is returned.
        """
        if not names:
            return ''

        if len(names) > 1:
            for tag in self.name_tags:
                if tag in names:
                    return names[tag]

        # Nothing? Return any of the other names as a default.
        return next(iter(names.values()))

    @staticmethod
    def from_accept_languages(langstr: str) -> 'Locales':
        """ Create a localization object from a language list in the
            format of HTTP accept-languages header.

            The functions tries to be forgiving of format errors by first splitting
            the string into comma-separated parts and then parsing each
            description separately. Badly formatted parts are then ignored.
        """
        # split string into languages
        candidates = []
        for desc in langstr.split(','):
            m = re.fullmatch(r'\s*([a-z_-]+)(?:;\s*q\s*=\s*([01](?:\.\d+)?))?\s*',
                             desc, flags=re.I)
            if m:
                candidates.append((m[1], float(m[2] or 1.0)))

        # sort the results by the weight of each language (preserving order).
        candidates.sort(reverse=True, key=lambda e: e[1])

        # If a language has a region variant, also add the language without
        # variant but only if it isn't already in the list to not mess up the weight.
        languages = []
        for lid, _ in candidates:
            languages.append(lid)
            parts = lid.split('-', 1)
            if len(parts) > 1 and all(c[0] != parts[0] for c in candidates):
                languages.append(parts[0])

        return Locales(languages)
