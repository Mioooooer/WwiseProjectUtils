import os
from waapi import WaapiClient, CannotConnectToWaapiException
from pprint import pprint
import argparse
from xml.etree import ElementTree
from utils.audio_config_parse import *
from utils.ebur128 import *

def getSelectedInfo(waapiClient, infoTypeList):
    args = {
            "options": {
                "return": infoTypeList
            }
    }
    result = waapiClient.call("ak.wwise.ui.getSelectedObjects", args)
    if len(result["objects"]) == 0:
        return None
    return result["objects"][0]

def getInfobyID(waapiClient, ID, infoTypeList):
    args = {
        "from": {
            "id": [ID]
        },
        "options": {
            "return": infoTypeList
        }
    }
    result = waapiClient.call("ak.wwise.core.object.get", args)
    if result == None or len(result["return"]) == 0:
        return None
    return result["return"][0]

def getSingleSelectedInfo(waapiClient, infoType):
    result = getSelectedInfo(waapiClient, [infoType])
    if result == None or not (infoType in result):
        return None
    return result[infoType]

def getSelectedInfoList(waapiClient, infoTypeList):
    args = {
            "options": {
                "return": infoTypeList
            }
    }
    result = waapiClient.call("ak.wwise.ui.getSelectedObjects", args)
    if len(result["objects"]) == 0:
        return None
    return result["objects"]

def getSingleSelectedInfoList(waapiClient, infoType):
    result = getSelectedInfoList(waapiClient, [infoType])
    resultList = []
    for child in result:
        if child == None or not (infoType in child):
            resultList.append(None)
        else:
            resultList.append(child[infoType])
    return resultList

def getSingleInfoBy(waapiClient, ID, infoType):
    result = getInfobyID(waapiClient, ID, [infoType])
    if infoType in result:
        return result[infoType]
    else:
        return None

def getChildrenID(waapiClient, ID):
    childrenIDList = []
    args = {
        "from": {
            "id": [ID]
        },
        "transform": [{
            "select": ["children"]
        }],
        "options": {
            "return": ["id"]
        }
    }
    result = waapiClient.call("ak.wwise.core.object.get", args)
    if len(result["return"]) > 0:
        for item in result["return"]:
            childrenIDList.append(item["id"])
        return childrenIDList
    else:
        return None

    
def batchSetProperty(waapiClient, IDList, property, value):
        for child in IDList:
            args = {
                "object": child,
                "property": property,
                "value": value
            }
            waapiClient.call("ak.wwise.core.object.setProperty", args)
            waapiClient.call("ak.wwise.core.log.addItem", {"message": getSingleInfoBy(waapiClient, child, "Name") + " [" + property + "] " + value})

def getProjectPath(waapiClient):
    object_get_args = {
            "from": {
                "path": ["\\"]
            },
            "options": {
                "return": ["filePath"]
            }
        }
    projectPath = waapiClient.call("ak.wwise.core.object.get", object_get_args)["return"][0]["filePath"]
    return projectPath

