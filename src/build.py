#!/usr/bin/env python

import json
import pathlib
import dataclasses
import re
import unicodedata
from typing import Any


@dataclasses.dataclass
class LanguageInfo:
    full_descr: str
    name: str
    code: str|None
    percent: float|None
    official: bool
    index: int


def split_lang_descr(descr:str) -> list[str]:
    ''' Split language list description by comma, taking care of parenthesis'''
    results = []

    cursor = 0
    lng_start = 0
    inside_parenthesis = False
    while cursor < len(descr):
        if inside_parenthesis:
            parenthesis_pos = descr.find(")", cursor)
            cursor = len(descr) if parenthesis_pos == -1 else parenthesis_pos+1
            inside_parenthesis = False
            if parenthesis_pos == -1:
                results.append(descr[lng_start:cursor-1].strip())
        else:
            parenthesis_pos = descr.find("(", cursor)
            comma_pos = descr.find(",", cursor)
            if parenthesis_pos == -1 and comma_pos == -1:
                cursor = len(descr)
                results.append(descr[lng_start:cursor-1].strip())
            elif comma_pos != -1 and (parenthesis_pos == -1 or comma_pos < parenthesis_pos):
                cursor = comma_pos+1
                results.append(descr[lng_start:cursor-1].strip())
                lng_start = cursor
            elif parenthesis_pos != -1:
                cursor = parenthesis_pos+1
                inside_parenthesis = True
    return results


def parse_langs(language_codes: dict[str, str], list_descr:str) -> list[LanguageInfo]:
    ''' Try to parse language info into structured data'''
    result = []
    for index, descr in enumerate(split_lang_descr(list_descr)):
        percent = None
        if m := re.search(r'((?:[0-9]{1,3}(?:[.,][0-9]{0,10})?)|(?:[.,][0-9]{1,10})) ?%', descr):
            percent = float(m.group(1))
        official = "official" in descr.lower()
        if m := re.search(r'^[a-zA-Z -]+', descr):
            name = m.group(0).strip().lower()
        else:
            name = descr.lower()
        code = find_language_code(language_codes, name)
        result.append(LanguageInfo(descr, name, code, percent, official, index))
    return result


def format(lng_list:list[LanguageInfo]) -> dict[str, Any]:
    # Filter languages to try to keep only relevent data
    printable_lngs = [l for l in lng_list if l.code is not None or (l.index < 5 or l.percent is not None)]
    for l in lng_list:
        if l.code is None and l.percent is not None and l.percent > 5:
            print("Warning: ignoring lang "+repr(l))
    return [{
        "label": lng.name,
        "code": lng.code,
        "percent": lng.percent,
        "official": lng.official,
        "position": lng.index+1
    } for lng in printable_lngs]


def _find_language_code(codes:dict[str, str], name:str) -> str|None:
    language_code = codes.get(name, None)
    if language_code is not None:
        return language_code
    return None

def find_language_code(codes:dict[str, str], language_name:str) -> str|None:
    ignored_words = ["only"]
    replaced_words = {}

    name = ' '.join([
        replaced_words[n] if n in replaced_words.keys() else n
        for n in language_name.lower().split()
        if n not in ignored_words
    ]) 

    result = _find_language_code(codes, name)
    if result is not None:
        return result

    if " or " in name:
        names = [n.strip() for n in name.split(" or ")]
        for subname in names:
            result = find_language_code(codes, subname)
            if result is not None:
                return result
        return None

    print("Warning: no language code found for "+language_name)
    return None


def _find_country_code(codes:dict[str, str], name:str) -> str|None:
    country_code = codes.get(name, None)
    if country_code is not None:
        return country_code
    return None

def find_country_code(codes:dict[str, str], country_name:str) -> str|None:
    # Sanitize name
    ignored_words = ["the", "only"]
    replaced_words = {"and": "&", "saint": "st."}

    name = ' '.join([
        replaced_words[n] if n in replaced_words.keys() else n
        for n in country_name.lower().split()
        if n not in ignored_words
    ])
    
    # Not std code:
    if name == "kosovo":
        return "XK"

    # Some name aliases, because I'm not matching every thing
    match name:
        case "burma": name = "myanmar (burma)"
        case "cabo verde": name = "cape verde"
        case "congo, democratic republic of": name = "congo - kinshasa"
        case "congo, republic of": name = "congo - brazzaville"
        case "gaza strip"|"west bank": name = "palestinian territories"
        case "hong kong": name = "hong kong sar china"
        case "macau": name = "macao sar china"
        case "svalbard": name = "svalbard & jan mayen"
        case "virgin islands": name = "british virgin islands"

    result = _find_country_code(codes, name)
    if result is not None:
        return result

    if " or " in name:
        names = [n.strip() for n in name.split(" or ")]
        for subname in names:
            result = find_country_code(codes, subname)
            if result is not None:
                return result
        return None
    
    if "," in name:
        # We try inverted name, eg Korea, North => North Korea
        inverted_name = " ".join([s.strip() for s in name.split(",")[::-1]])
        country_code = _find_country_code(codes, inverted_name)
        if country_code is not None:
            return country_code

        # We try without the details, eg 'Micronesia, Federated States of' => 'Micronesia'
        short_name = name.split(",", 1)[0]
        country_code = _find_country_code(codes, short_name)
        if country_code is not None:
            return country_code

    # We check for alternate names, eg: Falkland Islands (Islas Malvinas)
    if m := re.match(r'^(.*) \((.*)\)$', name):
        second_name = m.group(2).strip()
        country_code = _find_country_code(codes, second_name)
        if country_code is not None:
            return country_code
        first_name = m.group(1).strip()
        country_code = _find_country_code(codes, first_name)
        if country_code is not None:
            return country_code
    print("Warning: no country code found for "+country_name + "("+name+")")
    return None


def remove_special_chars(data:str) -> str:
    return unicodedata.normalize('NFKD', data).encode('ascii', 'ignore').decode('utf-8')


def main():
    project_path = pathlib.Path(__file__).parent.parent
    data_file = str(project_path.joinpath("data/countries_data.json"))
    output_file = str(project_path.joinpath("build/languages.json"))

    with open(project_path.joinpath("data/country_code.json"), "r") as fh:
        country_codes = {remove_special_chars(v.lower()):k for k,v in json.load(fh).items()}
    with open(project_path.joinpath("data/language_code.json"), "r") as fh:
        language_codes = {v.lower():k for k,v in json.load(fh).items()}

    LNG_KEY = "People and Society: Languages"
    with open(data_file, "r") as dfh:
        raw_data = {k:v[LNG_KEY] for k,v in json.load(dfh).items() if LNG_KEY in v.keys()}

    lngs_by_country = {}
    for country_name, country_lng_list_descr in raw_data.items():
        country_code = find_country_code(country_codes, country_name)
        if country_code is None:
            # Skipping country we didn't find the code ...
            continue
        lngs_by_country[country_code] = parse_langs(language_codes, country_lng_list_descr)

    output = {k:format(v) for k,v in lngs_by_country.items()}
    output = {k:v for k,v in dict(sorted(output.items())).items() if v}

    with open(output_file, "w+") as fh:
        json.dump(output, fh, indent=2)



if __name__ == "__main__":
    main()