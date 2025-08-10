````markdown
# Interaxx


**Interaxx** is an intelligent header and parameter injection scanner powered by [Playwright](https://playwright.dev/) designed to help security researchers and bug bounty hunters test for out-of-band vulnerabilities by injecting Burp Collaborator or similar payloads into HTTP headers and URL parameters.

---

## Features

- Injects unique Collaborator payloads into:
  - HTTP request headers (common headers like User-Agent, Referer, X-Forwarded-For, etc.)
  - URL query parameters (when using URL input mode)
- Supports two input modes:
  - **Subdomain mode:** tests headers only for a list of subdomains
  - **URL mode:** tests both query parameters and headers for a list of URLs
- Headless browser powered by Playwright to test resource loading and JavaScript-powered endpoints
- Concurrency support via threading flag to speed up scanning
- Configurable timeout and follow redirects flag
- Multi-format output: plain text, JSON, and CSV
- Debug mode to inspect requests and responses in detail
- Clean and colorful console output for easy monitoring

---

## Installation

1. Clone the repo or download `interaxx.py`.
2. Install dependencies:
````
```bash
pip3 install -r requirements.txt
playwright install
```


3. (Optional) Install via setup:

```bash
python setup.py install
```

---

## Usage

```bash
usage: interaxx.py [-h] (-s SUBS | -u URLS) -d PAYLOAD_DOMAIN
                   [-t THREADS] [--timeout TIMEOUT] [--follow-redirects]
                   [-o OUTPUT] [--output-json OUTPUT_JSON]
                   [--output-csv OUTPUT_CSV] [--debug] [--debug-req]
                   [--debug-resp]

Interaxx - Intelligent Header & Parameter Scanner

optional arguments:
  -h, --help            show this help message and exit
  -s SUBS, --subs SUBS  File containing list of subdomains (header injection)
  -u URLS, --urls URLS  File containing list of URLs (header + param injection)
  -d PAYLOAD_DOMAIN, --payload-domain PAYLOAD_DOMAIN
                        Collaborator payload domain (e.g. abc123.burpcollaborator.net)
  -t THREADS, --threads THREADS
                        Number of concurrent tasks (default: 5)
  --timeout TIMEOUT     Timeout in seconds for each request (default: 15)
  --follow-redirects    Follow HTTP redirects
  -o OUTPUT, --output OUTPUT
                        Output log file (plain text)
  --output-json OUTPUT_JSON
                        Output log file in JSON format
  --output-csv OUTPUT_CSV
                        Output log file in CSV format
  --debug               Enable debug mode (show request and response info)
  --debug-req           Show only request info
  --debug-resp          Show only response info
```

---

### Examples

* Scan a list of subdomains (headers only):

```bash
python interaxx.py --subs subdomains.txt -d yourcollab.oast.pro
```

* Scan a list of URLs (query parameters + headers):

```bash
python interaxx.py --urls urls.txt -d yourcollab.oast.pro -t 10 --timeout 10 --debug
```

* Save output logs:

```bash
python interaxx.py --subs subdomains.txt -d yourcollab.oast.pro -o output.txt --output-json output.json --output-csv output.csv
```

---

## Requirements

* Python 3.7+
* [Playwright](https://playwright.dev/python/docs/intro) (including browsers)
* rich
* pyfiglet

---

## Notes

* Playwright browsers must be installed with `playwright install` after installing dependencies.
* Redirects are followed by default (Playwright behavior).
* Use debug flags for detailed request and response inspection.
* Unique payload IDs are generated to correlate Collaborator interactions.

---

## Author

**Deepak Rawat**
Security Researcher & Bug Bounty Hunter

---

## License

MIT License

---
```
Feel free to contribute or report issues!
```

