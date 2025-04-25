# Language data

## Overview

Simple repository to generate a language statistic dataset

## Licensing

I didn't check the data source licences, so do whatever you want with the source code but
take care the data material fill your needs.

## Build requirement

* Python 3.12+ (actually it might work for lower version as well)

## Data sources

* Statistics about countries: [CIA World Factbook](https://www.cia.gov/the-world-factbook/field/languages/)
* Language codes: [umpirsky](https://github.com/umpirsky/language-list/blob/master/data/en/language.json)
* Country codes: [umpirsky](https://github.com/umpirsky/country-list/blob/master/data/en/country.json)

## TODO

* Check data licensing
* Normalize which iso code is used
* Document parsing heuristics
* Find better suited data source
