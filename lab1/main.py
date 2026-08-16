import time
import os
import matplotlib.pyplot as plt
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

from aes128 import AES128Cipher
from aes256 import AES256Cipher

def measure_execution_time(cipher_instance, padded_data: bytes, frequency: int, num_trials: int = 10) -> float:
    trial_durations = []
    for _ in range(num_trials):
        start_time = time.perf_counter()
        for _ in range(frequency):
            _ = cipher_instance.encrypt_prepadded(padded_data)
        end_time = time.perf_counter()
        trial_durations.append(end_time - start_time)
    return sum(trial_durations) / len(trial_durations)

def main():
    if not os.path.exists("test.txt"):
        from generate_test_file import create_test_file
        create_test_file("test.txt", 1.0)

    with open("test.txt", "rb") as f:
        data = f.read()

    padded_data = pad(data, AES.block_size)
    
    ciphers = [
        ("AES-128", AES128Cipher(), "AES-128"),
        ("AES-256", AES256Cipher(), "AES-256")
    ]
    
    frequencies = [10, 40, 70, 100]
    
    print("\n" + "="*80)
    print(f"{'S.No.':<6} | {'Function Name':<12} | {'Frequency':<10} | {'Total Exec Time (s)':<22} | {'Remarks'}")
    print("="*80)
    
    sno = 1
    plot_data = {}
    
    for cipher_name, cipher_obj, remark in ciphers:
        times = []
        for freq in frequencies:
            total_time = measure_execution_time(cipher_obj, padded_data, freq, num_trials=10)
            times.append(total_time)
            print(f"{sno:<6} | {cipher_name:<12} | {freq:<10} | {total_time:<22.6f} | {remark}")
            sno += 1
        plot_data[cipher_name] = times

    print("="*80 + "\n")

    plt.figure(figsize=(8, 5))
    for name, times in plot_data.items():
        plt.plot(frequencies, times, marker='o', label=name)
    plt.title("AES-128 vs AES-256 Execution Time")
    plt.xlabel("Frequency")
    plt.ylabel("Execution Time (s)")
    plt.grid(True, linestyle='--')
    plt.legend()
    plt.tight_layout()
    plt.savefig("aes_execution_time_comparison.png", dpi=300)
    plt.close()

if __name__ == "__main__":
    main()
