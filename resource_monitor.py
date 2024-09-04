#!/usr/bin/env python3

import os
import psutil
import time
import logging
import subprocess

log_file = "/var/log/resource_monitor.log"
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(message)s')

cpu_threshold = 201.0  
overall_cpu_threshold = 60.0  
memory_threshold = 0.2  
load_threshold = 20.0  
ping_host = "qq.com"  

def log_top_processes():
    current_pid = os.getpid()  # 获取当前脚本的PID
    top_procs = sorted(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']), 
                       key=lambda p: p.info['cpu_percent'], 
                       reverse=True)[:3]
    
    for proc in top_procs:
        if proc.info['pid'] == current_pid:
            continue  # 跳过记录当前脚本进程

        proc_info = proc.info
        memory_usage = proc_info['memory_info'].rss / (1024 * 1024 * 1024) 
        logging.info(f"进程 {proc_info['name']} (PID: {proc_info['pid']}) 使用的CPU: {proc_info['cpu_percent']}%，内存使用: {memory_usage:.2f}GB")

def log_system_status():
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_available = psutil.virtual_memory().available / (1024 * 1024 * 1024)  
    load_avg = os.getloadavg()[0]  
    logging.info(f"当前 CPU 使用率: {cpu_usage}%, 可用内存: {memory_available:.2f}GB, 负载平均: {load_avg}")
    
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
        if proc.info['cpu_percent'] > cpu_threshold:
            logging.warning(f"进程 {proc.info['name']} (PID: {proc.info['pid']}) 使用的CPU达到了 {proc.info['cpu_percent']}%，超过了阈值 {cpu_threshold}%")
            log_top_processes()
            break

    if cpu_usage > overall_cpu_threshold or memory_available < memory_threshold or load_avg > load_threshold:
        logging.warning(f"系统资源使用率超出阈值！记录前3个占用资源最高的进程：")
        log_top_processes()
        sys_log = os.popen('tail -n 5 /var/log/messages').read()
        logging.info(f"最近的系统日志:\n{sys_log}")

def check_system_unresponsive():
    try:
        result = subprocess.run(['ping', '-c', '1', ping_host], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            logging.error(f"无法 ping {ping_host}，可能系统卡死！")
            log_top_processes()
            sys_log = os.popen('tail -n 10 /var/log/messages').read()
            logging.info(f"最近的系统日志:\n{sys_log}")
    except Exception as e:
        logging.error(f"检查系统是否卡死时出错: {e}")

def monitor_resources():
    while True:
        log_system_status()
        check_system_unresponsive()
        time.sleep(120)  # 调整监控频率

if __name__ == "__main__":
    monitor_resources()