def batchCheckLoudness(waapiClient, IDList, property, value):
        xlsxSheetNameDict = dict(Integrated = "LoudnessRule-I",
                            Momentary = "LoudnessRule-M",
                            ShortTerm = "LoudnessRule-S",
                            Lra = "LRA",
                            TruePeak = "TruePeak")
        checkFuncDict = dict(Integrated = get_single_loudness_integrated,
                            Momentary = get_max_loudness_momentary,
                            ShortTerm = get_max_loudness_shortterm,
                            Lra = get_single_loudness_range,
                            TruePeak = get_max_true_peak)
        projectPath = os.path.dirname(getProjectPath(waapiClient))
        xlsxPath = os.path.join(projectPath, "Add-ons\\CustomConfig\\AudioConfig.xlsx")
        LoudnessRuleDict = getRuleFromFile(xlsxPath, xlsxSheetNameDict[property])
        for child in IDList:
            originalFilePath = getSingleInfoBy(waapiClient, child, "originalFilePath")
            if originalFilePath == None:
                if getSingleInfoBy(waapiClient, child, "type") == "MusicTrack":
                    originalFilePath = GetMusicOriginalFilePath(waapiClient, child)
                else:
                    continue
            FinalLoudness = checkFuncDict[property](originalFilePath)
            #FinalRTPCRangeMin = 0
            #FinalRTPCRangeMax = 0
            target = child
            targetName = getSingleInfoBy(waapiClient, target, "name")
            while property != "Lra":
                if target == None:
                    break
                if getSingleInfoBy(waapiClient, target, "type") == "WorkUnit":
                    break
                if getSingleInfoBy(waapiClient, target, "name") == "Actor-Mixer Hierarchy":
                    break
                if getSingleInfoBy(waapiClient, target, "name") == "Interactive Music Hierarchy":
                    break
                if getSingleInfoBy(waapiClient, target, "type") == "Sound" or getSingleInfoBy(waapiClient, target, "type") == "MusicTrack":
                    targetName = getSingleInfoBy(waapiClient, target, "name")
                    OutputBusID = getSingleInfoBy(waapiClient, target, "OutputBus")["id"]
                    BusBusVolume = getSingleInfoBy(waapiClient, OutputBusID, "BusVolume")##
                    BusOutputBusVolume = getSingleInfoBy(waapiClient, OutputBusID, "OutputBusVolume")##
                    targetBusID = getSingleInfoBy(waapiClient, OutputBusID, "parent")["id"]
                    while True:
                        if targetBusID == None:
                            break
                        if getSingleInfoBy(waapiClient, targetBusID, "type") == "WorkUnit":
                            break
                        if getSingleInfoBy(waapiClient, targetBusID, "name") == "Master-Mixer Hierarchy":
                            break
                        if getSingleInfoBy(waapiClient, targetBusID, "BusVolume") != None:
                            BusBusVolume += getSingleInfoBy(waapiClient, targetBusID, "BusVolume")##
                        if getSingleInfoBy(waapiClient, targetBusID, "OutputBusVolume") != None:
                            BusOutputBusVolume += getSingleInfoBy(waapiClient, targetBusID, "OutputBusVolume")##
                        targetBusID = getSingleInfoBy(waapiClient, targetBusID, "parent")["id"]
                    BusVoiceVolume = getSingleInfoBy(waapiClient, OutputBusID, "Volume")#only first bus count into calculate
                    OutputBusVolume = getSingleInfoBy(waapiClient, target, "OutputBusVolume")
                    SoundVolume = getSingleInfoBy(waapiClient, target, "Volume")
                    FinalLoudness += OutputBusVolume + SoundVolume + BusBusVolume + BusVoiceVolume + BusOutputBusVolume
                    #if getSingleInfoBy(waapiClient, target, "RTPC") != None:
                    #    for rtpc in getSingleInfoBy(waapiClient, target, "RTPC"):
                    #        if getSingleInfoBy(waapiClient, rtpc["id"], "PropertyName") == "OutputBusVolume" or getSingleInfoBy(waapiClient, rtpc["id"], "PropertyName") == "Volume":
                    #            if getSingleInfoBy(waapiClient, rtpc["id"], "Curve")["id"] != "{00000000-0000-0000-0000-000000000000}":
                    #                pointSet = getSingleInfoBy(waapiClient, rtpc["id"], "Curve")["points"]
                    #                yValueList = []
                    #                for point in pointSet:
                    #                    yValueList += [point["y"]]
                    #                FinalRTPCRangeMin += min(yValueList)
                    #                FinalRTPCRangeMax += max(yValueList)
                else:
                    if(getSingleInfoBy(waapiClient, target, "Volume") != None):
                        FinalLoudness += getSingleInfoBy(waapiClient, target, "Volume")
                        #if getSingleInfoBy(waapiClient, target, "RTPC") != None:
                        #    for rtpc in getSingleInfoBy(waapiClient, target, "RTPC"):
                        #        if getSingleInfoBy(waapiClient, rtpc["id"], "PropertyName") == "Volume":
                        #            if getSingleInfoBy(waapiClient, rtpc["id"], "Curve") != "{00000000-0000-0000-0000-000000000000}":
                        #                pointSet = getSingleInfoBy(waapiClient, rtpc["id"], "Curve")["points"]
                        #                yValueList = []
                        #                for point in pointSet:
                        #                    yValueList += [point["y"]]
                        #                FinalRTPCRangeMin += min(yValueList)
                        #                FinalRTPCRangeMax += max(yValueList)
                target = getSingleInfoBy(waapiClient, target, "parent")["id"]
            
            targetLoudness = getValueFromDict(LoudnessRuleDict, targetName)
            if targetLoudness != None:
                logChannel = "general"
                if value != "":
                    logChannel = value
                if FinalLoudness > targetLoudness.get("valueMax"):
                    waapiClient.call("ak.wwise.core.log.addItem", {"channel": logChannel, "severity": "Warning", "message": getSingleInfoBy(waapiClient, child, "Name") + " [" + xlsxSheetNameDict[property] + "] " + "{:.2f}".format(FinalLoudness) + " out of range. Max value: " + str(targetLoudness.get("valueMax"))})
                elif targetLoudness.get("valueMin") != None:
                    if FinalLoudness < targetLoudness.get("valueMin"):
                        waapiClient.call("ak.wwise.core.log.addItem", {"channel": logChannel, "severity": "Warning", "message": getSingleInfoBy(waapiClient, child, "Name") + " [" + xlsxSheetNameDict[property] + "] " + "{:.2f}".format(FinalLoudness) + " out of range. Min value: " + str(targetLoudness.get("valueMin"))})
            #waapiClient.call("ak.wwise.core.log.addItem", {"message": getSingleInfoBy(waapiClient, child, "Name") + " [" + property + "] " + str(FinalLoudness) + " [Actor-MixerLoudnessRTPC range] " + str(FinalRTPCRangeMin) + "~" +str(FinalRTPCRangeMax)})

