# Fix the kernel name with proper bold Unicode
with open('core/proof_step.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix line 412 and 414 with proper bold "Ker"
lines[411] = '        # Create kernel object name (𝐊𝐞𝐫 f) - bold Ker\n'
lines[413] = '        kernel_name = f"𝐊𝐞𝐫 {arrow_text}"\n'

with open('core/proof_step.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
    
print('Fixed kernel name with proper bold Ker')