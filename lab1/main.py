import time
import os

from aes128 import AES128Cipher
from aes256 import AES256Cipher
from triple_des import TripleDESCipher
from rsa_cipher import RSACipher
from sha256_hash import SHA256Hash

def solver(cipher_func, data, frequencies, num_readings=10):
    results = []
    for freq in frequencies:
        total_times = []
        for _ in range(num_readings):
            start_time = time.perf_counter()
            for _ in range(freq):
                cipher_func(data)
            end_time = time.perf_counter()
            total_times.append(end_time - start_time)
        
        avg_time = sum(total_times) / num_readings
        results.append(avg_time)
    return results

def main():
    if not os.path.exists("test.txt"):
        print("Error: test.txt not found.")
        return
        
    with open("test.txt", "rb") as f:
        data = f.read(100000)

    aes128 = AES128Cipher()
    aes256 = AES256Cipher()
    des3 = TripleDESCipher()
    rsa = RSACipher()
    sha256 = SHA256Hash()

    frequencies = [10, 40, 70, 100]
    
    algorithms = {
        "Triple DES": des3.encrypt,
        "AES-128": aes128.encrypt,
        "AES-256": aes256.encrypt,
        "RSA": rsa.encrypt,
        "SHA256": sha256.encrypt
    }

    results = {}
    
    print("-" * 55)
    print(f"{'S.No':<5} | {'Function Name':<15} | {'Freq':<5} | {'Execution Time (s)':<18}")
    print("-" * 55)
    
    s_no = 1
    for name, func in algorithms.items():
        times = solver(func, data, frequencies)
        results[name] = times
        
        for i, freq in enumerate(frequencies):
            print(f"{s_no:<5} | {name:<15} | {freq:<5} | {times[i]:<18.6f}")
            s_no += 1
            
    print("-" * 55)
    
    try:
        import matplotlib.pyplot as plt
        plt.figure(figsize=(10, 6))
        for name, times in results.items():
            plt.plot(frequencies, times, marker='o', label=name)
            
        plt.title("Execution Time vs Frequency")
        plt.xlabel("Frequency")
        plt.ylabel("Execution Time (seconds) - Log Scale")
        plt.yscale("log")
        plt.legend()
        plt.grid(True, which="both", ls="--")
        plt.savefig("execution_time_comparison.png")
    except Exception as e:
        print(f"Plotting failed: {e}")

if __name__ == "__main__":
    main()
