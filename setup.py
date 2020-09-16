#!/bin/python
import platform
import requests
import sys
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
iso_url_template = Template("${mirror}${iso_version}/void-${arch}${libc}-ROOTFS-${iso_version}.tar.xz")
checksum_url_template = Template("${mirror}${iso_version}/${checksum_filename}")

# >> Helper functions
def ask(text, options):
    print(text)
    for key in options:
        print(str(key) + " : " + str(options[key][0]))
    return options[int(input("> "))][1]

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
# Download file from url, and save it with the filename, all with a progress bar
def download(url, filename):
    with open(filename, "wb") as f:
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
# >> Main code
arch = getArch()
libc = getLibc()
mirror = getMirror()
iso_version = getISOVersion()
checksum_filename = getChecksumFilename()

iso_url = iso_url_template.substitute(mirror=mirror, arch=arch, libc=libc, iso_version=iso_version)
checksum_url = checksum_url_template.substitute(mirror=mirror, iso_version=iso_version, checksum_filename=checksum_filename)

print("")
print("Arch is "+arch)
print("Libc is "+libc)
print("Mirror is "+mirror)
print("ISO version is "+iso_version)

download(checksum_url, checksum_filename)

