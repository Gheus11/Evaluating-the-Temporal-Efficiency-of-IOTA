import traci
import traci.constants as tc
from traci.exceptions import TraCIException
import os
import sys
import threading
import json
import socket
import time

lock = threading.Lock()

def track_vehicle_data(vehicle_id, data_dictionary):
    try:
        traci.vehicle.subscribe(vehicle_id, (tc.VAR_SPEED, tc.VAR_LANE_ID, tc.VAR_TIME, tc.VAR_ACCEL))
        data = traci.vehicle.getSubscriptionResults(vehicle_id)
        with lock:
            data_dictionary[vehicle_id] = data
    except TraCIException:
        pass


def track_throttle(prev_speed, curr_speed, passed_time=0.1, mass=1500, max_force=5000):
    step_accel = (curr_speed - prev_speed) / passed_time
    generated_force = mass * step_accel
    throttle = (generated_force / max_force) * 100
    return f"{throttle:.0f}%"

        

def send_data(data, host, port=65524):
    serialized_data = json.dumps(data)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((host, port))
        client_socket.sendall(serialized_data.encode())


def main():
    if 'SUMO_HOME' in os.environ:
        sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))
    else:
        raise EnvironmentError("SUMO_HOME environment variable not set")

    simulation = traci.start(["sumo", "-c", "quickstart.sumocfg", "--step-length", "0.1"]) 
    print(f"Simulation {simulation} is starting..\n")

    vehicle1_id = "veh0"
    vehicle2_id = "veh13"
    vehicle3_id = "veh469"

    data_v1  = {}
    data_v2  = {}
    data_v3  = {}

    dataset_v1  = {}
    dataset_v2  = {}
    dataset_v3  = {}

    data_map = {
    "127.0.0.2": dataset_v1,
    "127.0.0.3": dataset_v2,
    "127.0.0.4": dataset_v3
    }

    list_deltaV_v1 = []
    list_deltaV_v2 = []
    list_deltaV_v3 = []

    list_time_v1 = []
    list_time_v2 = []
    list_time_v3 = []

    list_speed_v1 = []
    list_speed_v2 = []
    list_speed_v3 = []

    list_throttle_v1 = []
    list_throttle_v2 = []
    list_throttle_v3 = []

    list_brake_v1 = []
    list_brake_v2 = []
    list_brake_v3 = []

    previous_speed_v1 = 0
    previous_speed_v2 = 0
    previous_speed_v3 = 0

    counter = 0

    for step in range(1, 90001):
        time.sleep(0.1) 
        try:
            traci.simulationStep()
            active_vehicles = traci.vehicle.getIDList()
            colliding_vehicles = traci.simulation.getCollidingVehiclesIDList()

            if len(colliding_vehicles) > 0: 
                    print(f"\nCOLLISION DETECTED in step {step}. Sending colliding vehicles' data ({colliding_vehicles[0]}, {colliding_vehicles[1]})\n")

                    dataset_v2['frontal_airbag_deployment_v2'] = 10
                    dataset_v3['frontal_airbag_deployment_v3'] = 25
                    dataset_v2['frontal_airbag_deployment_passanger_v2'] = 10
                    dataset_v3['frontal_airbag_deployment_passanger_v3'] = 25
                    dataset_v2['number_of_event_v2'] = 1
                    dataset_v3['number_of_event_v3'] = 1
                    dataset_v2['time_event1-2_v2'] = "_"
                    dataset_v3['time_event1-2_v3'] = "_"
                    dataset_v2['complete_file_recorded_v2'] = "Yes" if len(dataset_v2) == 14 else "No"
                    dataset_v3['complete_file_recorded_v3'] = "Yes" if len(dataset_v3) == 14 else "No"

                    print(f"Vehicle {colliding_vehicles[0]} collision data: {dataset_v3}\n")
                    print(f"Vehicle {colliding_vehicles[1]} collision data: {dataset_v2}\n")

                    send_data(dataset_v3, "127.0.0.4")
                    send_data(dataset_v2, "127.0.0.3")
                    print(f"Data sent.")
                    break
            
            if vehicle1_id in active_vehicles:
                t1 = threading.Thread(target=track_vehicle_data, args=(vehicle1_id, data_v1))
                t1.start()
                t1.join()

                current_speed_v1 = data_v1[vehicle1_id][64]
                current_time_v1 = data_v1[vehicle1_id][102]

                deltaV_v1 = format(current_speed_v1 - previous_speed_v1, ".0f")
                list_deltaV_v1.append(deltaV_v1)
                list_time_v1.append(format(current_time_v1, ".2f"))

                if len(list_deltaV_v1) == 3:
                    max_deltaV_v1 = max(list_deltaV_v1)
                    time_max_deltaV_v1 = list_time_v1[list_deltaV_v1.index(max_deltaV_v1)]
                    dataset_v1['list_deltaV_v1'] = list_deltaV_v1.copy()
                    dataset_v1['max_deltaV_v1'] = max_deltaV_v1
                    dataset_v1['time_max_deltaV_v1'] = time_max_deltaV_v1
                    dataset_v1['ignition_cycle_v1'] = 60000
                    dataset_v1['ignition_cycle_download_v1'] = 60000
                    dataset_v1['seatbelt_v1'] = "on"
                    dataset_v1['frontal_airbag_warning_v1'] = "on"
                    list_deltaV_v1.clear()
                    list_time_v1.clear()
                    
            else:
                data_v1.clear()
                dataset_v1.clear()

            if vehicle2_id in active_vehicles and vehicle3_id in active_vehicles:   
                t2 = threading.Thread(target=track_vehicle_data, args=(vehicle2_id, data_v2))
                t3 = threading.Thread(target=track_vehicle_data, args=(vehicle3_id, data_v3))
                t2.start()
                t3.start()
                t2.join()
                t3.join()

                current_speed_v2 = data_v2[vehicle2_id][64]
                current_time_v2 = data_v2[vehicle2_id][102]
                current_speed_v3 = data_v3[vehicle3_id][64]
                current_time_v3 = data_v3[vehicle3_id][102]                

                deltaV_v2 = format(current_speed_v2 - previous_speed_v2, ".0f") 
                deltaV_v3 = format(current_speed_v3 - previous_speed_v3, ".0f") 

                list_deltaV_v2.append(deltaV_v2)
                list_time_v2.append(format(current_time_v2, ".2f"))
                list_deltaV_v3.append(deltaV_v3)
                list_time_v3.append(format(current_time_v3, ".2f"))              

                if len(list_deltaV_v2) == 3 and (len(list_deltaV_v2) == len(list_deltaV_v3)):
                    max_deltaV_v2 = max(list_deltaV_v2)
                    max_deltaV_v3 = max(list_deltaV_v3)
                    time_max_deltaV_v2 = list_time_v2[list_deltaV_v2.index(max_deltaV_v2)]
                    time_max_deltaV_v3 = list_time_v3[list_deltaV_v3.index(max_deltaV_v3)]
                    dataset_v2['list_deltaV_v2'] = list_deltaV_v2.copy()
                    dataset_v2['max_deltaV_v2'] = max_deltaV_v2
                    dataset_v2['time_max_deltaV_v2'] = time_max_deltaV_v2
                    dataset_v2['ignition_cycle_v2'] = 60000
                    dataset_v2['ignition_cycle_download_v2'] = 60000
                    dataset_v2['seatbelt_v2'] = "on"
                    dataset_v2['frontal_airbag_warning_v2'] = "off"
                    dataset_v3['list_deltaV_v3'] = list_deltaV_v3.copy()
                    dataset_v3['max_deltaV_v3'] = max_deltaV_v3
                    dataset_v3['time_max_deltaV_v3'] = time_max_deltaV_v3
                    dataset_v3['ignition_cycle_v3'] = 60000
                    dataset_v3['ignition_cycle_download_v3'] = 60000
                    dataset_v3['seatbelt_v3'] = "off"
                    dataset_v3['frontal_airbag_warning_v3'] = "off"
                    list_deltaV_v2.clear()
                    list_deltaV_v3.clear()

            if (step % 5) == 0: 
                if vehicle1_id in active_vehicles:
                    t1 = threading.Thread(target=track_vehicle_data, args=(vehicle1_id, data_v1))
                    t1.start()
                    t1.join()

                    current_speed_v1 = data_v1[vehicle1_id][64]
                    current_time_v1 = data_v1[vehicle1_id][102]

                    # v1
                    list_speed_v1.append(format(current_speed_v1, ".1f"))

                    if current_speed_v1 == previous_speed_v1:
                        throttle_v1 = "0%"
                        throttle_v1_raw = 0
                    elif current_speed_v1 - previous_speed_v1 < 0:
                        throttle_v1_raw = (previous_speed_v1 - current_speed_v1) / 0.1 # 0.1 = passed time
                        throttle_v1 = track_throttle(previous_speed_v1, current_speed_v1)

                    if throttle_v1_raw < 0:
                        list_brake_v1.append("on")
                    else:
                        list_brake_v1.append("off")

                    list_throttle_v1.append(throttle_v1)

                    if len(list_speed_v1) == 10:
                        dataset_v1['list_speed_v1'] = list_speed_v1.copy()
                        dataset_v1['engine_throttle_v1'] = list_throttle_v1.copy()
                        dataset_v1['service_brake_v1'] = list_brake_v1.copy()
                        list_speed_v1.clear()
                        list_throttle_v1.clear()       
                        list_brake_v1.clear()

                else:
                    data_v1.clear()

                if vehicle2_id in active_vehicles and vehicle3_id in active_vehicles:   
                    t2 = threading.Thread(target=track_vehicle_data, args=(vehicle2_id, data_v2))
                    t3 = threading.Thread(target=track_vehicle_data, args=(vehicle3_id, data_v3))
                    t2.start()
                    t3.start()
                    t2.join()
                    t3.join()

                    current_speed_v2 = data_v2[vehicle2_id][64]
                    current_time_v2 = data_v2[vehicle2_id][102]
                    current_speed_v3 = data_v3[vehicle3_id][64]
                    current_time_v3 = data_v3[vehicle3_id][102]

                    # v2
                    list_speed_v2.append(format(current_speed_v2, ".1f"))

                    if current_speed_v2 == previous_speed_v2:
                        throttle_v2 = "0%"
                        throttle_v2_raw = 0
                    elif current_speed_v2 < previous_speed_v2:
                        throttle_v2_raw = (previous_speed_v2 - current_speed_v2) / 0.1  
                        throttle_v2 = track_throttle(previous_speed_v2, current_speed_v2)

                    if throttle_v2_raw < 0:
                        list_brake_v2.append("on")
                    else:
                        list_brake_v2.append("off")

                    list_throttle_v2.append(throttle_v2)

                    # v3
                    list_speed_v3.append(format(current_speed_v3, ".1f"))

                    if current_speed_v3 == previous_speed_v3:
                        throttle_v3 = "0%"
                        throttle_v3_raw = 0
                    elif current_speed_v3 < previous_speed_v3:
                        throttle_v3_raw = (previous_speed_v3 - current_speed_v3) / 0.1 
                        throttle_v3 = track_throttle(previous_speed_v3, current_speed_v3)

                    if throttle_v3_raw < 0:
                        list_brake_v3.append("on")
                    else:
                        list_brake_v3.append("off")

                    list_throttle_v3.append(throttle_v3)

                    if len(list_speed_v2) == len(list_speed_v3) == 10:
                        dataset_v2['list_speed_v2'] = list_speed_v2.copy()
                        dataset_v3['list_speed_v3'] = list_speed_v3.copy()
                        dataset_v2['engine_throttle_v2'] = list_throttle_v2.copy()
                        dataset_v3['engine_throttle_v3'] = list_throttle_v3.copy()
                        dataset_v2['service_brake_v2'] = list_brake_v2.copy()
                        dataset_v3['service_brake_v3'] = list_brake_v3.copy()
                        
                        list_speed_v2.clear()
                        list_speed_v3.clear()
                        list_throttle_v2.clear()
                        list_throttle_v3.clear()
                        list_brake_v2.clear()
                        list_brake_v3.clear()



            if (step % 50) == 0:
                counter += 1
                print(f"Counter: {counter}")
                for ip, dataset in data_map.items():
                    if dataset:
                        print(f"step {step}. Dataset {dataset} was sent to {ip}.\n") 
                        send_data(dataset, ip)
                              

            previous_speed_v1 = current_speed_v1
            previous_speed_v2 = current_speed_v2
            previous_speed_v3 = current_speed_v3 

        except Exception:
            pass

    traci.close()


if __name__ == '__main__':
    main()

