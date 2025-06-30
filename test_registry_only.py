"""Test just the registry and capability descriptions"""

from capabilities.registry import get_registry

def test_registry():
    """Test capability registry"""
    print("Testing Capability Registry")
    print("=" * 50)
    
    registry = get_registry()
    capabilities = registry.get_all_instances()
    
    print(f"\nFound {len(capabilities)} capabilities:")
    for name in sorted(capabilities.keys()):
        print(f"  - {name}")
    
    print("\n\nCapability Descriptions:")
    print("-" * 50)
    
    for name, capability in sorted(capabilities.items()):
        desc = capability.describe()
        print(f"\n{name.upper()}:")
        print(f"  Purpose: {desc.purpose}")
        print(f"  Category: {desc.category}")
        print(f"  Examples: {len(desc.examples)}")
        
        # Show first example
        if desc.examples:
            print(f"  First example: '{desc.examples[0]}'")
    
    # Test help text generation
    print("\n\nHelp Text Generation:")
    print("-" * 50)
    help_text = registry.get_help_text()
    print(help_text[:500] + "..." if len(help_text) > 500 else help_text)

if __name__ == "__main__":
    test_registry()