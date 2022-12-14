from gpapi.googleplay import GooglePlayAPI

import os
import json

api26Server = GooglePlayAPI("ja_JP", "Asia/Tokyo", "crackling")
api28Server = GooglePlayAPI("ja_JP", "Asia/Tokyo")

def removeAllFiles(delPath):
    delList = os.listdir(delPath)
    for file in delList:
        filePath = os.path.join(delPath, file)
        if os.path.isfile(filePath):
            os.remove(filePath)

with open("./config.json", "r", encoding = "UTF-8") as text:
    config = json.load(text)
    text.close()

readme = ""

with open("./README.md.template", "r", encoding = "UTF-8") as template:
    readme = template.read()
    template.close()

# Login
print('Logging in with email and password')
api26Server.login(config["email"], config["password"], None, None)
api28Server.login(config["email"], config["password"], None, None)

for game in config["packages"].items():

    gameName = game[0]
    print(gameName)

    gameSubversions = game[1]

    readme = readme + "## " + gameName + "\n\n"

    for subversion in gameSubversions.items():

        locale = subversion[0]

        # Just cleaning up the config file and eliminate the unnecessary Global setting...
        if locale == "Global":
            locale = ""

        subversionInfo = subversion[1]

        packageName = subversionInfo["packageName"]
        allocatedServer = subversionInfo["allocatedServer"]

        try:
            manualMode = subversionInfo["manualMode"]
        except Exception as e:
            manualMode = False

        try:
            compatibilityMode = subversionInfo["compatibilityMode"]
            if compatibilityMode:
                server = api26Server
        except Exception as e:
            server = api28Server

        if not manualMode:
            version = subversionInfo["version"]
            # Fetch game version
            details = server.details(packageName)
            #print(details["details"]["appDetails"])
            newVersion = details["details"]["appDetails"]["versionCode"]
            versionString = details["details"]["appDetails"]["versionString"]

        obbList = {}

        if not manualMode and version < int(newVersion):

            print("Update found for " + gameName + " " + locale + ", triggering APK download...")

            # Create Folder
            try:
                os.mkdir("./temp/" +  packageName)
            except Exception as e:
                pass

            # Download game files

            try:
                download = server.download(packageName, expansion_files=True)
            except Exception as e:
                download = server.download(packageName, expansion_files=True)

            # Write APK file
            apkPath = packageName + "/" + packageName + "_" + versionString + ".apk"
            with open("./temp/" + apkPath, "wb") as first:
                for chunk in download.get('file').get('data'):
                    first.write(chunk)

            readme = readme + "### " + versionString + " " + locale + "\n\n"

            for serverInfo in config["servers"].items():
                if serverInfo[0] in allocatedServer:
                    readme = readme + "[" + serverInfo[0] + "](https://" + serverInfo[1]["domain"] + "/" + apkPath + ")\n\n"

            print("Downloading datapacks...")

            # Write OBB file
            for obb in download["additionalData"]:
                obbPath = packageName + "/" + obb['type'] + '.' + str(obb['versionCode']) + '.' + download['docId'] + '.obb'
                obbList[obb["type"]] = obbPath

                with open("./temp/" + obbPath, 'wb') as second:
                    for chunk in obb.get('file').get('data'):
                        second.write(chunk)

                readme = readme + "### " + versionString + " " + locale + " Google Play " + obb["type"] + " OBB File\n\n"

                for serverInfo in config["servers"].items():
                    if serverInfo[0] in allocatedServer:
                        readme = readme + "[" + serverInfo[0] + "](https://" + serverInfo[1]["domain"] + "/" + obbPath + ")\n\n"

            print("Pushing game files to download servers")
            for serverInfo in config["servers"].items():
                if serverInfo[0] in allocatedServer:
                    try:
                        command = "ssh -p " + serverInfo[1]["sshPort"] + " root@" + serverInfo[1]["domain"] + " \"mkdir " + serverInfo[1]["webRoot"] + packageName + "/\""
                        print(command)
                        os.system(command)
                    except Exception as e:
                        pass

                    command = "scp -P " + serverInfo[1]["sshPort"] + " ./temp/" + packageName + "/* root@" + serverInfo[1]["domain"] + ":" + serverInfo[1]["webRoot"] + packageName + "/"
                    print(command)
                    os.system(command)

            print("Download / upload completed, delete used files and update config")
            removeAllFiles("./temp/" + packageName + "/")

            with open("./config.json", "r", encoding = "UTF-8") as text:
                currentConfig = json.load(text)
                text.close()
            currentConfig["packages"][gameName][locale] = \
                {"packageName" : packageName, "version" : newVersion, "versionString" : versionString, "obb": obbList, "allocatedServer": allocatedServer}
            dumpedConfig = json.dumps(currentConfig, indent=4, separators=(',', ': '))

            with open("./config.json", "w", encoding = "UTF-8") as text:
                text.write(dumpedConfig)
                text.close()

        else:
            # Append APK info
            readme = readme + "### " + versionString + " " + locale + "\n\n"
            for serverInfo in config["servers"].items():
                if serverInfo[0] in allocatedServer:
                    readme = readme + "[" + serverInfo[0] + "](https://" + serverInfo[1]["domain"] + "/" + packageName + "/" + \
                        packageName + "_" + versionString + ".apk)\n\n"

            # Append OBB info
            for obbInfo in subversionInfo["obb"].items():
                obbType = obbInfo[0]
                obbPath = obbInfo[1]
                readme = readme + "### " + versionString + " " + locale + " Google Play " + obbType + " OBB File\n\n"
                for serverInfo in config["servers"].items():
                     if serverInfo[0] in allocatedServer:
                        readme = readme + "[" + serverInfo[0] + "](https://" + serverInfo[1]["domain"] + "/" + obbPath + ")\n\n"

with open("./temp/README.md", "w", encoding = "UTF-8") as readmeFile:
    readmeFile.write(readme)

print("Finally, pushing index markdown to frontend")
os.system("scp ./temp/README.md root@" + config["frontend"]["domain"] + ":" + config["frontend"]["docRoot"])
os.system("ssh root@" + config["frontend"]["domain"] + " \"konmai\"")
