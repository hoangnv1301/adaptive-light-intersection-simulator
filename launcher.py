import subprocess
import sys
import os
import time
import random
import multiprocessing
import json
import cv2
import streamlink
from streamlink.exceptions import PluginError, NoPluginError
from ultralytics import YOLO
import numpy as np
import subprocess # Add subprocess for ffmpeg
import shlex # For safely splitting command strings

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
    """Process đọc stream YouTube (qua ffmpeg), chạy YOLO, và gửi dữ liệu xe đến simulators."""

    YOUTUBE_URL = "https://www.youtube.com/watch?v=ByED80IKdIU"
    MODEL_PATH = "best.pt" # Đường dẫn tới model của bạn
    CONFIDENCE_THRESHOLD = 0.4
    STREAM_QUALITY = '720p'
    FFMPEG_PATH = 'ffmpeg' # Assume ffmpeg is in PATH, change if needed

    # --- !!! QUAN TRỌNG: ĐỊNH NGHĨA ROI VÀ CLASS MAP !!! ---
    ROIS = {
        'right': np.array([[100, 100], [300, 100], [300, 200], [100, 200]], dtype=np.int32),
        'down':  np.array([[400, 50],  [500, 50],  [500, 150], [400, 150]], dtype=np.int32),
        'left':  np.array([[600, 300], [800, 300], [800, 400], [600, 400]], dtype=np.int32),
        'up':    np.array([[400, 500], [500, 500], [500, 600], [400, 600]], dtype=np.int32),
    }
    DIRECTION_MAP = {'right': 0, 'down': 1, 'left': 2, 'up': 3}
    CLASS_MAP = {
        'car': 'car',
        'truck': 'truck',
        'bus': 'bus',
        'motorcycle': 'bike',
    }
    KNOWN_CLASS_NAMES = list(CLASS_MAP.keys())
    tracked_ids = set()

    # --- Kích thước frame dự kiến cho chất lượng stream ---
    # (Cần điều chỉnh nếu bạn chọn chất lượng khác 720p)
    WIDTH, HEIGHT = 1280, 720
    frame_size_bytes = WIDTH * HEIGHT * 3 # 3 bytes per pixel (BGR)

    # 1. Tải model YOLO (Giữ nguyên)
    try:
        model = YOLO(MODEL_PATH)
        print(f"Đã tải model YOLO từ: {MODEL_PATH}")
    except Exception as e:
        print(f"LỖI NGHIÊM TRỌNG khi tải model YOLO: {e}")
        pipe_adaptive.close()
        pipe_fixed.close()
        return

    # 2. Lấy URL stream trực tiếp bằng Streamlink (Giữ nguyên logic lấy URL)
    stream_url = None
    try:
        print(f"Đang thử lấy stream từ {YOUTUBE_URL} với chất lượng {STREAM_QUALITY}...")
        streams = streamlink.streams(YOUTUBE_URL)
        if not streams:
            print(f"Lỗi: Không tìm thấy stream nào cho URL: {YOUTUBE_URL}")
        elif STREAM_QUALITY not in streams:
            print(f"Lỗi: Không tìm thấy chất lượng stream '{STREAM_QUALITY}'. ... trying 'best' ...")
            STREAM_QUALITY = 'best'
            if STREAM_QUALITY not in streams:
                 print(f"Lỗi: Không tìm thấy chất lượng stream 'best'.")
                 streams = None
        if streams:
            stream_url = streams[STREAM_QUALITY].url
            print(f"Đã lấy được stream URL: {stream_url}")
        else:
             print("Không lấy được stream URL.")

    except (PluginError, NoPluginError) as e:
        print(f"Lỗi Streamlink: {e}")
    except Exception as e:
        print(f"Lỗi không xác định khi lấy stream URL: {e}")

    if not stream_url:
        print("Không thể lấy stream URL. Dừng generator.")
        pipe_adaptive.close()
        pipe_fixed.close()
        return

    # 3. Khởi chạy ffmpeg để đọc stream và pipe raw frames
    ffmpeg_process = None
    try:
        print("Đang khởi chạy ffmpeg...")
        command = [
            FFMPEG_PATH,
            '-hide_banner', '-loglevel', 'info', # Thay error thành info để xem nhiều output hơn
            '-i', stream_url,
            '-vf', f'scale={WIDTH}:{HEIGHT}',
            '-pix_fmt', 'bgr24',
            '-f', 'rawvideo',
            '-preset', 'ultrafast',
            'pipe:1'
        ]
        print(f"Lệnh FFMPEG: {' '.join(shlex.quote(c) for c in command)}")
        # Bỏ stderr=subprocess.PIPE để lỗi ffmpeg in ra terminal trực tiếp
        ffmpeg_process = subprocess.Popen(command, stdout=subprocess.PIPE)
        print("FFmpeg đã khởi chạy, đang chờ dữ liệu...")

        # 4. Vòng lặp đọc frame từ pipe của ffmpeg và xử lý
        frame_count = 0 # Đếm số frame đọc được
        while True:
            # Đọc đủ byte cho một frame từ stdout của ffmpeg
            # print("[DEBUG] Waiting to read frame...") # Debug đọc
            in_bytes = ffmpeg_process.stdout.read(frame_size_bytes)
            # print(f"[DEBUG] Read {len(in_bytes)} bytes.") # Debug số byte đọc được

            if not in_bytes or len(in_bytes) != frame_size_bytes:
                print(f"Không đọc đủ byte từ ffmpeg (đọc được {len(in_bytes)}, cần {frame_size_bytes}) hoặc stream kết thúc.")
                # Không cần đọc stderr ở đây nữa vì nó sẽ tự in ra
                # stderr_output = ffmpeg_process.stderr.read()
                # if stderr_output:
                #       print(f"FFmpeg stderr: {stderr_output.decode(errors='ignore')}")
                break
            
            frame_count += 1
            # print(f"[DEBUG] Processing frame {frame_count}") # Debug xử lý frame

            # Chuyển đổi bytes thành NumPy array (OpenCV frame)
            try:
                frame = np.frombuffer(in_bytes, np.uint8).reshape([HEIGHT, WIDTH, 3])
            except ValueError as reshape_error:
                 print(f"[ERROR] Lỗi reshape frame {frame_count}: {reshape_error}. Số byte đọc được: {len(in_bytes)}")
                 continue # Bỏ qua frame lỗi

            if frame is None:
                 # print("[DEBUG] Frame is None after reshape.")
                 time.sleep(0.01)
                 continue

            # 5. Chạy YOLO (Giữ nguyên logic)
            try:
                results = model.track(frame, persist=True, conf=CONFIDENCE_THRESHOLD, verbose=False)
            except Exception as e:
                 print(f"Lỗi trong quá trình model.track: {e}")
                 continue

            # 6. Xử lý kết quả và gửi pipe (Giữ nguyên logic)
            if results and results[0].boxes is not None and results[0].boxes.id is not None:
                boxes = results[0].boxes.xyxy.cpu().numpy()
                confs = results[0].boxes.conf.cpu().numpy()
                class_ids = results[0].boxes.cls.cpu().numpy().astype(int)
                track_ids = results[0].boxes.id.cpu().numpy().astype(int)

                for box, conf, cls_id, track_id in zip(boxes, confs, class_ids, track_ids):
                    # Print *every* detection for debugging
                    class_name = model.names[cls_id]
                    x1, y1, x2, y2 = map(int, box)
                    center_x = (x1 + x2) // 2
                    center_y = (y1 + y2) // 2
                    center_point = (center_x, center_y)
                    print(f"[DEBUG] Detected: ID={track_id}, Class='{class_name}', Conf={conf:.2f}, Center=({center_x}, {center_y})")

                    # --- Các kiểm tra logic như cũ ---
                    if track_id in tracked_ids:
                        # print(f"[DEBUG] ID {track_id} already processed. Skipping.")
                        continue

                    if class_name not in KNOWN_CLASS_NAMES:
                        # print(f"[DEBUG] Class '{class_name}' not in KNOWN_CLASS_NAMES. Skipping.")
                        continue

                    # Kiểm tra ROI
                    for direction_name, roi_poly in ROIS.items():
                        is_inside = cv2.pointPolygonTest(roi_poly, center_point, False) >= 0
                        if is_inside:
                            print(f"[DEBUG] ID {track_id} ({class_name}) ENTERED ROI: {direction_name}") # Print when entering ROI
                            # --- Logic tạo và gửi vehicle_data như cũ ---
                            sim_class = CLASS_MAP[class_name]
                            direction_number = DIRECTION_MAP[direction_name]
                            lane_number = 0 if sim_class == 'bike' else random.randint(1, 2)
                            will_turn = 1 if lane_number == 2 and random.random() < 0.3 else 0
                            vehicle_data = {
                                'vehicle_class': sim_class,
                                'lane_number': lane_number,
                                'will_turn': will_turn,
                                'direction_number': direction_number,
                                'direction': direction_name
                            }
                            try:
                                pipe_adaptive.send(vehicle_data)
                                pipe_fixed.send(vehicle_data)
                                tracked_ids.add(track_id)
                                print(f"---> Sent vehicle data for ID {track_id}") # Confirm sending
                            except (BrokenPipeError, EOFError):
                                print("Lỗi pipe khi gửi dữ liệu. Dừng generator.")
                                raise StopIteration
                            break # Thoát vòng lặp ROI

            # (Optional) Display frame for debugging
            try:
                frame_display = results[0].plot() # Vẽ bbox lên frame
                # Vẽ các ROI lên frame
                for dir_name, roi_pts in ROIS.items():
                    cv2.polylines(frame_display, [roi_pts], isClosed=True, color=(0, 255, 255), thickness=2) # Màu vàng
                    cv2.putText(frame_display, dir_name, (roi_pts[0][0], roi_pts[0][1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                cv2.imshow("YOLO Live Detection", frame_display)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("Người dùng yêu cầu thoát.")
                    break # Exit the main loop
            except Exception as display_error:
                 print(f"Lỗi khi hiển thị frame: {display_error}")

    except StopIteration:
        pass
    except KeyboardInterrupt:
        print("Đã nhận tín hiệu dừng (Ctrl+C).")
    except Exception as e:
        print(f"Lỗi không mong muốn trong vòng lặp xử lý: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Đang dừng vehicle generator...")
        # Dừng tiến trình ffmpeg nếu đang chạy
        if ffmpeg_process and ffmpeg_process.poll() is None:
            print("Đang dừng ffmpeg...")
            ffmpeg_process.terminate()
            try:
                ffmpeg_process.wait(timeout=5) # Chờ tối đa 5s
            except subprocess.TimeoutExpired:
                print("FFmpeg không dừng, đang kill...")
                ffmpeg_process.kill()
            print("FFmpeg đã dừng.")

        cv2.destroyAllWindows()
        # Đóng pipes (Giữ nguyên)
        try:
            pipe_adaptive.close()
        except Exception: pass
        try:
            pipe_fixed.close()
        except Exception: pass
        print("Vehicle generator đã dừng.")

# New function to generate vehicles randomly
def random_vehicle_generator_process(pipe_adaptive, pipe_fixed):
    """Generates random vehicle data and sends it to the simulation pipes."""
    print("Starting random vehicle generator process...")
    try:
        while True:
            vehicle_data = VehicleGenerator.generate_vehicle_data()
            # The original generateVehicles_fixed in dual_mode_simulation.py had a more complex structure
            # for vehicle_type, lane_number, will_turn, direction_number.
            # VehicleGenerator.generate_vehicle_data() encapsulates this.
            # We need to ensure the output format is compatible.
            # dual_mode_simulation.py's FixedVehicle and Vehicle constructors expect:
            # (lane, vehicleClass, direction_number, direction, will_turn)
            # The `vehicle_data` from `generate_vehicle_data` is a dict:
            # {
            #     'vehicle_type': vehicle_type_int, # Not directly used by sim's Vehicle, but determines vehicle_class
            #     'vehicle_class': vehicle_class_str,
            #     'lane_number': lane_number_int,
            #     'will_turn': will_turn_int,
            #     'direction_number': direction_number_int,
            #     'direction': direction_str
            # }
            # The simulation scripts (simulation_dual_mode_for_comparison.py and fixed_timing_simulation.py)
            # will need to be able to receive this dictionary and extract the necessary information.
            # Assuming the pipes send this dictionary as is, and the simulation scripts are adapted
            # or can already handle this dictionary structure.

            # For now, we send the dict. If issues arise, the simulation scripts' vehicle creation logic
            # might need adjustment to unpack this dict.
            
            print(f"[RandomGen] Generated: {vehicle_data}")
            pipe_adaptive.send(vehicle_data)
            pipe_fixed.send(vehicle_data)
            # Match the sleep time from other generator functions like generateVehicles_fixed
            time.sleep(0.75) 
    except (BrokenPipeError, EOFError):
        print("Simulation pipe closed. Stopping random vehicle generator.")
    except KeyboardInterrupt:
        print("Random vehicle generator process interrupted by user.")
    finally:
        print("Closing pipes for random vehicle generator.")
        if not pipe_adaptive.closed:
            pipe_adaptive.close()
        if not pipe_fixed.closed:
            pipe_fixed.close()

def main():
    print("Starting dual mode traffic simulation...")
    print("1. Running adaptive timing simulation")
    print("2. Running fixed timing simulation (30s)")
    print("--- Using RANDOM vehicle generation ---") # Indication of change

    # Thiết lập pipes cho việc trao đổi dữ liệu phương tiện
    adaptive_parent_conn, adaptive_child_conn = multiprocessing.Pipe()
    fixed_parent_conn, fixed_child_conn = multiprocessing.Pipe()

    # Bắt đầu process tạo phương tiện NGẪU NHIÊN
    vehicle_gen_process = multiprocessing.Process(
        target=random_vehicle_generator_process, # CHANGED from vehicle_generator
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
    # IMPORTANT on some systems (like macOS with 'spawn'):
    # Ensure model loading and heavy libraries happen *inside* the child process (vehicle_generator)
    # NOT at the global scope of the launcher script if using spawn start method.
    multiprocessing.set_start_method('spawn', force=True) # Giữ nguyên spawn
    main() 