import subprocess

output_file = "results.txt"
script_to_run = "script/main.py"
script_args = ["-single_run", "-pre_move", "-state_bouncing", "-no_csv", "-seed", "2065223488"]
num_iterations = 20  # Adjust as needed

results = []

for i in range(num_iterations):
    print(i+1, "/", num_iterations, end="\r")  # Display the progress
    result = subprocess.run(["python", script_to_run] + script_args, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error running script: {result.stderr}")
        continue  # Skip this iteration if an error occurs

    last_line = result.stdout.strip().split("\n")[-1]  # Extract the last printed line
    results.append(last_line)

    # Save to file
    with open(output_file, "w") as f:
        f.write("\n".join(results) + "\n")