def recursionFindProperty(waapiClient, id, property, value, recursion = True):
    result = []
    if getSingleInfoBy(waapiClient, id, property) != None and len(getSingleInfoBy(waapiClient, id, property)) > 0:
        if getSingleInfoBy(waapiClient, id, property) == value:
            result.append(id)
            return result
    if recursion == False:
        return result
    childrenList = getChildrenID(waapiClient, id)
    if childrenList == None:
        return result
    for child in childrenList:
        if getSingleInfoBy(waapiClient, child, property) == None or len(getSingleInfoBy(waapiClient, child, property)) == 0:
            continue
        if getSingleInfoBy(waapiClient, child, property) == value:
            result.append(child)
        else:
            result += recursionFindProperty(waapiClient, child, property, value)
    return result

def xmlRecursionFindWithKeyValue(orcas, keyString, valueString):
    for orca in orcas:
        if orca.get(keyString) == valueString:
            return orca
        else:
            temp = xmlRecursionFindWithKeyValue(orca, keyString, valueString)
            if temp != False:
                return temp
    return False

def xmlRecursionFindTag(orcas, tagName):
    for orca in orcas:
        if orca.tag == tagName:
            return orca
        else:
            temp = xmlRecursionFindTag(orca, tagName)
            if temp != False:
                return temp
    return False

def GetMusicOriginalFilePath(waapiClient, targetID):
    object_get_args = {
            "from": {
                "path": ["\\Interactive Music Hierarchy"]
            },
            "options": {
                "return": ["id", "name"]
            }
        }
    HierarchyID = waapiClient.call("ak.wwise.core.object.get", object_get_args)["return"][0]["id"]
    HierarchyFilePath = getSingleInfoBy(waapiClient, HierarchyID, "filepath")
    wwuPath = getSingleInfoBy(waapiClient, getSingleInfoBy(waapiClient, targetID, "WorkUnit")["id"], "filePath")
    XMLTree = ElementTree.parse(wwuPath)
    XMLRoot = XMLTree.getroot()
    musicTrack = xmlRecursionFindWithKeyValue(XMLRoot, "ID", targetID)
    musicSourceFileName = xmlRecursionFindTag(musicTrack, "AudioFile").text
    musicSourceLanguageName = xmlRecursionFindTag(musicTrack, "Language").text
    audioFilePath = os.path.join(os.path.dirname(HierarchyFilePath), "Originals", musicSourceLanguageName, musicSourceFileName)
    return audioFilePath

def BatchSetting(waapiClient, targetTypeList, property, value, recursion = True):
    idList = []
    for targetType in targetTypeList:
        for id in getSingleSelectedInfoList(waapiClient, "id"):
            idList += recursionFindProperty(waapiClient, id, "type", targetType, recursion)
    batchSetProperty(waapiClient, idList, property, value)

def BatchProcess(waapiClient, targetTypeList, property, value, workerFunction, recursion = True):
    object_get_args = {
            "from": {
                "path": ["\\Actor-Mixer Hierarchy", "\\Interactive Music Hierarchy"]
            },
            "options": {
                "return": ["id", "name"]
            }
        }
    HierarchyIDList = waapiClient.call("ak.wwise.core.object.get", object_get_args)["return"]
    workunitList = []
    for Hierarchy in HierarchyIDList:
        workunitList += [Hierarchy["id"]]
    idList = []
    for targetType in targetTypeList:
        for id in workunitList:
            idList += recursionFindProperty(waapiClient, id, "type", targetType, recursion)
    for name, flag in property.items():
        if flag:
            workerFunction(waapiClient, idList, name, value)

try:
    # Connecting to Waapi using default URL
    with WaapiClient() as client:
        # NOTE: client will automatically disconnect at the end of the scope
        try:
            parser = argparse.ArgumentParser()
            parser.add_argument("--Channel", required=False)
            #parser.add_argument("--targetTypeList", nargs="+", required=True)
            parser.add_argument("--Integrated", action="store_true", default=False, required=False)
            parser.add_argument("--Momentary", action="store_true", default=False, required=False)
            parser.add_argument("--ShortTerm", action="store_true", default=False, required=False)
            parser.add_argument("--LRA", action="store_true", default=False, required=False)
            parser.add_argument("--TruePeak", action="store_true", default=False, required=False)
            args = parser.parse_args()
        except BaseException as e:
            print(f'unexpectation: {e}')

        property = dict(Integrated = args.Integrated,
                        Momentary = args.Momentary,
                        ShortTerm = args.ShortTerm,
                        Lra = args.LRA,
                        TruePeak = args.TruePeak)

        targetTypeList = ["Sound", "MusicTrack"]
        logChannel = ""
        if args.Channel == "soundbankGenerate":
            logChannel = "soundbankGenerate"
        recursion = True
        BatchProcess(client, targetTypeList, property, logChannel, batchCheckLoudness, recursion)
except CannotConnectToWaapiException:
    print("Could not connect to Waapi: Is Wwise running and Wwise Authoring API enabled?")
