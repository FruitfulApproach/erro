# Fix the missing arrow_text definition
with open('core/proof_step.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Insert the missing arrow_text line before the kernel_name line
lines.insert(413, '        arrow_text = self.arrow.get_text()\n')

with open('core/proof_step.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
    
print('Added missing arrow_text definition')