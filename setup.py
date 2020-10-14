#!/bin/python
import requests
import tarfile

import hashlib
import json
import sys
import platform
import os
from string import Template

# >> STATIC Global variables here
mirrors = {
    1: ("https://alpha.de.repo.voidlinux.org/live/", "https://alpha.de.repo.voidlinux.org/live/"),
    2: ("other", "other")
}
libcs = {
    1: ("musl", "-musl"),
    2: ("glibc", "")
}
iso_versions = {
    1: ("20191109", "20191109"),
    2: ("other", "other")
}
checksum_filenames = {
    1: ("sha256.txt", "sha256.txt"),
    2: ("sha256sums.txt", "sha256sums.txt"),
    3: ("other", "other")
}

login_file = Template("""#!/bin/bash -e
unset LD_PRELOAD
exec proot -r ./void-linux-ROOTFS -0 -w / -b /dev -b /proc -b /sys -b ${HOME} -w ${HOME} /usr/bin/env -i HOME=/root USER=root TERM="${TERM}" LANG=${LANG} PATH=/bin:/usr/bin:/sbin:/usr/sbin /bin/bash --login
""")

login_folderpath = os.environ["PREFIX"] if os.environ["PREFIX"] != None else "/bin"
login_filename = os.path.join(login_folderpath, "startvoid")
login_filedata = login_file.substitute(LANG=os.environ["LANG"], TERM=os.environ["TERM"], HOME=os.environ["HOME"], DESTINATION=login_filename)

iso_filename_template = Template("void-${arch}${libc}-ROOTFS-${iso_version}.tar.xz")
iso_url_template = Template("${mirror}${iso_version}/${iso_filename}")
checksum_url_template = Template("${mirror}${iso_version}/${checksum_filename}")

# >> Helper functions
def ask(text, options):
    print(text)
    for key in options:
        print(str(key) + " : " + str(options[key][0]))
    return options[int(input("> "))][1]
# Download file from url, and save it with the filename, all with a progress bar
def download(url, filename):
    with open(filename, "wb") as f:
        print("Starting to download " + filename)
        response = requests.get(url, stream=True)
        total_length = response.headers.get("content-length")
        if total_length is None:
            printf("No `content-lenght`")
            f.write(response.content)
        else:
            progress = 0
            total_length = int(total_length)
            for data in response.iter_content(chunk_size=8192):
                progress += len(data)
                f.write(data)
                percent_progress = (progress * 100) / total_length
                sys.stdout.write("\rCurrent progress {:.2f}%".format(percent_progress))                
                sys.stdout.flush()
            print("") # Add newline
        print("Done downloading " + filename)
# Extract inputfile
def extract(inputfile, outputfolder):
    tar = tarfile.open(inputfile, "r:xz")
    print("Starting to extract " + inputfile)
    tar.extractall(path=outputfolder)
    print("Done extractiong " + inputfile)
    tar.close()
# Parse the two different checksum files
def parse_checksum(checksumfile):
    checksum_arr = {}
    with open(checksumfile, "r") as f:
        if checksumfile == "sha256.txt":
            for line in f.readlines():
                info = line.split(" ")
                if info[0] != "SHA256":
                    raise Exception(info[0] + " is not supported")
                else:
                    checksum_arr[info[1].strip('()')] = info[3].rstrip()
        elif checksumfile == "sha256sums.txt":
           for line in f.readlines():
                info = line.split(" ")
                checksum_arr[info[2].rstrip()] = info[0]
        else:
            raise Exception("Checksum filetype not supported")
    return checksum_arr
# Calculate and check hash
def checksum(isofile, checksumfile):
    checksum_data_arr = parse_checksum(checksumfile)
    if isofile in checksum_data_arr:
        checksum_data = checksum_data_arr[isofile]
        filesize = os.path.getsize(isofile)
        progress = 0
        with open(isofile, "rb") as f:
            filehash = hashlib.sha256()
            print("Starting to calculate hash of " + isofile)
            while chunk := f.read(8192):
                progress += len(chunk)
                filehash.update(chunk)
                percent_progress = (progress * 100) / filesize
                sys.stdout.write("\rCurrent progress {:.2f}%".format(percent_progress))                
                sys.stdout.flush()
            print()
            print("Done calculating hash of " + isofile)
            if filehash.hexdigest().lower() == checksum_data.lower():
                return 1 # Valid
            else:
                return 0 # Invalid
    else:
        raise Exception("File not found in checksum data")
# >> Global variable getters
def getISOVersion():
    version = ask("Which version of void linux do you want?", iso_versions)
    if version == "other":
        return input("> ")
    else:
        return version
def getChecksumFilename():
    checksum_filename = ask("What filename does the checksum have?", checksum_filenames)
    if checksum_filename == "other":
        return input("> ")
    else:
        return checksum_filename
def getArch():
    return platform.machine()
def getLibc():
    return ask("Which libc do you want to use?", libcs)
def getMirror():
    mirror = ask("Which mirror do you want to use?", mirrors)
    if mirror == "other":
        return input("> ")
    else:
        return mirror
# >> Main code
def main():
    # Real input from user
    arch = getArch() 
    libc = getLibc()
    mirror = getMirror()
    iso_version = getISOVersion()
    checksum_filename = getChecksumFilename()
    # Substritude templates
    iso_filename = iso_filename_template.substitute(arch=arch, libc=libc, iso_version=iso_version)
    iso_url = iso_url_template.substitute(mirror=mirror, arch=arch, iso_version=iso_version, iso_filename=iso_filename)
    checksum_url = checksum_url_template.substitute(mirror=mirror, iso_version=iso_version, checksum_filename=checksum_filename)
    # Print selection & ask if user wants to continue
    print("")
    print("Arch is "+arch)
    print("Libc is "+libc)
    print("Mirror is "+mirror)
    print("ISO version is "+iso_version)
    print("")
    if ask("Do you want to continue?", {1: ("Yes!", "yes"), 2: ("No!", "no")}) == "no":
        print("Ok. Quitting.")
        return
    # Download, checksum and extract
    download(checksum_url, checksum_filename)
    download(iso_url, iso_filename)
    if checksum(iso_filename, checksum_filename) == 0: # Invalid
        raise Exception("Checksum does not match, your download might me corrupt")
    os.mkdir("void-linux-ROOTFS")
    extract(iso_filename, "void-linux-ROOTFS")
    # Setup login file
    os.makedirs(login_folderpath, exist_ok=True)
    with open(login_filename, "w") as f:
        f.write(login_filedata)
    os.system("chmod 700 " + login_filename)
try:
    status = main()
    sys.exit(0)
except Exception as err:
    sys.stderr.write("Cought exception: " + str(err) + "\n")
    raise err
    sys.exit(1)
