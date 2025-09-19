"""
Tests for funcpipe pipeline functionality.
"""

import unittest
from funcpipe import Pipeline, filters, transforms


class TestPipeline(unittest.TestCase):
    
    def setUp(self):
        """Set up test data."""
        self.sample_data = [
            {"name": "Alice", "age": 30, "salary": 50000},
            {"name": "bob", "age": 25, "salary": 45000},
            {"name": "Charlie", "age": 35, "salary": 60000},
            {"name": "diana", "age": 28, "salary": 52000}
        ]
    
    def test_empty_pipeline(self):
        """Test empty pipeline returns original data."""
        pipeline = Pipeline()
        result = pipeline.run(self.sample_data)
        self.assertEqual(result, self.sample_data)
    
    def test_filter_greater_than(self):
        """Test filtering with greater than."""
        pipeline = Pipeline().filter(filters.greater_than('age', 27))
        result = pipeline.run(self.sample_data)
        self.assertEqual(len(result), 3)  # Alice, Charlie, diana
        self.assertTrue(all(item['age'] > 27 for item in result))
    
    def test_filter_equals(self):
        """Test filtering with equals."""
        pipeline = Pipeline().filter(filters.equals('name', 'Alice'))
        result = pipeline.run(self.sample_data)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'Alice')
    
    def test_map_capitalize(self):
        """Test capitalizing field."""
        pipeline = Pipeline().map(transforms.capitalize_field('name'))
        result = pipeline.run(self.sample_data)
        expected_names = ['Alice', 'Bob', 'Charlie', 'Diana']
        actual_names = [item['name'] for item in result]
        self.assertEqual(actual_names, expected_names)
    
    def test_map_multiply(self):
        """Test multiplying numeric field."""
        pipeline = Pipeline().map(transforms.multiply_field('salary', 1.1))
        result = pipeline.run(self.sample_data)
        self.assertEqual(result[0]['salary'], 55000.0)  # Alice: 50000 * 1.1
    
    def test_chained_operations(self):
        """Test chaining multiple operations."""
        pipeline = (Pipeline()
                   .filter(filters.greater_than('age', 25))
                   .map(transforms.capitalize_field('name'))
                   .map(transforms.add_field('status', 'active'))
                   .sort(lambda item: item['age']))
        
        result = pipeline.run(self.sample_data)
        
        # Should have 3 records (age > 25)
        self.assertEqual(len(result), 3)
        
        # All should have status 'active'
        self.assertTrue(all(item['status'] == 'active' for item in result))
        
        # Should be sorted by age
        ages = [item['age'] for item in result]
        self.assertEqual(ages, sorted(ages))
        
        # Names should be capitalized
        names = [item['name'] for item in result]
        self.assertTrue(all(name[0].isupper() for name in names))
    
    def test_take_and_skip(self):
        """Test take and skip operations."""
        pipeline = Pipeline().skip(1).take(2)
        result = pipeline.run(self.sample_data)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], 'bob')  # Second item
        self.assertEqual(result[1]['name'], 'Charlie')  # Third item
    
    def test_immutability(self):
        """Test that operations don't modify original data."""
        original_data = self.sample_data.copy()
        pipeline = (Pipeline()
                   .map(transforms.upper_field('name'))
                   .map(transforms.multiply_field('salary', 2)))
        
        result = pipeline.run(self.sample_data)
        
        # Original data should be unchanged
        self.assertEqual(self.sample_data, original_data)
        
        # Result should be modified
        self.assertNotEqual(result, original_data)
        self.assertTrue(all(item['name'].isupper() for item in result))


class TestFilters(unittest.TestCase):
    
    def test_comparison_filters(self):
        """Test various comparison filters."""
        item = {"age": 30, "score": 85.5}
        
        self.assertTrue(filters.greater_than('age', 25)(item))
        self.assertFalse(filters.greater_than('age', 35)(item))
        
        self.assertTrue(filters.less_than('score', 90)(item))
        self.assertFalse(filters.less_than('score', 80)(item))
        
        self.assertTrue(filters.equals('age', 30)(item))
        self.assertFalse(filters.equals('age', 25)(item))
    
    def test_string_filters(self):
        """Test string-based filters."""
        item = {"name": "Alice Johnson", "email": "alice@example.com"}
        
        self.assertTrue(filters.contains('name', 'Alice')(item))
        self.assertFalse(filters.contains('name', 'Bob')(item))
        
        self.assertTrue(filters.starts_with('email', 'alice')(item))
        self.assertFalse(filters.starts_with('email', 'bob')(item))
        
        self.assertTrue(filters.ends_with('email', '.com')(item))
        self.assertFalse(filters.ends_with('email', '.org')(item))
    
    def test_null_filters(self):
        """Test null checking filters."""
        item = {"name": "Alice", "middle_name": None, "age": 30}
        
        self.assertTrue(filters.is_null('middle_name')(item))
        self.assertFalse(filters.is_null('name')(item))
        
        self.assertTrue(filters.is_not_null('name')(item))
        self.assertFalse(filters.is_not_null('middle_name')(item))
    
    def test_combined_filters(self):
        """Test combining filters with and/or."""
        item = {"name": "Alice", "age": 30, "active": True}
        
        combined_and = filters.and_filter(
            filters.greater_than('age', 25),
            filters.equals('active', True)
        )
        self.assertTrue(combined_and(item))
        
        combined_or = filters.or_filter(
            filters.equals('name', 'Bob'),
            filters.greater_than('age', 25)
        )
        self.assertTrue(combined_or(item))


class TestTransforms(unittest.TestCase):
    
    def test_field_transforms(self):
        """Test basic field transformations."""
        item = {"name": "alice", "age": 30}
        
        # Capitalize
        result = transforms.capitalize_field('name')(item)
        self.assertEqual(result['name'], 'Alice')
        self.assertEqual(result['age'], 30)  # Other fields unchanged
        
        # Add field
        result = transforms.add_field('status', 'active')(item)
        self.assertEqual(result['status'], 'active')
        self.assertIn('name', result)  # Original fields preserved
        
        # Remove field
        result = transforms.remove_field('age')(item)
        self.assertNotIn('age', result)
        self.assertIn('name', result)
    
    def test_numeric_transforms(self):
        """Test numeric transformations."""
        item = {"price": 100.0, "quantity": 5}
        
        # Multiply
        result = transforms.multiply_field('price', 1.2)(item)
        self.assertEqual(result['price'], 120.0)
        
        # Add
        result = transforms.add_to_field('quantity', 10)(item)
        self.assertEqual(result['quantity'], 15)
        
        # Round
        item_with_decimal = {"value": 3.14159}
        result = transforms.round_field('value', 2)(item_with_decimal)
        self.assertEqual(result['value'], 3.14)
    
    def test_computed_fields(self):
        """Test computed field transformation."""
        item = {"first_name": "Alice", "last_name": "Johnson", "age": 30}
        
        full_name_transform = transforms.compute_field(
            'full_name', 
            lambda x: f"{x['first_name']} {x['last_name']}"
        )
        
        result = full_name_transform(item)
        self.assertEqual(result['full_name'], 'Alice Johnson')
        self.assertIn('first_name', result)  # Original fields preserved


if __name__ == '__main__':
    unittest.main()
