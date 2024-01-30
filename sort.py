import json
import sys
import argparse
import time
parser = argparse.ArgumentParser(description="json parser")

parser.add_argument("path2json",type=argparse.FileType('r'),help="json file to be parsed",default="/Users/valerian/Desktop/uniad.json")

args = parser.parse_args()

jsonfile = args.path2json

class CudaEvent:
    def __init__(self, start, end, name) -> None:
        self.start = start
        self.end = end
        #ms
        self.duration = float((end - start) / 1000000)
        self.name = name
        
    def __str__(self) -> str:
        return f"name:{self.name} -> {self.start}, {self.end}, duration: {self.duration}ms"

name = []
CudaEvents = []

index = 0
for line in jsonfile:
    singleJson = json.loads(line)
    if index == 0:
        name = singleJson['data']
    index += 1
    
    if singleJson.get("Type") == 79:
        cuda_event = singleJson['CudaEvent']
        demangled_id = int(cuda_event['kernel']['demangledName'])
        startNs = float(cuda_event['startNs'])
        endNs = float(cuda_event['endNs'])
        demangled_name = name[demangled_id]
        event = CudaEvent(startNs,endNs,demangled_name)
        CudaEvents.append(event)

CudaEvents_sorted = sorted(CudaEvents, key=lambda event: event.duration, reverse=True)
    
# 打印排序后的列表
for event in CudaEvents_sorted:
    print(event)
