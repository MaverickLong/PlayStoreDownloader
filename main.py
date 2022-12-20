from gpapi.googleplay import GooglePlayAPI

import os
import json

api26Server = GooglePlayAPI("ja_JP", "Asia/Tokyo", "crackling")
api31Server = GooglePlayAPI("ja_JP", "Asia/Tokyo")

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
api31Server.login(config["email"], config["password"], None, None)

for game in config["packages"].items():

    # Load game details from config
    gameName = game[0]
    gameSubversions = game[1]

    print(gameName)

    readme = readme + "## " + gameName + "\n\n"

    for subversion in gameSubversions.items():

        locale = subversion[0]
        subversionInfo = subversion[1]

        packageName = subversionInfo["packageName"]
        allocatedServer = subversionInfo["allocatedServer"]

        try:
            manualMode = subversionInfo["manualMode"]
        except Exception as e:
            manualMode = False

        server = api26Server

        versionString = subversionInfo["versionString"]

        if not manualMode:
            version = subversionInfo["version"]
            # Fetch game version
            try:
                details = server.details(packageName)
                newVersion = details["details"]["appDetails"]["versionCode"]
                versionString = details["details"]["appDetails"]["versionString"]
            except Exception as _:
                print("Compatability option not available, switching to API31...")
                server = api31Server
                details = server.details(packageName)
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
                os.system("mv ./temp/" + apkPath + " ./temp/" + packageName + "/base.apk")
                apkPath = apkPath + "s"
                os.system("zip -r ./temp/" + apkPath + " ./temp/" + packageName + "/*.apk")
                os.system("rm ./temp/" + packageName + "/*.apk")
                readme = readme + "### " + versionString + " " + locale + " APKS\n\n"      
            else:
                readme = readme + "### " + versionString + " " + locale + "\n\n"

            for serverInfo in config["servers"].items():
                if serverInfo[0] in allocatedServer:
                    readme = readme + "[" + serverInfo[0] + "](https://" + serverInfo[1]["domain"] + "/" + apkPath + ")\n\n"

            print("Extracting datapacks...")

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
