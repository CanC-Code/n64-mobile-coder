import os
import json
import re

# Configuration
DKR_PATH = os.path.expanduser("~/Diddy-Kong-Racing")
OUTPUT_FILE = "n64_dataset.jsonl"

def parse_c_file(filepath):
    """Extracts function names from a C file."""
    functions = {}
    with open(filepath, 'r', errors='ignore') as f:
        content = f.read()
        # Basic regex to find function definitions like `void func_name(...) {`
        pattern = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_*\s]+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*\{', re.MULTILINE)
        for match in pattern.finditer(content):
            func_name = match.group(1)
            # Find the end of the function by matching braces (simplified)
            start = match.start()
            brace_count = 1
            i = match.end()
            while i < len(content) and brace_count > 0:
                if content[i] == '{': brace_count += 1
                elif content[i] == '}': brace_count -= 1
                i += 1
            functions[func_name] = content[start:i]
    return functions

def main():
    if not os.path.exists(DKR_PATH):
        print(f"Error: {DKR_PATH} not found.")
        return

    dataset = []
    
    # Walk through the src directory
    for root, _, files in os.walk(os.path.join(DKR_PATH, 'src')):
        for file in files:
            if file.endswith('.c'):
                c_path = os.path.join(root, file)
                funcs = parse_c_file(c_path)
                
                # Look for the corresponding .s file
                rel_path = os.path.relpath(c_path, os.path.join(DKR_PATH, 'src'))
                s_path = os.path.join(DKR_PATH, 'asm', rel_path.replace('.c', '.s'))
                
                if os.path.exists(s_path):
                    with open(s_path, 'r', errors='ignore') as f:
                        asm_content = f.read()
                        
                    for func_name, c_code in funcs.items():
                        # Extract the specific assembly block for this function
                        asm_match = re.search(rf'glabel {func_name}.*?endlabel {func_name}', asm_content, re.DOTALL)
                        if asm_match:
                            asm_code = asm_match.group(0)
                            dataset.append({
                                "messages": [
                                    {"role": "system", "content": "You are an N64 decompilation expert. Convert the following MIPS assembly to matching C code."},
                                    {"role": "user", "content": asm_code},
                                    {"role": "assistant", "content": c_code}
                                ]
                            })

    with open(OUTPUT_FILE, 'w') as f:
        for item in dataset:
            f.write(json.dumps(item) + '\n')
            
    print(f"Extracted {len(dataset)} function pairs to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
