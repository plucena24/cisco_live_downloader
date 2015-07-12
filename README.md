# Cisco Live Downloader

## About

'cisco_live_downloader' is a script that logs into your Cisco Live 365 account
and downloads all of the mp4/pdfs from any sessions you have marked under
your 'interests'. By default, only the latest Cisco Live event -
Cisco Live 2015 San Diego - will be downloaded. This is configurable through
the command line.

Uses multiple threads to download mp4/pdfs concurrently. By default 20 threads
will be spawned, meaning 20 downloads will be kicked off at the time time. The
number of threads is also configurable.

The downloads are efficient, by chunking the downloaded files every 1024MB and
writing to disk. None of previous downloaded chunks are kept in memory -
similar to a web browser download.

Requires two third party libraries - BeautifulSoup and requests.

pip install BeautifulSoup
pip install requests

For efficiency, the script checks the configured directorty (current
directorty by default) for any existing .mp4s that have already been
downloaded. This is to prevent having to re-download a file that has been
previously downloaded during a previous execution of the script. If for
example you ran the script, but added more sessions under your 'interests'.


## Installation

### Prerequisites

You need:

* [BeautifulSoup][1]
* [requests][2]


## Usage

Note: For Windows users - please use doble "\\" as path separators:

python cisco_live_downloader.py -u username -p password -e "2015 San Diego" -d C:\\users\\admin\\cisco_live\\

Or just use "/"

python cisco_live_downloader.py -u username -p password -e "2015 San Diego" -d C:/users/admin/cisco_live/

python cisco_live_downloader.py --username admin -password pass


[1]: https://pypi.python.org/pypi/requests "requests"
[2]: https://pypi.python.org/pypi/BeautifulSoup "BeautifulSoup"
