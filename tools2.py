import json
import csv
import sys
import time
import matplotlib.pyplot as plt
from tqdm import tqdm

# map: name -> id
id2name = {}

# map: id -> CudaEventJson
CudaEvents = []
 
#dictionary
name2throughput = {}
with open("/Users/valerian/Desktop/uniad.csv","r") as file:
    reader = csv.reader(file)
    headers = next(reader)
    data = {}
    
    for row in reader:
        row_data = {}
        for header, value in zip(headers, row):
            row_data[header] = value
            
        name = row_data["Demangled Name"]
        throughput = float(row_data["Memory Throughput"])
        
        if name in name2throughput:
            name2throughput[name].append(throughput)
        else:
            name2throughput[name] = [throughput]
             

print("Load csv loaded")
#calculate the avg throughput of each kernel
for name, throughput_list in name2throughput.items():
    average_throughput = sum(throughput_list) / len(throughput_list)
    assert average_throughput < 100
    name2throughput[name] = average_throughput


# open json files
with open("/Users/valerian/Desktop/profile_output2.json") as file:
    for line in file:
        data = json.loads(line)
        if all(key in data for key in ['type','id', 'value']):
            id = int(data['id'])
            value = data['value']
            id2name[id] = value
                     
        if data.get("Type") == 79:
            cuda_event = data['CudaEvent']
            demangled_name = cuda_event['kernel']['demangledName']
            demangled_name_id = int(demangled_name)
            CudaEvents.append(cuda_event)

     
    
sorted_CudaEvents = sorted(CudaEvents,key=lambda x: x['startNs'])
print("json file loaded!")

intersected_ranges = []
non_intersected_ranges = []
time2throughput = {}


# 假设 sorted_CudaEvents 是已经包含所有CUDA事件并排好序的列表
total_events = len(sorted_CudaEvents)

# 计算我们需要的事件数量：总数的1/10
required_event_count = total_events  # 使用整除

# 从列表中获取1/10的事件
required_events = sorted_CudaEvents[:required_event_count]

# 现在你可以使用 required_events 来进行你的分析

counter = 0
for event in tqdm(required_events,total=len(required_events),desc="Processing CUDA Events"):
    counter = counter + 1
    if counter % 100 != 0:
        continue
    start = int(event['startNs']) / 1000000
    end = int(event['endNs']) / 1000000
    id = int(event["kernel"]["demangledName"])
    name = id2name[id]
    
    if name in name2throughput:  
        # 判断一下有没有，如果没有直接跳过
        throughput = name2throughput[name]
        
        if throughput > 60:
            print(f"High throughput {(start,end)}:{throughput}")
        time2throughput[(start,end)] = throughput
        
time.sleep(2)
print("result")
# # 打印时间段对应的 throughput
# for time_range, throughput in time2throughput.items():
#     print(time_range, throughput)

# 准备 x 轴（时间）和 y 轴（吞吐量）的数据
times = [start for (start, end) in time2throughput.keys()]
throughputs = list(time2throughput.values())

# 创建图形
plt.figure(figsize=(10, 5))  # 可以调整图形的大小
plt.scatter(times, throughputs, alpha=0.6)  # 创建散点图，alpha值是点的透明度

# 设置图形的标题和轴标签
plt.title('Event Throughput Over Time')
plt.xlabel('Time (ms)')
plt.ylabel('Throughput')

# 可选：设置 x 轴的范围，如果时间跨度很大的话
plt.xlim([min(times), max(times)])

# 可选：设置 y 轴的范围，如果吞吐量有明显的上下限的话
plt.ylim([min(throughputs), max(throughputs)])

# 显示网格
plt.grid(True)

# 显示图形
plt.show()
    
