import argparse
import asyncio
import csv
import json
import sys
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from playwright.async_api import async_playwright
from rich.console import Console
import pyfiglet

# ------------------- Constants -------------------
COMMON_HEADERS = [
    "User-Agent",
    "Referer",
    "X-Forwarded-For",
    "X-Client-IP",
    "X-Real-IP",
    "X-Forwarded-Host",
    "X-Forwarded-Proto",
]

# ------------------- Banner -------------------
def print_banner():
    console = Console()
    ascii_art = pyfiglet.figlet_format("INTERAXX", font="slant")
    console.print(f"[bold cyan]{ascii_art}[/bold cyan]")
    console.print("[italic green]Intelligent Header & Parameter Scanner (v1.0)[/italic green]")
    console.print("[bold yellow]by Deepak Rawat[/bold yellow]\n")

# ------------------- Injection Helpers -------------------
async def build_injected_headers(payload_domain, mapping, target, counter, mapping_lock):
    """
    Build headers with unique Collaborator payloads injected,
    track them in mapping for later correlation.
    """
    headers = {}
    created_ids = []
    async with mapping_lock:
        for h in COMMON_HEADERS:
            token_id = str(counter[0])
            created_ids.append(token_id)
            mapping[token_id] = {
                "target": target,
                "injection_type": "header",
                "injection_point": h,
            }
            counter[0] += 1
    for idx, h in enumerate(COMMON_HEADERS):
        headers[h] = f"http://{created_ids[idx]}.{payload_domain}"
    return headers, created_ids


async def inject_query_params(url, payload_domain, mapping, target, counter, mapping_lock):
    """
    Replace all query param values with unique Collaborator payloads,
    track them in mapping for later correlation.
    """
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    new_qs = {}
    created_ids = []
    async with mapping_lock:
        for key in qs:
            token_id = str(counter[0])
            created_ids.append(token_id)
            mapping[token_id] = {
                "target": target,
                "injection_type": "query",
                "injection_point": key,
            }
            counter[0] += 1
    for idx, key in enumerate(qs):
        new_qs[key] = [f"http://{created_ids[idx]}.{payload_domain}"]
    new_url = urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            urlencode(new_qs, doseq=True),
            parsed.fragment,
        )
    )
    return new_url, created_ids


# ------------------- Core Processing -------------------
async def process_target(
    url,
    args,
    state,
    console,
):
    """
    Process a single URL or subdomain: inject payloads in headers and/or query params
    Send request via headless browser, collect response, log as needed.
    """
    mapping = state["mapping"]
    counter = state["counter"]
    mapping_lock = state["mapping_lock"]
    timeout = args.timeout

    # Parse target info
    parsed = urlparse(url)
    scheme = parsed.scheme or "http"
    netloc = parsed.netloc if parsed.netloc else parsed.path  # Handle if scheme missing

    target = f"{scheme}://{netloc}"

    try:
        # Headers injection for subs and urls both
        if args.subs:
            # Subdomain mode: inject headers only once per subdomain (netloc)
            headers, created_ids = await build_injected_headers(
                args.payload_domain, mapping, target, counter, mapping_lock
            )
            # URL stays same
            test_url = target
        else:
            # URLs mode: inject query params and headers both
            test_url, param_ids = await inject_query_params(
                url, args.payload_domain, mapping, url, counter, mapping_lock
            )
            headers, header_ids = await build_injected_headers(
                args.payload_domain, mapping, url, counter, mapping_lock
            )

        # Merge headers with any additional user headers if needed
        # Add headers for test
        if args.subs:
            req_headers = headers
        else:
            req_headers = headers

        # Debug output for request
        if args.debug or args.debug_req:
            console.print(f"[blue][Request][/blue] URL: {test_url}")
            console.print(f"[blue][Request][/blue] Headers: {req_headers}")

        # Use playwright to visit the URL and get response + resource loads
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            # Set extra headers on the page context
            await context.set_extra_http_headers(req_headers)

            # Event to capture all network requests and responses
            requests = []

            async def on_request(request):
                requests.append({"type": "request", "url": request.url, "method": request.method, "headers": dict(request.headers)})

            async def on_response(response):
                try:
                    body = await response.body()
                    requests.append({"type": "response", "url": response.url, "status": response.status, "headers": dict(response.headers), "body_len": len(body)})
                except Exception as e:
                    requests.append({"type": "response", "url": response.url, "status": response.status, "headers": dict(response.headers), "body_len": None})

            page.on("request", on_request)
            page.on("response", on_response)

            # Go to the URL with timeout and redirect options
            try:
                await page.goto(test_url, wait_until="networkidle", timeout=timeout * 1000)
            except Exception as e:
                console.print(f"[red][✗][/red] {url} - Error: {str(e)}")
                await browser.close()
                return False

            # Debug output for response
            if args.debug or args.debug_resp:
                console.print(f"[green][Response][/green] URL: {test_url}")
                for r in requests:
                    if r["type"] == "response":
                        console.print(f"[green][Response][/green] {r['url']} Status: {r['status']} BodyLen: {r['body_len']}")

            await browser.close()

        # Log output
        output_line = f"[✓] {url} - Tested successfully"
        console.print(output_line)

        # Save mapping if JSON/CSV requested (optional)
        if args.output_json or args.output_csv or args.output:
            # Save mapping at end - handled in main()
            pass

        return True

    except Exception as ex:
        console.print(f"[red][✗][/red] {url} - Exception: {ex}")
        return False


