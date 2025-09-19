#!/usr/bin/env python3
"""
Quick validation script to test funcpipe functionality.
Run this to verify the installation works correctly.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def test_imports():
    """Test that all modules import correctly."""
    print("Testing imports...")
    try:
        from funcpipe import Pipeline, filters, transforms, readers, writers
        print("✓ Core imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_basic_pipeline():
    """Test basic pipeline functionality."""
    print("Testing basic pipeline...")
    try:
        from funcpipe import Pipeline, filters, transforms
        
        # Test data
        data = [
            {"name": "alice", "age": 30, "active": True},
            {"name": "bob", "age": 25, "active": False},
            {"name": "charlie", "age": 35, "active": True}
        ]
        
        # Build pipeline
        pipeline = (Pipeline()
                   .filter(filters.equals('active', True))
                   .map(transforms.capitalize_field('name'))
                   .map(transforms.add_field('processed', True)))
        
        result = pipeline.run(data)
        
        # Validate results
        assert len(result) == 2, f"Expected 2 records, got {len(result)}"
        assert all(r['active'] for r in result), "All should be active"
        assert all(r['name'][0].isupper() for r in result), "Names should be capitalized"
        assert all(r['processed'] for r in result), "All should have processed=True"
        
        print("✓ Basic pipeline test passed")
        return True
        
    except Exception as e:
        print(f"✗ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_file_operations():
    """Test file reading and writing."""
    print("Testing file operations...")
    try:
        from funcpipe import readers, writers
        import json
        import tempfile
        import os
        
        # Create test data
        test_data = [
            {"id": 1, "name": "Test Item", "value": 100.5},
            {"id": 2, "name": "Another Item", "value": 200.0}
        ]
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Test JSON
            json_file = os.path.join(tmp_dir, "test.json")
            writers.write_json(test_data, json_file)
            loaded_data = readers.read_json(json_file)
            assert loaded_data == test_data, "JSON round-trip failed"
            
            # Test CSV
            csv_file = os.path.join(tmp_dir, "test.csv")
            writers.write_csv(test_data, csv_file)
            loaded_csv = readers.read_csv(csv_file)
            # Note: CSV reader converts strings to numbers when possible
            assert len(loaded_csv) == len(test_data), "CSV length mismatch"
            assert loaded_csv[0]['name'] == test_data[0]['name'], "CSV data mismatch"
        
        print("✓ File operations test passed")
        return True
        
    except Exception as e:
        print(f"✗ File operations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_functional_composition():
    """Test functional programming concepts."""
    print("Testing functional composition...")
    try:
        from funcpipe import Pipeline, filters, transforms
        
        # Test immutability
        original_data = [{"name": "test", "value": 10}]
        pipeline = Pipeline().map(transforms.multiply_field('value', 2))
        
        result = pipeline.run(original_data)
        
        # Original should be unchanged
        assert original_data[0]['value'] == 10, "Original data was mutated!"
        assert result[0]['value'] == 20, "Transform didn't work"
        
        # Test curried functions
        age_filter = filters.greater_than('age', 25)
        test_item1 = {"age": 30}
        test_item2 = {"age": 20}
        
        assert age_filter(test_item1) == True, "Curried filter failed"
        assert age_filter(test_item2) == False, "Curried filter failed"
        
        print("✓ Functional composition test passed")
        return True
        
    except Exception as e:
        print(f"✗ Functional composition test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("FuncPipe Validation Tests")
    print("=" * 30)
    
    tests = [
        test_imports,
        test_basic_pipeline,
        test_file_operations,
        test_functional_composition
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            results.append(False)
        print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("=" * 30)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! FuncPipe is ready to use.")
        return 0
    else:
        print("❌ Some tests failed. Check the output above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
