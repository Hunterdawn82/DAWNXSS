## Dawnxss – XSS Automation Made Easy

Dawnxss is designed to streamline your XSS testing process by tying together several proven tools. By integrating Waybackurls, GF, GF Patterns, Dalfox, and Gau, this script helps automate vulnerability scans and enhances your security assessments.

Learn More:
For comprehensive guidance, visit our official documentation at: Dawnxss Documentation
Prerequisites

Before getting started with Dawnxss, make sure your system meets the following requirements:

1. Install Golang

First, install Go:

> `sudo apt-get update && sudo apt-get install -y golang`

Then configure your Go environment:

`export GOROOT=/usr/lib/go`<br>
`export GOPATH=$HOME/go`<br>
`export PATH=$PATH:$GOROOT/bin:$GOPATH/bin`<br>
`source ~/.bashrc`<br>

2. Essential Tools

Dawnxss depends on several external tools:

    GF – GitHub Repository
    GF Patterns – GitHub Repository
    Dalfox – GitHub Repository
    Waybackurls – GitHub Repository
    Gau – GitHub Repository

You can install them all at once using our helper script or one-by-one as detailed below.
Automated Setup

To install all required tools automatically, run:

`chmod +x install.sh`<br>
`./install.sh`

If you prefer a manual setup, use these commands:

    go get -u github.com/tomnomnom/gf
    go get github.com/tomnomnom/waybackurls
    GO111MODULE=on go get -v github.com/hahwul/dalfox/v2
    GO111MODULE=on go get -u -v github.com/lc/gau
    mkdir -p ~/.gf
    cp -r $GOPATH/src/github.com/tomnomnom/gf/examples ~/.gf
    git clone https://github.com/1ndianl33t/Gf-Patterns
    mv ~/Gf-Patterns/*.json ~/.gf

## Installing Dawnxss

 Clone the Dawnxss repository and prepare the script:

     git clone https://github.com/Hunterdawn82/Dawnxss.git
     cd Dawnxss
     chmod +x Dawnxss.sh

## How to Use

Dawnxss accepts a target domain along with optional parameters such as a blind XSS payload or an output file. Here’s how you can run it:

    Basic Scan:

    ./Dawnxss.sh -d target.com

Using a Blind XSS Payload:

    ./Dawnxss.sh -d target.com -b blindxss.yourpayload.ht

Saving Results to a File:


Combining Options:

    ./Dawnxss.sh -d target.com -b blindxss.yourpayload.ht -o results.txt

# Installation
## Prerequisites

    Go Installation: Install Go and configure your environment:
    sudo apt-get update && sudo apt-get install -y golang
    export GOROOT=/usr/lib/go
    export GOPATH=$HOME/go
    export PATH=$PATH:$GOROOT/bin:$GOPATH/bin
    source ~/.bashrc

# Support & Contributions

If Dawn has helped you improve your security testing workflow or contributed to your success, please consider supporting the project:

## Buy me a KO-fi 

Ko-fi.com/hunterdawn 




