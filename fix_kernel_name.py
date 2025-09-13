with open('core/proof_step.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Replace line 414 (0-indexed as 413)  
lines[413] = '        kernel_name = f"𝑲{arrow_text}"\n'

with open('core/proof_step.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
    
print('Updated kernel name to use bold K')