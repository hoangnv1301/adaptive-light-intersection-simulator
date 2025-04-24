import subprocess
import sys
import os
import time
import random
import multiprocessing
import json

class VehicleGenerator:
    @staticmethod
    def generate_vehicle_data():
        """Tạo thông tin phương tiện ngẫu nhiên"""
        vehicle_types = {0:'car', 1:'bus', 2:'truck', 3:'rickshaw', 4:'bike'}
        direction_numbers = {0:'right', 1:'down', 2:'left', 3:'up'}
        
        # Tạo loại xe
        vehicle_type = random.randint(0,4)
        
        # Xác định làn đường
        if vehicle_type == 4:  # bike
            lane_number = 0
        else:
            lane_number = random.randint(0,1) + 1
        
        # Xác định có rẽ hay không
        will_turn = 0
        if lane_number == 2:
            temp = random.randint(0,4)
            if temp <= 2:
                will_turn = 1
        
        # Xác định hướng di chuyển
        temp = random.randint(0,999)
        a = [400,800,900,1000]
        if temp < a[0]:
            direction_number = 0
        elif temp < a[1]:
            direction_number = 1
        elif temp < a[2]:
            direction_number = 2
        elif temp < a[3]:
            direction_number = 3
        
        # Đóng gói dữ liệu
        return {
            'vehicle_type': vehicle_type,
            'vehicle_class': vehicle_types[vehicle_type],
            'lane_number': lane_number,
            'will_turn': will_turn,
            'direction_number': direction_number,
            'direction': direction_numbers[direction_number]
        }

def vehicle_generator(pipe_adaptive, pipe_fixed):
    """Process riêng để tạo phương tiện và gửi đến cả hai simulator"""
    try:
        while True:
            # Tạo dữ liệu phương tiện
            vehicle_data = VehicleGenerator.generate_vehicle_data()
            
            # Gửi cùng dữ liệu đến cả hai simulator
            pipe_adaptive.send(vehicle_data)
            pipe_fixed.send(vehicle_data)
            
            # Nghỉ giữa hai lần tạo
            time.sleep(0.75)
    except (BrokenPipeError, EOFError, KeyboardInterrupt):
        # Đóng pipes khi kết thúc
        pipe_adaptive.close()
        pipe_fixed.close()
        print("Vehicle generator stopped.")

def main():
    print("Starting dual mode traffic simulation...")
    print("1. Running adaptive timing simulation")
    print("2. Running fixed timing simulation (30s)")
    
    # Thiết lập pipes cho việc trao đổi dữ liệu phương tiện
    adaptive_parent_conn, adaptive_child_conn = multiprocessing.Pipe()
    fixed_parent_conn, fixed_child_conn = multiprocessing.Pipe()
    
    # Bắt đầu process tạo phương tiện
    vehicle_gen_process = multiprocessing.Process(
        target=vehicle_generator, 
        args=(adaptive_child_conn, fixed_child_conn)
    )
    vehicle_gen_process.daemon = True
    vehicle_gen_process.start()
    
    # Get the path to the python executable
    python_executable = sys.executable
    
    # Chuẩn bị biến môi trường để truyền file descriptors của pipes
    env = os.environ.copy()
    env['ADAPTIVE_PIPE_FD'] = str(adaptive_parent_conn.fileno())
    env['FIXED_PIPE_FD'] = str(fixed_parent_conn.fileno())
    env['SYNC_VEHICLES'] = '1'  # Cờ báo hiệu sử dụng chế độ đồng bộ
    
    # Start both simulations in separate processes
    adaptive_process = subprocess.Popen(
        [python_executable, "simulation_dual_mode_for_comparison.py"],
        env=env,
        pass_fds=[adaptive_parent_conn.fileno()]
    )
    
    time.sleep(1)  # Small delay to avoid resource conflicts
    
    fixed_process = subprocess.Popen(
        [python_executable, "fixed_timing_simulation.py"],
        env=env,
        pass_fds=[fixed_parent_conn.fileno()]
    )
    
    print("Both simulations are now running with synchronized vehicle traffic!")
    print("Close both windows to exit the simulation.")
    
    # Wait for both processes to complete
    adaptive_process.wait()
    fixed_process.wait()
    
    # Dừng process tạo phương tiện
    vehicle_gen_process.terminate()
    
    # Đóng pipes
    adaptive_parent_conn.close()
    fixed_parent_conn.close()
    
    print("Simulation ended.")

if __name__ == "__main__":
    multiprocessing.set_start_method('spawn', force=True)
    main() 