#!/usr/bin/env python3
"""
Pure test for file_write functionality in strands_tools
"""
import asyncio
import os
import sys

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_file_write_directly():
    """Test the file_write tool directly"""
    print("=== Direct Test of file_write from strands_tools ===")
    
    try:
        from strands_tools import file_write
        print(f"✓ file_write imported successfully")
        print(f"✓ Type: {type(file_write)}")
        
        # Try to inspect what file_write actually is
        print(f"✓ file_write object: {file_write}")
        print(f"✓ dir(file_write): {dir(file_write)[:10]}...")  # First 10 attributes
        
        # Test with a simple write
        test_content = "# Test File\nThis is a test file.\n\n- Item 1\n- Item 2\n"
        test_path = "reports/test_output.md"
        
        print(f"\nTrying to write to: {test_path}")
        
        # First create the directory if it doesn't exist
        os.makedirs(os.path.dirname(test_path), exist_ok=True)
        
        # Try calling file_write as a function
        result = file_write(test_path, test_content)
        print(f"✓ file_write result: {result}")
        
        # Verify the file was created
        if os.path.exists(test_path):
            print("✓ File was created successfully")
            with open(test_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"✓ File content: {content[:100]}...")
        else:
            print("✗ File was not created")
            
    except Exception as e:
        print(f"✗ Direct file_write test failed: {e}")
        import traceback
        traceback.print_exc()


def test_file_write_as_method():
    """Test file_write as a method of strands_tools module"""
    print("\n=== Testing file_write as module method ===")
    
    try:
        import strands_tools
        print(f"✓ strands_tools imported: {type(strands_tools)}")
        print(f"✓ Available attributes: {[attr for attr in dir(strands_tools) if 'file' in attr.lower()]}")
        
        if hasattr(strands_tools, 'file_write'):
            file_write_func = strands_tools.file_write
            print(f"✓ Found file_write as attribute: {type(file_write_func)}")
            
            # Test with the same content
            test_content = "# Test File 2\nThis is another test file.\n\n- Item A\n- Item B\n"
            test_path = "reports/test_output2.md"
            
            # Create directory if needed
            os.makedirs(os.path.dirname(test_path), exist_ok=True)
            
            # Try calling it
            result = file_write_func(test_path, test_content)
            print(f"✓ file_write method result: {result}")
            
            # Verify the file was created
            if os.path.exists(test_path):
                print("✓ File was created successfully with method")
            else:
                print("✗ File was not created with method")
        else:
            print("✗ file_write not found as attribute of strands_tools")
            print(f"✗ All attributes: {dir(strands_tools)}")
            
    except Exception as e:
        print(f"✗ Module method test failed: {e}")
        import traceback
        traceback.print_exc()


def test_with_agent_tool_pattern():
    """Test using agent.tool pattern similar to how it's used in documentation"""
    print("\n=== Testing file_write using Agent.tool pattern ===")
    
    try:
        from strands import Agent
        from strands_tools import file_write
        
        # Create a simple agent with file_write tool
        agent = Agent(tools=[file_write])
        print("✓ Agent created with file_write tool")
        
        # Test writing using agent's tool interface
        test_content = "# Test File 3\nAgent tool test.\n\n- Test A\n- Test B\n"
        test_path = "reports/test_output3.md"
        
        os.makedirs(os.path.dirname(test_path), exist_ok=True)
        
        # Use the agent's tool interface
        result = agent.tool.file_write(path=test_path, content=test_content)
        print(f"✓ Agent tool result: {result}")
        
        # Verify
        if os.path.exists(test_path):
            print("✓ File created via agent tool")
        else:
            print("✗ File not created via agent tool")
        
    except Exception as e:
        print(f"✗ Agent tool test failed: {e}")
        import traceback
        traceback.print_exc()


def test_file_write_signature():
    """Test to understand the file_write function signature"""
    print("\n=== Testing file_write signature and properties ===")
    
    try:
        from strands_tools import file_write
        print(f"✓ Function: {file_write}")
        print(f"✓ Type: {type(file_write)}")
        print(f"✓ Callable: {callable(file_write)}")
        print(f"✓ Dir: {dir(file_write)}")
        
        # Check if it has attributes like __name__, __doc__, etc.
        print(f"✓ Has __name__: {hasattr(file_write, '__name__')}")
        if hasattr(file_write, '__name__'):
            print(f"✓ __name__: {file_write.__name__}")
        
        print(f"✓ Has __doc__: {hasattr(file_write, '__doc__')}")
        if hasattr(file_write, '__doc__'):
            print(f"✓ __doc__: {file_write.__doc__[:100]}..." if file_write.__doc__ else "No doc")
        
        print(f"✓ Has __call__: {hasattr(file_write, '__call__')}")
        
    except Exception as e:
        print(f"✗ Signature test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🧪 Testing file_write functionality in strands_tools\n")
    
    test_file_write_signature()
    test_file_write_directly()
    test_file_write_as_method()
    test_with_agent_tool_pattern()
    
    print("\n🔍 Analysis complete. This will help determine the correct way to use file_write.")