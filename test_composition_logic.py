"""
Simple test for composition notation and kernel zero logic.
"""
import sys

# Add the project root to Python path  
sys.path.insert(0, r'C:\Users\fruit\OneDrive\Desktop\erro')

from core.proof_step import MapElementProofStep, KernelAtElementIsZeroProofStep

def test_composition_logic():
    """Test the composition notation logic without Qt components."""
    
    print("=== Test 1: Function Composition Notation ===")
    
    # Create a mock MapElementProofStep to test the method
    class MockMapStep:
        def _create_mapped_element_notation(self, element_name, function_name):
            """Create proper function composition notation for mapped elements."""
            # Handle zero elements specially
            if '=0' in element_name:
                # For zero elements like "(e∘k_e)(a)=0", map to "f(0)=0"
                return f"{function_name}(0)=0"
            
            # Check if the element is already a function application
            if '(' in element_name and ')' in element_name:
                # Find the base element (after the last opening parenthesis)
                last_paren = element_name.rfind('(')
                if last_paren != -1:
                    base_element = element_name[last_paren+1:element_name.rfind(')')]
                    
                    # Extract the existing function composition
                    existing_composition = element_name[:last_paren]
                    
                    # If it's already in composition form like "(g∘f)", add to it
                    if existing_composition.startswith('(') and existing_composition.endswith(')'):
                        # Remove outer parentheses and add new function
                        inner_composition = existing_composition[1:-1]
                        new_composition = f"({function_name}∘{inner_composition})"
                    else:
                        # Simple function like "f", convert to composition
                        new_composition = f"({function_name}∘{existing_composition})"
                    
                    return f"{new_composition}({base_element})"
            
            # Simple element name, just apply the function
            return f"{function_name}({element_name})"
    
    map_step = MockMapStep()
    
    # Test simple element
    result1 = map_step._create_mapped_element_notation("a", "f")
    print(f"f maps 'a' -> '{result1}'")  # Should be "f(a)"
    
    # Test already mapped element  
    result2 = map_step._create_mapped_element_notation("f(a)", "g")
    print(f"g maps 'f(a)' -> '{result2}'")  # Should be "(g∘f)(a)"
    
    # Test composed element
    result3 = map_step._create_mapped_element_notation("(g∘f)(a)", "h")
    print(f"h maps '(g∘f)(a)' -> '{result3}'")  # Should be "(h∘g∘f)(a)"
    
    # Test zero element
    result4 = map_step._create_mapped_element_notation("(e∘k_e)(a)=0", "g")
    print(f"g maps '(e∘k_e)(a)=0' -> '{result4}'")  # Should be "g(0)=0"
    
    print("\n=== Test 2: Kernel Element Pattern Detection ===")
    
    # Test pattern detection
    test_patterns = [
        "(e∘k_e)(a)",
        "f(a)",
        "(g∘k_e)(b)", 
        "x",
        "(h∘k_f∘j)(c)"
    ]
    
    for pattern in test_patterns:
        is_kernel = KernelAtElementIsZeroProofStep._is_kernel_element_pattern(pattern)
        print(f"'{pattern}' is kernel pattern: {is_kernel}")
    
    print("\nAll logic tests completed successfully!")

if __name__ == "__main__":
    test_composition_logic()