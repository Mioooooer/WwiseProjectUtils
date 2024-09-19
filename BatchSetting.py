from waapi import WaapiClient, CannotConnectToWaapiException
from pprint import pprint
import argparse

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
        #print(getSingleInfoBy(waapiClient, child, "Name"))
        if getSingleInfoBy(waapiClient, child, property) == None or len(getSingleInfoBy(waapiClient, child, property)) == 0:
            continue
        if getSingleInfoBy(waapiClient, child, property) == value:
            result.append(child)
        else:
            result += recursionFindProperty(waapiClient, child, property, value)
    return result

def BatchSetting(waapiClient, targetTypeList, property, value, recursion = True):
    idList = []
    for targetType in targetTypeList:
        for id in getSingleSelectedInfoList(waapiClient, "id"):
            idList += recursionFindProperty(waapiClient, id, "type", targetType, recursion)
    batchSetProperty(waapiClient, idList, property, value)

try:
    # Connecting to Waapi using default URL
    with WaapiClient() as client:
        # NOTE: client will automatically disconnect at the end of the scope
        try:
            parser = argparse.ArgumentParser()
            parser.add_argument("--property", required=True)
            parser.add_argument("--value", required=True)
            parser.add_argument("--targetTypeList", nargs="+", required=True)
            parser.add_argument("--recursionFalse", action="store_true", default=False, required=False)
            args = parser.parse_args()
        except BaseException as e:
            print(f'unexpectation: {e}')
        property = args.property
        value = args.value
        targetTypeList = args.targetTypeList
        recursion = True
        if args.recursionFalse:
            recursion = False
        BatchSetting(client, targetTypeList, property, value, recursion)

except CannotConnectToWaapiException:
    print("Could not connect to Waapi: Is Wwise running and Wwise Authoring API enabled?")
