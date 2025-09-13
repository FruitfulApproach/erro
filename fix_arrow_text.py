with open('core/proof_step.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix lines 413-414 - add arrow_text definition and remove duplicate
lines[412] = '        # Create kernel object name (𝑲f) - bold K for kernel\n'
lines[413] = '        arrow_text = self.arrow.get_text()\n'
lines[414] = '        kernel_name = f"𝑲{arrow_text}"\n'

with open('core/proof_step.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
    
print('Fixed kernel name generation with arrow_text definition')