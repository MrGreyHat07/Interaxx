import argparse
import asyncio
import csv
import json
import sys
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from playwright.async_api import async_playwright
from rich.console import Console
import pyfiglet
import traceback

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
    console.print("[italic green]Intelligent Header & Parameter Scanner (v1.1)[/italic green]")
    console.print("[bold yellow]by Deepak Rawat[/bold yellow]\n")

# ------------------- Injection Helpers -------------------
async def build_injected_headers(payload_domain, mapping, target, counter, mapping_lock):
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
async def process_target(url, args, state, console, context):
    mapping = state["mapping"]
    counter = state["counter"]
    mapping_lock = state["mapping_lock"]
    timeout = args.timeout

    parsed = urlparse(url)
    scheme = parsed.scheme or "http"
    netloc = parsed.netloc if parsed.netloc else parsed.path
    target = f"{scheme}://{netloc}"

    try:
        # Injection logic
        if args.subs:
            headers, _ = await build_injected_headers(
                args.payload_domain, mapping, target, counter, mapping_lock
            )
            test_url = target
            req_headers = headers
        else:
            test_url, _ = await inject_query_params(
                url, args.payload_domain, mapping, url, counter, mapping_lock
            )
            req_headers = {}  # No header injection in --urls mode

        # Debug: Request info
        if args.debug or args.debug_req:
            console.print(f"[blue][Request][/blue] URL: {test_url}")
            console.print(f"[blue][Request][/blue] Headers: {req_headers}")

        page = await context.new_page()

        if req_headers:
            await context.set_extra_http_headers(req_headers)

        requests = []

        async def on_request(request):
            requests.append({
                "type": "request",
                "url": request.url,
                "method": request.method,
                "headers": dict(request.headers),
            })

        async def on_response(response):
            try:
                body = await response.body()
                requests.append({
                    "type": "response",
                    "url": response.url,
                    "status": response.status,
                    "headers": dict(response.headers),
                    "body_len": len(body),
                })
                # Handle redirects
                if 300 <= response.status < 400 and not args.follow_redirects:
                    await page.close()
            except Exception:
                requests.append({
                    "type": "response",
                    "url": response.url,
                    "status": response.status,
                    "headers": dict(response.headers),
                    "body_len": None,
                })

        page.on("request", on_request)
        page.on("response", on_response)

        try:
            await page.goto(test_url, wait_until="networkidle", timeout=timeout * 1000)
        except Exception as e:
            console.print(f"[red][✗][/red] {url} - Error: {str(e)}")
            await page.close()
            return False

        if args.debug or args.debug_resp:
            console.print(f"[green][Response][/green] URL: {test_url}")
            for r in requests:
                if r["type"] == "response":
                    console.print(
                        f"[green][Response][/green] {r['url']} Status: {r['status']} BodyLen: {r['body_len']}"
                    )

        await page.close()
        console.print(f"[✓] {url} - Tested successfully")
        return True

    except Exception as ex:
        console.print(f"[red][✗][/red] {url} - Exception: {type(ex).__name__}: {ex}")
        if args.debug:
            traceback.print_exc()
        return False

# ------------------- Main async function -------------------
async def main_async(args):
    console = Console()
    print_banner()

    if args.subs:
        with open(args.subs, "r") as f:
            targets = [line.strip() for line in f if line.strip()]
    elif args.urls:
        with open(args.urls, "r") as f:
            targets = [line.strip() for line in f if line.strip()]
    else:
        targets = [line.strip() for line in sys.stdin if line.strip()]

    state = {
        "mapping": {},
        "counter": [1],
        "mapping_lock": asyncio.Lock(),
    }

    semaphore = asyncio.Semaphore(args.threads)
    success_count = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        async def sem_task(url):
            async with semaphore:
                return await process_target(url, args, state, console, context)

        tasks = [asyncio.create_task(sem_task(t)) for t in targets]
        done, _ = await asyncio.wait(tasks)

        for task in done:
            if task.result():
                success_count += 1

        await browser.close()

    console.print(f"\n[bold green]Scan complete.[/bold green] {success_count}/{len(targets)} targets succeeded.")

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

# ------------------- Argument parser -------------------
def parse_args():
    parser = argparse.ArgumentParser(description="Interaxx - Intelligent Header & Parameter Scanner")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-s", "--subs", help="File containing list of subdomains (only header injection)")
    group.add_argument("-u", "--urls", help="File containing list of URLs (query param injection only)")

    parser.add_argument("-d", "--payload-domain", required=True, help="Collaborator payload domain")
    parser.add_argument("-t", "--threads", type=int, default=5, help="Concurrent tasks (default: 5)")
    parser.add_argument("--timeout", type=int, default=15, help="Timeout per request (default: 15s)")
    parser.add_argument("--follow-redirects", action="store_true", help="Follow HTTP redirects")
    parser.add_argument("-o", "--output", help="Output log file (plain text)")
    parser.add_argument("--output-json", help="Output log file in JSON format")
    parser.add_argument("--output-csv", help="Output log file in CSV format")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--debug-req", action="store_true", help="Show only request info")
    parser.add_argument("--debug-resp", action="store_true", help="Show only response info")
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
