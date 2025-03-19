```
# Interaxx

**Interaxx** is a Python-based tool for sending customized HTTP requests to subdomains or URLs. With its flexibility, Interaxx allows users to configure custom headers, set time delays, and log detailed request and response information. It's particularly useful for testing and exploring web interactions efficiently.

## Features

- Send HTTP requests to multiple URLs from a file or a single URL.
- Support for custom HTTP headers (e.g., `Referer`, `User-Agent`, `X-Forwarded-For`).
- Option to set a time delay between requests to control execution flow.
- Results can be displayed in the terminal and optionally saved to a file.
- Debug mode for troubleshooting and enhanced visibility into request processes.
- Displays an attractive ASCII art banner for the tool name during startup.

## Installation

### Requirements

1. Install Python 3.x on your system.
2. Install required dependencies using the following command:
   ```bash
   pip3 install -r requirements.txt
   ```

### `requirements.txt`:

```plaintext
colorama==0.4.6
pyfiglet==0.8.post1
requests==2.31.0
urllib3==1.26.15
```

## Usage

Run the script via the command line with various configurable options.

### Command-Line Arguments

| Argument           | Description                                                                                              |
|--------------------|----------------------------------------------------------------------------------------------------------|
| `-f`, `--file`     | Path to the input file containing URLs.                                                                  |
| `-u`, `--url`      | A single URL to send the request to.                                                                     |
| `-o`, `--output`   | Path to the output file where results will be saved.                                                     |
| `-d`, `--debug`    | Enable debug messages for verbose logs.                                                                  |
| `-H`, `--header`   | Custom header key for payloads (e.g., `Referer`, `User-Agent`, `X-Forwarded-For`). Defaults to `Referer`. |

### Examples

1. **Send requests using a file with a custom header**:
   ```bash
   python interaxx.py -f urls.txt -H "User-Agent" -o results.txt
   ```

2. **Send a single request with a `Referer` header**:
   ```bash
   python interaxx.py -u "https://example.com" -H "Referer"
   ```

3. **Enable debug mode for detailed logging**:
   ```bash
   python interaxx.py -f urls.txt -d
   ```

4. **Specify a custom delay between requests**:
   - The script will prompt you to enter the time delay when executed:
     ```plaintext
     Enter the time delay (in seconds) between requests: 2
     ```

## Output

- **Terminal**: Displays the details for each request:
  - URL
  - Custom header key and value
  - Response code
  - Redirected URL (if applicable)
  
- **File**: Saves the results to the specified output file if the `-o` argument is used.

### Sample Terminal Output:

```plaintext
 python3 script.py -f /home/kali/vdp/live_subdomains.txt -H X-Forwarded-For
    ____      __
   /  _/___  / /____  _________ __  ___  __
   / // __ \/ __/ _ \/ ___/ __ `/ |/_/ |/_/
 _/ // / / / /_/  __/ /  / /_/ />  <_>  <
/___/_/ /_/\__/\___/_/   \__,_/_/|_/_/|_|


Author: @MrGreyHat
Enter the OAST domain: cvd7sc9on5bs78io92n04c954hbdxe6s8.oast.site
Enter the time delay (in seconds) between requests: 5
#1[2025-03-19 14:07:55] Sending request to: https://sa.services.target.com
  [2025-03-19 14:07:55] X-Forwarded-For: http://1.cvd7sc9on5bs78io92n04c954hbdxe6s8.oast.site
  [2025-03-19 14:07:55] Response Code: 302
  [2025-03-19 14:07:55] Redirected URI: https://sa.services.target.com/

#2[2025-03-19 14:08:00] Sending request to: http://sa.services.target.com
  [2025-03-19 14:08:00] X-Forwarded-For: http://2.cvd7sc9on5bs78io92n04c954hbdxe6s8.oast.site
  [2025-03-19 14:08:00] Response Code: 200
  [2025-03-19 14:08:00] Redirected URI: http://sa.services.target.com/
```

## How It Works

1. **Custom Header Support**:
   - Use the `-H` or `--header` flag to specify a custom header key.
   - The payloads will be sent as values in the specified header.

2. **Time Delay**:
   - The script prompts the user to set a time delay between requests to manage pacing.

3. **OAST Domain Integration**:
   - URLs in the header include dynamic referencing using the specified OAST domain.

## Contributing

Contributions are welcome! Feel free to fork this repository, submit issues, or create pull requests for new features and improvements.

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT). See the `LICENSE` file for more details.

---

Developed with 💡 by **@MrGreyHat**.
