#!/usr/bin/env python3
"""
XSSdawn: A tool to crawl a target website, gather URLs (using built-in crawling, Waybackurls, and ParamSpider),
filter them using GF patterns, and then discover hidden parameters via Arjun.
Created by hunterdawn

This script will:
        - Download/build external tools if not already present:
                        * Waybackurls (by TomNomNom)
                        * gf (by TomNomNom) along with GF Patterns (by 1ndianl33t)
                        * Arjun (for scanning hidden parameters)
                        * ParamSpider (by devanshbatham)
        - Crawl the target website (via a built‐in crawler, Waybackurls, and ParamSpider)
        - Merge URLs and optionally filter them using gf patterns
        - Invoke Arjun on the target

Pre-requisites:
        - Git and Go must be installed manually (this script does not install Go).
        - Users should have a sufficiently recent Go version installed.
"""

import argparse
import os
import subprocess
import sys
import requests
from collections import deque
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from colorama import Fore, Style, init

# Initialize colorama for colored output.
init(autoreset=True)

###############################
#       Banner Function       #
###############################

def printBanner():
    banner = f"""
{Fore.GREEN}
 __  __ _____  _____ _____  _    _ _   _ 
|  \/  |  __ \|  __ \_   _|/ \  | | \ | |
| \  / | |  | | |  | || | / _ \ | |  \| |
| |\/| | |  | | |  | || |/ ___ \| | .  |
| |  | | |__| | |__| || /_/   \_\ | |\  |
|_|  |_|_____/|_____/|_|        |_| \_|

                                                 XSSdawn
                                 created by hunterdawn
{Style.RESET_ALL}
    """
    print(banner)

###############################
#     Tool Management Code    #
###############################

def ensure_dir(directory):
    if not os.path.isdir(directory):
        os.makedirs(directory)

