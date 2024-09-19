#coding=utf-8
import os
import shutil
import configparser
from waapi import WaapiClient, CannotConnectToWaapiException
import argparse

if __name__ =='__main__':
    config=configparser.ConfigParser()
    cfgpath='./FileReplace.ini'
    if os.path.exists(cfgpath):
        try:
            parser = argparse.ArgumentParser()
            parser.add_argument("--Channel", required=False)
            parser.add_argument("--SoundbankPath", required=True)
            args = parser.parse_args()
        except BaseException as e:
            print(f'unexpectation: {e}')
        logChannel = "general"
        if args.Channel != None and args.Channel != "":
            logChannel = args.Channel
        config.read(cfgpath)
        copysrc = args.SoundbankPath
        copydst=config.get('path','dst')
        if os.path.exists(copydst):
            shutil.rmtree(copydst)
        shutil.copytree(copysrc, copydst)
        try:
            # Connecting to Waapi using default URL
            with WaapiClient() as client:
                # NOTE: client will automatically disconnect at the end of the scope
                client.call("ak.wwise.core.log.addItem", {"channel": logChannel, "severity": "Warning", "message": "soundbank copied from " + copysrc + "to " + copydst})
        except CannotConnectToWaapiException:
            print("Could not connect to Waapi: Is Wwise running and Wwise Authoring API enabled?")
