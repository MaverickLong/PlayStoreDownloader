from gpapi.googleplay import GooglePlayAPI

import os
import json

# Load templates, configs and emulators
api26Server = GooglePlayAPI("ja_JP", "Asia/Tokyo", "crackling")
api31Server = GooglePlayAPI("ja_JP", "Asia/Tokyo")

with open("./config.json", "r", encoding="UTF-8") as text:
    config = json.load(text)
    text.close()

updated = False

readme = ""

with open("./README.md.template", "r", encoding="UTF-8") as template:
    readme = template.read()
    template.close()


def removeAllFiles(delPath):
    delList = os.listdir(delPath)
    for file in delList:
        filePath = os.path.join(delPath, file)
        if os.path.isfile(filePath):
            os.remove(filePath)


def tryFunc(func, default=0):
    try:
        return func()
    except:
        return default


def updateConfig(suffix, packageName, newVersion, versionString, obbList, allocatedServer, gameName, locale):
    with open("./config.json", "r", encoding="UTF-8") as text:
        currentConfig = json.load(text)
        text.close()
    currentConfig["packages"][gameName][locale] = \
        {"suffix": suffix, "packageName": packageName, "version": newVersion,
            "versionString": versionString, "obb": obbList, "allocatedServer": allocatedServer}
    dumpedConfig = json.dumps(currentConfig, indent=4, separators=(',', ': '))

    with open("./config.json", "w", encoding="UTF-8") as text:
        text.write(dumpedConfig)
        text.close()


def doUpgrade(gameName, locale, packageName, versionString, allocatedServer, server, newVersion):
    print("Update found for " + gameName + " " +
          locale + ", triggering APK download...")

    # Create Folder
    tryFunc(lambda: os.mkdir("./temp/" + packageName))

    # Download game files
    download = server.download(packageName, expansion_files=True)

    # Write base APK file
    apkPath = packageName + "/" + packageName + "_" + versionString + ".apk"
    with open("./temp/" + apkPath, "wb") as first:
        for chunk in download.get('file').get('data'):
            first.write(chunk)

    print("Extracting Split APK...")

    hasSplitAPK = False

    for splits in download["splits"]:
        hasSplitAPK = True
        splitPath = packageName + "/" + splits["name"] + '.apk'
        with open("./temp/" + splitPath, "wb") as third:
            for chunk in splits.get('file').get('data'):
                third.write(chunk)

    if hasSplitAPK:
        print("Generating APKS File")
        os.system("mv ./temp/" + apkPath + " ./temp/" +
                  packageName + "/base.apk")
        apkPath = apkPath + "s"
        os.system("zip -r ./temp/" + apkPath +
                  " ./temp/" + packageName + "/*.apk")
        os.system("rm ./temp/" + packageName + "/*.apk")
        suffix = "apks"
    else:
        suffix = "apk"

    print("Extracting datapacks...")

    obbList = {}

    # Write OBB file
    for obb in download["additionalData"]:
        obbPath = packageName + "/" + \
            obb['type'] + '.' + str(obb['versionCode']) + \
            '.' + download['docId'] + '.obb'
        obbList[obb["type"]] = obbPath

        with open("./temp/" + obbPath, 'wb') as second:
            for chunk in obb.get('file').get('data'):
                second.write(chunk)

    print("Pushing game files to download servers")
    for serverInfo in config["servers"].items():
        if serverInfo[0] in allocatedServer:
            os.system("scp -r -P " + serverInfo[1]["sshPort"] + " ./temp/" + packageName +
                      "/ root@" + serverInfo[1]["domain"] +
                      ":" + serverInfo[1]["webRoot"])

    print("Download / upload completed, delete used files and update config")
    removeAllFiles("./temp/" + packageName + "/")

    updateConfig(suffix, packageName, newVersion,
                 versionString, obbList, allocatedServer, gameName, locale)
    appendReadme(suffix, versionString, packageName, locale, allocatedServer, obbList)


def appendReadme(suffix, versionString, packageName, locale, allocatedServer, obbs):
    global readme
    # Append APK info
    supplementText = ""
    if not suffix == "apk":
        print("Found non-apk file type " + suffix)
        supplementText = " " + suffix.upper()
    suffix = "." + suffix

    readme = readme + "### " + versionString + \
        " " + locale + supplementText + "\n\n"
    for serverInfo in config["servers"].items():
        if serverInfo[0] in allocatedServer:
            readme = readme + "[" + serverInfo[0] + "](https://" + serverInfo[1]["domain"] + "/" + packageName + "/" + \
                packageName + "_" + versionString + suffix + ")\n\n"

    # Append OBB info
    for obbInfo in obbs:
        obbType, obbPath = obbInfo
        readme = readme + "### " + versionString + " " + \
            locale + " " + obbType + " OBB数据包文件\n\n"
        for serverInfo in config["servers"].items():
            if serverInfo[0] in allocatedServer:
                readme = readme + \
                    "[" + serverInfo[0] + \
                    "](https://" + \
                    serverInfo[1]["domain"] + "/" + obbPath + ")\n\n"


def fetchInfo(packageName, server):
    details = server.details(packageName)
    newVersion = details["details"]["appDetails"]["versionCode"]
    versionString = details["details"]["appDetails"]["versionString"]
    return (newVersion, versionString)


def checkUpdate(subversion):
    global readme
    global updated

    locale, subversionInfo = subversion

    packageName = subversionInfo["packageName"]
    allocatedServer = subversionInfo["allocatedServer"]

    manualMode = tryFunc(lambda: subversionInfo["manualMode"], False)

    server = api26Server

    versionString = subversionInfo["versionString"]
    suffix = tryFunc(lambda: subversionInfo["suffix"], "apk")

    if not manualMode:
        version = subversionInfo["version"]
        # Fetch game version
        try:
            newVersion, versionString = fetchInfo(packageName, server)
        except:
            server = api31Server
            newVersion, versionString = fetchInfo(packageName, server)

    if not manualMode and version < int(newVersion):
        doUpgrade(gameName, locale, packageName,
                  versionString, allocatedServer, server, newVersion)
        updated = True
    else:
        appendReadme(suffix, versionString, packageName,
                     locale, allocatedServer, subversionInfo["obb"].items())

# Login
print('Logging in with email and password')
api26Server.login(config["email"], config["password"], None, None)
api31Server.login(config["email"], config["password"], None, None)

for game in config["packages"].items():

    # Load game details from config
    gameName = game[0]
    gameSubversions = game[1]

    print(gameName)

    readme = readme + "## " + gameName + "\n\n"

    for subversion in gameSubversions.items():
        checkUpdate(subversion)

with open("./temp/README.md", "w", encoding="UTF-8") as readmeFile:
    readmeFile.write(readme)

if updated:
    print("Finally, pushing index markdown to frontend")
    os.system("scp ./temp/README.md root@" +
          config["frontend"]["domain"] + ":" + config["frontend"]["docRoot"])
    os.system("ssh root@" + config["frontend"]["domain"] + " \"konmai\"")
else:
    print("not updated, skip markdown push")
