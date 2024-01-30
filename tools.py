import json
import csv
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
             

print("Load csv finished!")
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


intersected_ranges = []
non_intersected_ranges = []
time2throughput = {}


# 假设 sorted_CudaEvents 是已经包含所有CUDA事件并排好序的列表
total_events = len(sorted_CudaEvents)

# 计算我们需要的事件数量：总数的1/10
required_event_count = total_events // 100  # 使用整除以得到整数

# 从列表中获取1/10的事件
required_events = sorted_CudaEvents[:required_event_count]

# 现在你可以使用 required_events 来进行你的分析


for event in tqdm(required_events,total=len(required_events),desc="Processing CUDA Events"):
    start = int(event['startNs'])
    end = int(event['endNs'])
    id = int(event["kernel"]["demangledName"])
    name = id2name[id]
    
    if name in name2throughput:
           
        # 判断一下有没有，如果没有直接跳过
        throughput = name2throughput[name]

    mostrecent = start
    
    processed = False
    for time_range in time2throughput:
        range_start, range_end = time_range
        
        if start < range_end and end > range_start: 
            #
            processed = True
            # 有交集
            intersect_start = max(start, range_start)
            intersect_end = min(end, range_end)
            
            if intersect_start > range_start:
                #Is there a need to set the range end to intersect_start - 1?
                non_intersected_ranges.append((range_start, intersect_start, time2throughput[time_range]))
            
            if(time2thorughput[time_range]) > 100:
                print(f"{name} {throughput} + {time2thorughput[time_range]}")
                assert False
            intersected_ranges.append((intersect_start,intersect_end,throughput + time2throughput[time_range]))
            
            if intersect_end < range_end:
                non_intersected_ranges.append((intersect_end,range_end,time2throughput[time_range]))
                
            #update current
            mostrecent = range_end;
        else:
            non_intersected_ranges.append((range_start,range_end,time2throughput[time_range]))
    
    time2thorughput = {}
    
    # if left
    if mostrecent < end:
        non_intersected_ranges.append((mostrecent,end,throughput))
        
    if not processed:
        time2throughput[(start,end)] = throughput
    else:
        for time_range in non_intersected_ranges + intersected_ranges:
            range_start, range_end, range_throughput = time_range
            time2throughput[(range_start,range_end)] = range_throughput
        
print("result")
# 打印时间段对应的 throughput
for time_range, throughput in time2throughput.items():
    print(time_range, throughput)

    
time_ranges = list(time2throughput.keys())
throughputs = list(time2throughput.values())

# 转换时间范围为相对时间（相对于第一个时间戳的时间差）
start_time = time_ranges[0][0]
relative_time_ranges = [(start - start_time, end - start_time) for start, end in time_ranges]

# 准备绘图数据
x_values = [start for start, _ in relative_time_ranges]
widths = [end - start for start, end in relative_time_ranges]
y_values = throughputs

# 绘图
fig, ax = plt.subplots()
ax.bar(x_values, y_values, width=widths, align='edge', edgecolor='black')

# 设置x轴和y轴标签
ax.set_xlabel('Time (absolute)')
ax.set_ylabel('Throughput')

# 设置x轴的刻度标签
ax.set_xticks(x_values)
ax.set_xticklabels([f'{(start + start_time) / 1e9:.2f}s\n{(end + start_time) / 1e9:.2f}s' for start, end in relative_time_ranges])

# 显示图表
plt.show()
