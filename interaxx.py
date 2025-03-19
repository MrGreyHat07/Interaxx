import time
import requests
from datetime import datetime
import argparse
import warnings
from urllib3.exceptions import InsecureRequestWarning
from colorama import Fore, Style, init
import sys
from pyfiglet import Figlet  # For ASCII art

# Initialize colorama
init()

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Send HTTP requests to subdomains.")
parser.add_argument("-f", "--file", type=str, help="Path to the input file containing URLs.")
parser.add_argument("-u", "--url", type=str, help="Single URL to send the request to.")
parser.add_argument("-o", "--output", type=str, help="Output file to save the results.")
parser.add_argument("-d", "--debug", action="store_true", help="Enable debug messages.")
parser.add_argument("-H", "--header", type=str, help="Custom header key (e.g., 'User-Agent', 'X-Forwarded-For').")
args = parser.parse_args()

# Suppress warnings unless debug mode is enabled
if not args.debug:
    warnings.filterwarnings("ignore", category=InsecureRequestWarning)

# Display ASCII art for the tool name in blue
ascii_art = Figlet(font="slant")
print(f"{Fore.BLUE}{Style.BRIGHT}{ascii_art.renderText('Interaxx')}{Style.RESET_ALL}")

# Print the author's name
print(f"{Fore.CYAN}{Style.BRIGHT}Author: @MrGreyHat{Style.RESET_ALL}")

# Ask the user for the OAST domain URL (without protocol)
oast_domain = input("Enter the OAST domain: ")

# Validate the input OAST domain
if not oast_domain:
    print("Invalid OAST domain. Please provide a valid domain.")
    sys.exit(1)

# Ask the user for the time delay between requests
try:
    time_delay = float(input("Enter the time delay (in seconds) between requests: "))
    if time_delay < 0:
        raise ValueError("Time delay must be a non-negative number.")
except ValueError as e:
    print(f"Invalid time delay value: {e}")
    sys.exit(1)

# Read the list of URLs
if args.file:
    with open(args.file, "r") as file:
        urls = [line.strip() for line in file if line.strip()]
elif args.url:
    urls = [args.url]
else:
    print("Please specify either a file using -f/--file or a URL using -u/--url.")
    sys.exit(1)

# Prepare output file if specified
output_file = args.output
output_data = []  # To store the results if output file is specified

# Counter to track the number of requests
request_count = 0

try:
    # Send requests to each URL
    for index, url in enumerate(urls, start=1):
        try:
            # Ensure URL starts with a valid protocol
            if not url.startswith(("http://", "https://")):
                if args.debug:
                    print(f"Invalid protocol in URL: {url}. Skipping...")
                continue

            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Use the custom header if provided, otherwise default to 'Referer'
            header_key = args.header if args.header else "Referer"
            header_value = f"http://{index}.{oast_domain}"

            headers = {
                "User-Agent": "Mozilla/5.0 (Knoppix; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
                "Accept-Charset": "utf-8",
                "Accept-Encoding": "gzip",
                header_key: header_value
            }

            print(f"#{request_count + 1}{Fore.RED}[{timestamp}]{Style.RESET_ALL} Sending request to: {Fore.GREEN}{url}{Style.RESET_ALL}")
            print(f"  {Fore.RED}[{timestamp}]{Style.RESET_ALL} {header_key}: {headers[header_key]}")

            # Send the GET request with SSL verification disabled
            response = requests.get(url, headers=headers, verify=False)

            # Log the response status code
            output_entry = (
                f"Request #{request_count + 1} | "
                f"Timestamp: {timestamp} | "
                f"URL: {url} | "
                f"{header_key}: {header_value} | "
                f"Response Code: {response.status_code} | "
                f"Redirected URL: {response.url}\n"
            )

            # Display response information
            print(f"  {Fore.RED}[{timestamp}]{Style.RESET_ALL} Response Code: {response.status_code}")
            print(f"  {Fore.RED}[{timestamp}]{Style.RESET_ALL} Redirected URI: {response.url}\n")

            # Increment the request counter
            request_count += 1

            # Save results to output file if specified
            if output_file:
                output_data.append(output_entry)

            # Wait for the user-specified delay before the next request
            time.sleep(time_delay)

        except requests.exceptions.RequestException as e:
            if args.debug:
                print(f"Error with {url}: {e}\n")

except KeyboardInterrupt:
    print(f"\n{Fore.YELLOW}Program interrupted by user. Exiting gracefully...{Style.RESET_ALL}")
    if output_file:
        with open(output_file, "w") as file:
            file.writelines(output_data)
        print(f"{Fore.CYAN}Output saved to: {output_file}{Style.RESET_ALL}")
    sys.exit(0)

# Save results to output file if specified (when program finishes normally)
if output_file:
    with open(output_file, "w") as file:
        file.writelines(output_data)
    print(f"{Fore.CYAN}Output saved to: {output_file}{Style.RESET_ALL}")

# Print the total count of requests made
print(f"Total requests made: {request_count}")
