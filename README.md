# FactorioApiScraper

A small script that goes through the Factorio API documentation html and exports
JSON intended to be used by autocomplete extensions such as https://github.com/simonvizzini/vscode-factorio-lua-api-autocomplete

## Usage

Generate `defines.json` and `classes.json` files by executing one of the following:

### Via python

- Install Python 3.7+ & BeautifulSoup (`bs4`)
- `python Scraper.py`

### Via docker

```sh
# optional: docker build -t cdaringe/factorio-api-scraper .
docker run --rm -v $PWD:/app cdaringe/factorio-api-scraper
```
