#!/bin/python
import requests
import tarfile

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
            for data in response.iter_content(chunk_size=4096):
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
    checksum_arr = []
    with open(checksumfile, "r") as f:
        if checksumfile == "sha256.txt":
            for line in f.readlines():
                info = line.split(" ")
                if info[0] != "SHA256":
                    raise Exception(info[0] + " is not supported")
                else:
                    checksum_arr.append({
                        'filename': info[1].strip('()'),
                        'checksum': info[3].rstrip()
                    })
        elif checksumfile == "sha256sums.txt":
           for line in f.readlines():
                info = line.split(" ")
                checksum_arr.append({
                    'filename': info[2].rstrip(),
                    'checksum': info[0]
                })
        else:
            raise Exception("Checksum filetype not supported")
    return checksum_arr
def checksum(inputfilename, checksumfile):
    raise Exception("Not implemented")
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
def main:
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
    if ask("Do you want to continue?", {1: ("Yes!", "yes"), 2: ("No!", "no")}) == "no":
        print("Ok. Quitting.")
        return 0
    download(checksum_url, checksum_filename)
    download(iso_url, iso_filename)
    os.mkdir("voidLinuxROOTFS")
    extract("void.tar.gz", "voidLinuxROOTFS")
    checksum()

sys.exit(main())
