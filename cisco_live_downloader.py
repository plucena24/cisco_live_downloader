'''
Cisco Live 365 Session downloader command line utility.
Author: Pablo Lucena, @plucena24

Logs into your Cisco Live 365 account and parses any sessions marked under
your 'interests'. By default the tool will download all session materials
(pdfs, mp4s) from Cisco Live 2015 San Diego, but this is configurable by
passing a different event from the command line.

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

usage:

Note: For Windows users - please use doble "\\" as path separators:

python cisco_live_downloader.py -u username -p password -e "2015 San Diego" -d C:\\users\\admin\\cisco_live\\

Or just use "/"

python cisco_live_downloader.py -u username -p password -e "2015 San Diego" -d C:/users/admin/cisco_live/

python cisco_live_downloader.py --username admin -password pass

See README for more usage details, or look at the --help.

Since this is a multi-threaded program, you will not be able to kill it by
using cntrl-c. Kill the command prompt running the script instead by using
your OS's task manager.

`cisco_live_downloader` is able to detect if the script has been previously ran
by storing a text file on the current directorty with the `resource_id` of any
file that was fully downloaded successfully and saved to disk. A check is made
prior to beginning the download process, such that files that were already
downloaded are not over-written and re-downloaded.

'''

import re
import requests
import os
import argparse
import sys
import json
from multiprocessing.dummy import Pool as ThreadPool
from BeautifulSoup import BeautifulSoup
from itertools import chain

parser = argparse.ArgumentParser()
parser.add_argument('-u', '--username', help = 'Cisco Live 365 Username', type = str)
parser.add_argument('-p', '--password', help = 'Cisco Live 365 Password', type = str)
parser.add_argument('-e', '--event', help ='Cisco Live Event', type = str, default = '2015 San Diego')
parser.add_argument('-c', '--concurrent', help ='Concurrent Downloads', type =int, default = 20)
parser.add_argument('-d', '--dir', help ='Directory to store downloaded files', type = str)
args = parser.parse_args()

if not (args.username or args.password):
    sys.exit('Please enter username and password to log into Cisco Live!')

pool_workers = args.concurrent
username     = args.username
password     = args.password
event        = args.event

if args.dir:
    if not os.path.isdir(os.path.abspath(args.dir)):
        os.mkdir(os.path.abspath(args.dir))
    os.chdir(os.path.abspath(args.dir))

session = requests.Session()

data = {'username': username , 'password' : password}
headers = {'Content-Type' : 'application/x-www-form-urlencoded','User-Agent':'Mozilla/5.0'}
url = 'https://www.ciscolive.com/online/connect/processLogin.do'
html = session.post(url,headers=headers, data=data)

sessions_url = 'https://www.ciscolive.com/online/connect/interests.ww'
html_sess = session.get(sessions_url)
soup = BeautifulSoup(html_sess.content)

links = list()
for link in soup.findAll('a'):
    if event in link.parent.text:
        links.append(dict(name=link.text, resource_link='https://www.ciscolive.com/online/connect/' + link['href']))

def name_scrubber(name):
    '''remove illegal filename characters from names'''

    replace = {':' : '_', '/' : '_'}
    replace = dict((re.escape(k), v) for k,v in replace.items())
    re_sub  = re.compile('|'.join(replace.keys()))
    return re_sub.sub(lambda m : replace[re.escape(m.group(0))], name)

def get_links(resource):
    '''get session pdf and mp4 links'''

    html_resource  = session.get(resource['resource_link'])
    resource_soup  = BeautifulSoup(html_resource.content)
    video_field    = resource_soup.find('ul', {'id' : 'mediaList'})
    pdf_field      = resource_soup.find('ul', {'id' : 'fileDownloadList'})

    try:
        resource['video_link'] = dict(name = resource['name'],
                                      link = video_field.li.a['data-url'],
                                      )
    except AttributeError:
        resource['video_link'] = None

    try:
        resource['pdf_link'] = dict(name = resource['name'],
                                    link = pdf_field.li['data-url'])

    except AttributeError:
        resource['pdf_link'] = None

    for res in resource['pdf_link'], resource['video_link']:
        if res:
            extension   = res['link'].rsplit('.')[-1]
            resource_id = name_scrubber(res['name'] + '.' + extension)
            res.update(resource_id = resource_id)

    return resource

def download_resource((n_job, resource)):

    '''session pdf and mp4 downloader. uses little memory by chunking the
    output.

    if the session does not have a corresponding mp4, the pdf will still be
    downloaded.

    '''

    resource_id = resource['resource_id']

    print('Starting job_id {0}. Session {1}'.format(n_job, resource_id))

    try:
        download = requests.get(resource['link'], stream=True)
        with open(resource_id, 'wb') as fh:
            for chunk in download.iter_content(chunk_size=1024):
                if chunk:
                    fh.write(chunk)
                    fh.flush()

    except Exception:
        return None

    files_downloaded.append(resource_id)

    print('Finished job_id {0}. Session {1}'.format(n_job, resource_id))

def create_download_log():
    '''create download log'''

    with open(download_log, 'wb') as fh:
        fh.write("\n".join(files_downloaded))


download_log = 'downloaded_files_list.txt'
pool         = ThreadPool(pool_workers)
results      = pool.map(get_links, links)

results   = chain.from_iterable((res['video_link'], res['pdf_link']) for res in results)

# if file exists, script has ran before and downloads may exist.
skippable = []
if os.path.isfile(download_log):
    with open(download_log, 'r') as fh:
        skippable = fh.readlines()

# no need to start a thread for a non-existent resource
results   = [res for res in results if res is not None and res['resource_id'] not in skippable]

if not results:
    sys.exit("Either the credentials provided are wrong, or you currently don't have any saved interests under this account.")

print(json.dumps(results, indent=4))
print("\n"*3 + "#"*80 + "\n"*3)
print('''About to download {} resources. This may take a long time depending on your bandwidth...'''.format(len(results)))
print("\n"*3 + "#"*80 + "\n"*3)

files_downloaded = []

try:
    pool.map(download_resource, enumerate(results, 1))
except Exception as e:
    create_download_log()
    print("Encountered Error, {} - logged all files successfully downloaded.".format(e))
    raise

create_download_log()
print("\n"*3 + "#"*80 + "\n"*3)
print('Download job finished. Enjoy! =)')