def ensure_tool(tool_name, repo_url, build_commands, binary_relative_path):
    """
    Ensure that a given tool is downloaded and built.
    If a go.mod file is not present in the repo directory, it runs 'go mod init <tool_name>'.
    Returns the absolute path to the binary.
    NOTE: This script does not install Go. Ensure that Go is installed.
    Also, it disables automatic toolchain downloads by setting GOTOOLDOWNLOAD=off.
    """
    script_dir = os.path.dirname(os.path.realpath(__file__))
    tools_dir = os.path.join(script_dir, "tools")
    ensure_dir(tools_dir)
    tool_dir = os.path.join(tools_dir, tool_name)
    binary_path = os.path.join(tool_dir, binary_relative_path) if binary_relative_path else ""
    if binary_relative_path and os.path.isfile(binary_path):
        print(Fore.GREEN + f"[+] {tool_name} already exists.")
        return binary_path
    else:
        print(Fore.GREEN + f"[+] Downloading and building {tool_name}...")
        if not os.path.isdir(tool_dir):
            subprocess.run(["git", "clone", repo_url, tool_dir], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if build_commands and any("go build" in cmd for cmd in build_commands):
            if not os.path.isfile(os.path.join(tool_dir, "go.mod")):
                print(Fore.GREEN + f"[+] Initializing Go module for {tool_name}...")
                env = os.environ.copy()
                env["GOTOOLDOWNLOAD"] = "off"
                subprocess.run(["go", "mod", "init", tool_name], cwd=tool_dir, check=True, env=env)
        env = os.environ.copy()
        env["GOTOOLDOWNLOAD"] = "off"
        for cmd in build_commands:
            subprocess.run(cmd, shell=True, cwd=tool_dir, check=True, env=env)
        return os.path.join(tool_dir, binary_relative_path) if binary_relative_path else tool_dir

def ensure_repo(repo_name, repo_url):
    """
    Ensure a repository is cloned (used for gf patterns).
    Returns the path to the repository.
    """
    script_dir = os.path.dirname(os.path.realpath(__file__))
    tools_dir = os.path.join(script_dir, "tools")
    ensure_dir(tools_dir)
    repo_dir = os.path.join(tools_dir, repo_name)
    if not os.path.isdir(repo_dir):
        print(Fore.GREEN + f"[+] Cloning {repo_name} repository...")
        subprocess.run(["git", "clone", repo_url, repo_dir], check=True)
    else:
        print(Fore.GREEN + f"[+] {repo_name} already cloned.")
    return repo_dir

###############################
#         Crawling Code       #
###############################

def crawl_website(start_url, allow_subdomains=False, max_pages=100):
    """
    Crawl the website starting at start_url and return a set of URLs with query parameters.
    """
    visited = set()
    urls_with_params = set()
    queue = deque([start_url])
    base_netloc = urlparse(start_url).netloc

    while queue and len(visited) < max_pages:
        current_url = queue.popleft()
        if current_url in visited:
            continue
        visited.add(current_url)
        try:
            response = requests.get(current_url, timeout=10)
        except requests.RequestException as e:
            print(Fore.RED + f"[-] Error fetching {current_url}: {e}")
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        for link in soup.find_all("a", href=True):
            href = link["href"]
            absolute_url = urljoin(current_url, href)
            parsed = urlparse(absolute_url)
            if parsed.scheme not in ["http", "https"]:
                continue

            if not allow_subdomains:
                if parsed.netloc != base_netloc:
                    continue
            else:
                if base_netloc not in parsed.netloc:
                    continue

            if absolute_url not in visited:
                queue.append(absolute_url)
            if "?" in absolute_url:
                urls_with_params.add(absolute_url)
    return urls_with_params

###############################
#      External Tools Code    #
###############################

def run_waybackurls(wayback_path, target):
    """
    Run Waybackurls on the target domain.
    Returns a set of URLs.
    """
    try:
        proc = subprocess.run(f"echo {target} | {wayback_path}", shell=True, capture_output=True, text=True, check=True)
        output = proc.stdout.strip()
        if not output:
            print(Fore.YELLOW + "[!] Waybackurls returned no output.")
        urls = set(output.splitlines())
        print(Fore.GREEN + f"[+] Waybackurls returned {len(urls)} URLs.")
        return urls
    except subprocess.CalledProcessError as e:
        print(Fore.RED + f"[-] Error running Waybackurls: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return set()

def run_gf_filter(gf_path, gf_patterns_dir, input_file):
    """
    Use gf (with patterns from gf patterns repo) to filter URLs from the input file.
    Returns a set of filtered URLs.
    """
    filtered_urls = set()
    pattern_files = [f for f in os.listdir(gf_patterns_dir) if f.endswith(".json") or f.endswith(".txt")]
    for pattern in pattern_files:
        try:
            cmd = f"cat {input_file} | {gf_path} {pattern}"
            proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
            out = proc.stdout.strip()
            if not out:
                print(Fore.YELLOW + f"[!] GF pattern {pattern} returned no output.")
            for line in out.splitlines():
                if line:
                    filtered_urls.add(line.strip())
        except subprocess.CalledProcessError as e:
            print(Fore.RED + f"[-] Error running gf with pattern {pattern}: {e}")
    print(Fore.GREEN + f"[+] GF filtering returned {len(filtered_urls)} URLs.")
    return filtered_urls

def run_arjun(target):
    """
    Run Arjun (installed as a Python module) to scan for hidden parameters on the target.
    """
    print(Fore.GREEN + "[+] Running Arjun for hidden parameter scanning...")
    try:
        cmd = f"python3 -m arjun -u {target}"
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        output = proc.stdout.strip()
        if not output:
            print(Fore.YELLOW + "[!] Arjun returned no output.")
        else:
            print(Fore.BLUE + f"[+] Arjun output:\n{output}")
    except subprocess.CalledProcessError as e:
        print(Fore.RED + f"[-] Error running Arjun: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)

def run_paramspider(paramspider_path, target):
    """
    Run ParamSpider on the target domain.
    Returns a set of URLs.
    ParamSpider expects only the domain name without the protocol.
    """
    parsed = urlparse(target)
    domain = parsed.netloc if parsed.netloc else target
    try:
        cmd = f"python3 {paramspider_path} --domain {domain}"
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        output = proc.stdout.strip()
        if not output:
            print(Fore.YELLOW + "[!] ParamSpider returned no output.")
        urls = set(output.splitlines())
        print(Fore.GREEN + f"[+] ParamSpider returned {len(urls)} URLs.")
        return urls
    except subprocess.CalledProcessError as e:
        print(Fore.RED + f"[-] Error running ParamSpider: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return set()

###############################
#           Main Flow         #
###############################

def main():
    printBanner()

    parser = argparse.ArgumentParser(
        description="XSSdawn: Crawl target website, gather URLs, filter using GF patterns, and discover hidden parameters with Arjun."
    )
    parser.add_argument("--target", required=True, help="Target website URL (e.g., https://example.com)")
    parser.add_argument("-s", "--subdomains", action="store_true", help="Allow scanning subdomains")
    parser.add_argument("--max-pages", type=int, default=100, help="Maximum number of pages to crawl (default: 100)")
    parser.add_argument("--output", default="merged_urls.txt", help="Output file to save merged URLs (default: merged_urls.txt)")
    parser.add_argument("--gf", action="store_true", help="Run GF filtering on the URLs")
    parser.add_argument("--arjun", action="store_true", help="Run Arjun for hidden parameter scanning on target")
    args = parser.parse_args()

    target = args.target

    # Define tools directory.
    script_dir = os.path.dirname(os.path.realpath(__file__))
    tools_dir = os.path.join(script_dir, "tools")
    ensure_dir(tools_dir)

    ###############################
    #   Ensure External Tools     #
    ###############################

    # Waybackurls (by TomNomNom)
    waybackurls_path = ensure_tool(
        tool_name="waybackurls",
        repo_url="https://github.com/tomnomnom/waybackurls.git",
        build_commands=["go build ."],
        binary_relative_path="waybackurls"
    )

    # gf (by TomNomNom)
    gf_path = ensure_tool(
        tool_name="gf",
        repo_url="https://github.com/tomnomnom/gf.git",
        build_commands=["go build ."],
        binary_relative_path="gf"
    )

    # GF Patterns (by 1ndianl33t)
    gf_patterns_dir = ensure_repo(
        repo_name="Gf-Patterns",
        repo_url="https://github.com/1ndianl33t/Gf-Patterns.git"
    )

    # For Arjun, we install it as a Python package.
    ensure_tool(
        tool_name="arjun",
        repo_url="https://github.com/s0md3v/Arjun.git",
        build_commands=["pip install ."],
        binary_relative_path=""  # No binary file is produced.
    )

    # ParamSpider (by devanshbatham)
    paramspider_requirements = os.path.join(tools_dir, "ParamSpider", "requirements.txt")
    paramspider_build_commands = ["pip3 install -r requirements.txt"] if os.path.isfile(paramspider_requirements) else ["echo 'No requirements.txt found, skipping installation.'"]
    paramspider_path = ensure_tool(
        tool_name="ParamSpider",
        repo_url="https://github.com/devanshbatham/ParamSpider.git",
        build_commands=paramspider_build_commands,
        binary_relative_path="paramspider/main.py"
    )

    ###############################
    #       Crawl & Merge         #
    ###############################

    print(Fore.BLUE + f"[+] Crawling website (built-in) on: {target}")
    crawler_urls = crawl_website(target, allow_subdomains=args.subdomains, max_pages=args.max_pages)
    print(Fore.GREEN + f"[+] Built-in crawler found {len(crawler_urls)} URLs with parameters.")

    print(Fore.BLUE + f"[+] Running Waybackurls on: {target}")
    wayback_urls = run_waybackurls(waybackurls_path, target)

    print(Fore.BLUE + f"[+] Running ParamSpider on: {target}")
    paramspider_urls = run_paramspider(paramspider_path, target)

    merged_urls = crawler_urls.union(wayback_urls).union(paramspider_urls)
    print(Fore.GREEN + f"[+] Total merged URLs: {len(merged_urls)}")

    try:
        with open(args.output, "w") as f:
            for url in merged_urls:
                f.write(url + "\n")
        print(Fore.GREEN + f"[+] Merged URLs saved to {args.output}")
    except Exception as e:
        print(Fore.RED + f"[-] Error saving merged URLs: {e}")
        sys.exit(1)

    ###############################
    #      GF Filtering (optional)#
    ###############################
    if args.gf:
        print(Fore.BLUE + "[+] Running GF filtering on merged URLs...")
        filtered_urls = run_gf_filter(gf_path, gf_patterns_dir, args.output)
        if filtered_urls:
            try:
                with open(args.output, "w") as f:
                    for url in filtered_urls:
                        f.write(url + "\n")
                print(Fore.GREEN + f"[+] Filtered URLs saved to {args.output}")
            except Exception as e:
                print(Fore.RED + f"[-] Error saving filtered URLs: {e}")
        else:
            print(Fore.YELLOW + "[!] GF filtering did not return any URLs.")

    ###############################
    #         Arjun Scan          #
    ###############################
    if args.arjun:
        run_arjun(target)

if __name__ == "__main__":
    main()
