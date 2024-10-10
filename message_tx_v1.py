import os
import json
import socket
import time
from dotenv import load_dotenv
from iota_sdk import Client
from iota_sdk.wallet.common import WalletError
import functions_ed as f


def receive_and_upload(host='127.0.0.2', port=65524):
    load_dotenv()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((host, port))
        server_socket.listen()
        print(f"Listening on {host}: {port}")

        mnemonic = "wise evolve then chair image problem cradle indicate pistol math concert interest program river science hidden when cement total custom pattern trouble short laptop"
        seed = f.mnemonic_to_seed(mnemonic)
        private_key = f.seed_to_private_key(seed)

        tag_counter = 1
        data_buffer = []
        time_intervals = []
        
        while True:
            conn, addr = server_socket.accept()
            with conn:
                while True:  
                    data = conn.recv(1024)
                    if not data:
                        break

                    deserialized_data = json.loads(data)
                    data_buffer.append(deserialized_data)
                    
                    try:  
                        print(f"Data received. Uploading data to the Tangle. Counter {tag_counter}: {data_buffer[0]}\n")
                        confirmation_time = store_and_measure_time(private_key, data_buffer[0], tag_counter)
    
                        total = 0
                        time_intervals.append(confirmation_time)
                        for element in range(len(time_intervals)):
                            total = total + time_intervals[element]
                            avg_time = total / len(time_intervals)
                        print(f'\nAverage time: {avg_time}s.\n')

                        tag_counter += 1 
                        data_buffer.pop(0)
                    except (IOError, WalletError, ValueError) as e:
                        print(f"Exception! {e}")
                        time.sleep(0.1)
    

def store_and_measure_time(private_key, vehicle_data, counter):
    tag = "0x" + f"vehicle1_data#{counter}".encode("utf-8").hex()
    data = json.dumps(vehicle_data)

    signature = f.sign_data(private_key, data)

    data_with_signature = {
    'data': data,
    'signature': signature
    }

    data_with_signature_json = json.dumps(data_with_signature)
    data_with_signature_hex = "0x" + data_with_signature_json.encode("utf-8").hex()

    client = Client(nodes=['https://api.testnet.iotaledger.net'])

    block = client.build_and_post_block(tag=tag, data=data_with_signature_hex)
    start_time = time.time()
    print(f'Data block sent: {os.environ["EXPLORER_URL"]}/block/{block[0]}')

    # This part of the code should only be commented if no time measurements need to be made. 
    # This will delay the issuance of blocks in real time as the data is received in this module.
    # The delay time is dependant on the confirmation time of the block by the coordinator node (reference by a milestone).
    block_info = client.get_block_metadata(block[0])
    milestone_ref = block_info.referencedByMilestoneIndex

    while not milestone_ref:
        milestone_ref = client.get_block_metadata(block[0]).referencedByMilestoneIndex
        time.sleep(0.01)
    end_time = time.time() - start_time

    print(f"\nBlock {block[0]} was confirmed!")
    print(f'\nBlock confirmation time: {end_time}s.\n')
    return end_time

   
if __name__ == "__main__":
    receive_and_upload()