# ------------------- Main async function -------------------
async def main_async(args):
    console = Console()
    print_banner()

    # Load input URLs or subdomains
    if args.subs:
        with open(args.subs, "r") as f:
            targets = [line.strip() for line in f if line.strip()]
    elif args.urls:
        with open(args.urls, "r") as f:
            targets = [line.strip() for line in f if line.strip()]
    else:
        # Read from stdin fallback
        targets = [line.strip() for line in sys.stdin if line.strip()]

    # State shared across coros
    state = {
        "mapping": {},
        "counter": [1],  # mutable int for unique IDs
        "mapping_lock": asyncio.Lock(),
    }

    # Concurrency semaphore for threading
    semaphore = asyncio.Semaphore(args.threads)

    # Track results
    results = []

    async def sem_task(url):
        async with semaphore:
            return await process_target(url, args, state, console)

    # Run all tasks concurrently
    tasks = [asyncio.create_task(sem_task(t)) for t in targets]

    done, pending = await asyncio.wait(tasks)

    # Collect success/fail
    success_count = 0
    for task in done:
        res = task.result()
        if res:
            success_count += 1

    console.print(f"\n[bold green]Scan complete.[/bold green] {success_count}/{len(targets)} targets succeeded.")

    # Output mapping/logs if requested
    if args.output:
        with open(args.output, "w") as f:
            for key, val in state["mapping"].items():
                f.write(f"{key}: {val}\n")

    if args.output_json:
        with open(args.output_json, "w") as f:
            json.dump(state["mapping"], f, indent=2)

    if args.output_csv:
        with open(args.output_csv, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["TokenID", "Target", "Injection Type", "Injection Point"])
            for key, val in state["mapping"].items():
                writer.writerow([key, val.get("target"), val.get("injection_type"), val.get("injection_point")])

    return 0


# ------------------- Argument parser -------------------
def parse_args():
    parser = argparse.ArgumentParser(description="Interaxx - Intelligent Header & Parameter Scanner")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-s", "--subs", help="File containing list of subdomains (only header injection)")
    group.add_argument("-u", "--urls", help="File containing list of URLs (query param + header injection)")

    parser.add_argument(
        "-d", "--payload-domain",
        required=True,
        help="Collaborator payload domain (e.g. abc123.burpcollaborator.net)"
    )

    parser.add_argument(
        "-t", "--threads",
        type=int,
        default=5,
        help="Number of concurrent tasks (default: 5)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=15,
        help="Timeout in seconds for each request (default: 15)"
    )
    parser.add_argument(
        "--follow-redirects",
        action="store_true",
        help="Follow HTTP redirects"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output log file (plain text)"
    )
    parser.add_argument(
        "--output-json",
        help="Output log file in JSON format"
    )
    parser.add_argument(
        "--output-csv",
        help="Output log file in CSV format"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode (show request and response info)"
    )
    parser.add_argument(
        "--debug-req",
        action="store_true",
        help="Show only request info"
    )
    parser.add_argument(
        "--debug-resp",
        action="store_true",
        help="Show only response info"
    )

    return parser.parse_args()

# ------------------- Entry point -------------------
def main():
    args = parse_args()
    try:
        asyncio.run(main_async(args))
    except KeyboardInterrupt:
        print("\n[!] Exiting on user interrupt.")
        sys.exit(1)

if __name__ == "__main__":
    main()
