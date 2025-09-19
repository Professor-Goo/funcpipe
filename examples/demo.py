#!/usr/bin/env python3
"""
Example usage of funcpipe library demonstrating functional data processing.
"""

from funcpipe import Pipeline, filters, transforms, readers, writers


def example_employee_processing():
    """Process employee data using functional pipeline."""
    print("=== Employee Data Processing ===")
    
    # Read employee data
    employees = readers.read_csv('examples/employees.csv')
    print(f"Loaded {len(employees)} employees")
    
    # Build processing pipeline
    pipeline = (Pipeline()
                .filter(filters.equals('active', True))           # Only active employees
                .filter(filters.greater_than('age', 26))          # Age > 26
                .map(transforms.capitalize_field('name'))         # Capitalize names
                .map(transforms.multiply_field('salary', 1.05))   # 5% raise
                .map(transforms.round_field('salary', 0))         # Round salary
                .map(transforms.add_field('bonus', 2000))         # Add bonus
                .sort(lambda emp: emp['salary'], reverse=True))   # Sort by salary desc
    
    # Execute pipeline
    result = pipeline.run(employees)
    
    print(f"After processing: {len(result)} employees")
    print("\nProcessed employees:")
    writers.print_sample(result, n=5)
    
    # Save results
    writers.write_json(result, 'examples/processed_employees.json')
    print("Results saved to processed_employees.json")
    
    return result


def example_product_analysis():
    """Analyze product data with functional transformations."""
    print("\n=== Product Analysis ===")
    
    # Read product data
    products = readers.read_json('examples/products.json')
    print(f"Loaded {len(products)} products")
    
    # Analysis pipeline
    electronics_pipeline = (Pipeline()
                           .filter(filters.equals('category', 'Electronics'))
                           .filter(filters.equals('in_stock', True))
                           .map(transforms.compute_field('total_value', 
                                                       lambda p: p['price'] * p['quantity']))
                           .map(transforms.round_field('total_value', 2))
                           .sort(lambda p: p['total_value'], reverse=True))
    
    electronics = electronics_pipeline.run(products)
    
    print(f"In-stock electronics: {len(electronics)} items")
    print("\nTop electronics by inventory value:")
    writers.print_sample(electronics, n=3)
    
    return electronics


def example_data_transformation():
    """Demonstrate various transformation capabilities."""
    print("\n=== Data Transformation Examples ===")
    
    # Sample messy data
    messy_data = [
        {"name": "  alice JOHNSON  ", "email": "ALICE@EXAMPLE.COM", "score": 85.7234},
        {"name": "bob smith", "email": "bob@test.org", "score": 92.1},
        {"name": "Charlie Brown", "email": "charlie@demo.net", "score": 78.456}
    ]
    
    # Cleanup pipeline using function composition
    cleanup_pipeline = (Pipeline()
                       .map(transforms.strip_field('name'))              # Remove whitespace
                       .map(transforms.lower_field('name'))              # Lowercase
                       .map(transforms.capitalize_field('name'))         # Proper case
                       .map(transforms.lower_field('email'))             # Lowercase email
                       .map(transforms.round_field('score', 1))          # Round score
                       .map(transforms.compute_field('grade',            # Compute grade
                                                   lambda x: 'A' if x['score'] >= 90 
                                                           else 'B' if x['score'] >= 80 
                                                           else 'C')))
    
    cleaned = cleanup_pipeline.run(messy_data)
    
    print("Original messy data:")
    writers.print_sample(messy_data)
    
    print("After cleanup pipeline:")
    writers.print_sample(cleaned)
    
    return cleaned


def example_advanced_filtering():
    """Demonstrate advanced filtering techniques."""
    print("\n=== Advanced Filtering Examples ===")
    
    # Read employees again for filtering demo
    employees = readers.read_csv('examples/employees.csv')
    
    # Complex filter combinations
    senior_engineers = (Pipeline()
                       .filter(filters.and_filter(
                           filters.equals('department', 'Engineering'),
                           filters.greater_than('age', 30),
                           filters.greater_than('salary', 50000)
                       ))
                       .map(transforms.add_field('seniority', 'Senior')))
    
    result = senior_engineers.run(employees)
    
    print("Senior Engineers (Engineering, age>30, salary>50k):")
    writers.print_sample(result)
    
    # String filtering
    marketing_folks = (Pipeline()
                      .filter(filters.or_filter(
                          filters.contains('department', 'Marketing'),
                          filters.contains('name', 'Adams')
                      ))
                      .sort(lambda p: p['name']))
    
    marketing = marketing_folks.run(employees)
    print("\nMarketing team + people named Adams:")
    writers.print_sample(marketing)
    
    return result, marketing


if __name__ == '__main__':
    # Run all examples
    try:
        example_employee_processing()
        example_product_analysis()
        example_data_transformation()
        example_advanced_filtering()
        
        print("\n=== All Examples Complete! ===")
        print("Check the examples/ directory for output files.")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        import traceback
        traceback.print_exc()
