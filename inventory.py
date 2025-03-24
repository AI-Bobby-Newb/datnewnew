import os
from datetime import datetime

class InventoryManager:
    """Manages inventory operations for the vape store system"""
    
    def __init__(self, db):
        """Initialize with database connection"""
        self.db = db
    
    def view_all_products(self):
        """Display all products in inventory"""
        products = self.db.execute_query("""
            SELECT p.*, c.name as category_name 
            FROM products p
            LEFT JOIN categories c ON p.category = c.name
            ORDER BY p.name
        """)
        
        if not products:
            print("No products found in inventory.")
            return
        
        print("\nCurrent Inventory:")
        print(f"{'ID':<4}| {'SKU':<10}| {'Name':<30}| {'Category':<15}| {'Price':<8}| {'Quantity':<8}")
        print("-" * 80)
        
        for product in products:
            print(f"{product['id']:<4}| {product['sku']:<10}| {product['name']:<30}| {product['category_name']:<15}| ${product['price']:<7.2f}| {product['quantity']:<8}")
        
        input("\nPress Enter to continue...")
    
    def add_product(self):
        """Add a new product to inventory"""
        print("\nAdd New Product")
        
        # Get categories for selection
        categories = self.db.execute_query("SELECT name FROM categories ORDER BY name")
        if not categories:
            print("Error: No categories found. Please add categories first.")
            return
        
        # Generate SKU
        sku = f"VS{datetime.now().strftime('%y%m%d%H%M')}"
        
        # Get product details
        name = input("Product Name: ")
        
        # Display categories
        print("\nAvailable Categories:")
        for i, cat in enumerate(categories, 1):
            print(f"{i}. {cat['name']}")
        
        cat_choice = int(input("\nSelect Category (number): "))
        if cat_choice < 1 or cat_choice > len(categories):
            print("Invalid category selection.")
            return
        
        category = categories[cat_choice-1]['name']
        subcategory = input("Subcategory (optional): ")
        brand = input("Brand: ")
        description = input("Description: ")
        
        try:
            price = float(input("Retail Price: $"))
            cost = float(input("Cost Price: $"))
            quantity = int(input("Initial Quantity: "))
            min_stock = int(input("Minimum Stock Level: "))
        except ValueError:
            print("Error: Price, cost, quantity and minimum stock must be numbers.")
            return
        
        nicotine_strength = input("Nicotine Strength (if applicable): ")
        flavor = input("Flavor (if applicable): ")
        
        # Insert the new product
        success = self.db.execute_update("""
            INSERT INTO products 
            (sku, name, category, subcategory, brand, description, price, cost, 
             quantity, min_stock, nicotine_strength, flavor)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (sku, name, category, subcategory, brand, description, price, cost, 
              quantity, min_stock, nicotine_strength, flavor))
        
        if success:
            print(f"\nProduct '{name}' added successfully with SKU: {sku}")
        else:
            print("\nFailed to add product. Please try again.")
        
        input("\nPress Enter to continue...")
    
    def update_product(self):
        """Update existing product details"""
        search = input("\nEnter product name, SKU or ID to update: ")
        
        products = self.db.execute_query("""
            SELECT * FROM products 
            WHERE id = ? OR sku LIKE ? OR name LIKE ?
        """, (search, f"%{search}%", f"%{search}%"))
        
        if not products:
            print(f"No products found matching '{search}'.")
            return
        
        if len(products) > 1:
            print("\nMultiple products found:")
            for i, product in enumerate(products, 1):
                print(f"{i}. [{product['sku']}] {product['name']}")
            
            choice = int(input("\nSelect product to update (number): "))
            if choice < 1 or choice > len(products):
                print("Invalid selection.")
                return
            
            product = products[choice-1]
        else:
            product = products[0]
        
        print(f"\nUpdating Product: {product['name']} (SKU: {product['sku']})")
        print("\nLeave field empty to keep current value.")
        
        # Get current values for reference
        name = input(f"Name [{product['name']}]: ") or product['name']
        brand = input(f"Brand [{product['brand']}]: ") or product['brand']
        description = input(f"Description [{product['description']}]: ") or product['description']
        
        try:
            price_input = input(f"Retail Price [${product['price']}]: ")
            price = float(price_input) if price_input else product['price']
            
            cost_input = input(f"Cost Price [${product['cost']}]: ")
            cost = float(cost_input) if cost_input else product['cost']
            
            quantity_input = input(f"Quantity [{product['quantity']}]: ")
            quantity = int(quantity_input) if quantity_input else product['quantity']
            
            min_stock_input = input(f"Minimum Stock [{product['min_stock']}]: ")
            min_stock = int(min_stock_input) if min_stock_input else product['min_stock']
        except ValueError:
            print("Error: Price, cost, quantity and minimum stock must be numbers.")
            return
        
        # Update the product
        success = self.db.execute_update("""
            UPDATE products 
            SET name = ?, brand = ?, description = ?, price = ?, cost = ?, 
                quantity = ?, min_stock = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (name, brand, description, price, cost, quantity, min_stock, product['id']))
        
        if success:
            print(f"\nProduct '{name}' updated successfully.")
        else:
            print("\nFailed to update product. Please try again.")
        
        input("\nPress Enter to continue...")
    
    def search_products(self):
        """Search for products in inventory"""
        print("\nSearch Products")
        search = input("Enter search term (name, SKU, brand, category): ")
        
        products = self.db.execute_query("""
            SELECT p.*, c.name as category_name 
            FROM products p
            LEFT JOIN categories c ON p.category = c.name
            WHERE p.name LIKE ? OR p.sku LIKE ? OR p.brand LIKE ? OR p.category LIKE ?
            ORDER BY p.name
        """, (f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"))
        
        if not products:
            print(f"No products found matching '{search}'.")
            return
        
        print(f"\nSearch Results for '{search}':")
        print(f"{'ID':<4}| {'SKU':<10}| {'Name':<30}| {'Category':<15}| {'Price':<8}| {'Quantity':<8}")
        print("-" * 80)
        
        for product in products:
            print(f"{product['id']:<4}| {product['sku']:<10}| {product['name']:<30}| {product['category_name']:<15}| ${product['price']:<7.2f}| {product['quantity']:<8}")
        
        # Ask if user wants to view detailed information for a product
        view_detail = input("\nView product details? (y/n): ")
        if view_detail.lower() == 'y':
            product_id = input("Enter product ID: ")
            product = self.db.execute_query("SELECT * FROM products WHERE id = ?", (product_id,))
            
            if product:
                product = product[0]
                print("\nProduct Details:")
                print(f"SKU: {product['sku']}")
                print(f"Name: {product['name']}")
                print(f"Brand: {product['brand']}")
                print(f"Category: {product['category']}")
                print(f"Subcategory: {product['subcategory']}")
                print(f"Description: {product['description']}")
                print(f"Retail Price: ${product['price']:.2f}")
                print(f"Cost Price: ${product['cost']:.2f}")
                print(f"Profit Margin: ${product['price'] - product['cost']:.2f} ({(product['price'] - product['cost']) / product['price'] * 100:.1f}%)")
                print(f"Current Stock: {product['quantity']}")
                print(f"Minimum Stock Level: {product['min_stock']}")
                
                if product['nicotine_strength']:
                    print(f"Nicotine Strength: {product['nicotine_strength']}")
                if product['flavor']:
                    print(f"Flavor: {product['flavor']}")
                
                print(f"Last Updated: {product['updated_at']}")
            else:
                print(f"Product with ID {product_id} not found.")
        
        input("\nPress Enter to continue...")
    
    def check_low_stock(self):
        """Display products with stock below minimum level"""
        low_stock = self.db.execute_query("""
            SELECT * FROM products 
            WHERE quantity <= min_stock
            ORDER BY (quantity * 1.0 / min_stock), name
        """)
        
        if not low_stock:
            print("\nNo products are below minimum stock levels.")
            return
        
        print("\nLow Stock Alert:")
        print(f"{'ID':<4}| {'SKU':<10}| {'Name':<30}| {'Quantity':<8}| {'Min Stock':<9}| {'Status':<10}")
        print("-" * 80)
        
        for product in low_stock:
            ratio = product['quantity'] / product['min_stock']
            if product['quantity'] == 0:
                status = "OUT OF STOCK"
            elif ratio <= 0.25:
                status = "CRITICAL"
            elif ratio <= 0.5:
                status = "LOW"
            else:
                status = "WARNING"
            
            print(f"{product['id']:<4}| {product['sku']:<10}| {product['name']:<30}| {product['quantity']:<8}| {product['min_stock']:<9}| {status:<10}")
        
        input("\nPress Enter to continue...")
    
    def manage_categories(self):
        """Manage product categories"""
        while True:
            print("\nCategory Management")
            print("1. View All Categories")
            print("2. Add New Category")
            print("3. Edit Category")
            print("4. Delete Category")
            print("0. Back to Inventory Menu")
            
            choice = input("\nSelect an option: ")
            
            if choice == '1':
                categories = self.db.execute_query("""
                    SELECT c.*, COUNT(p.id) as product_count 
                    FROM categories c
                    LEFT JOIN products p ON c.name = p.category
                    GROUP BY c.id
                    ORDER BY c.name
                """)
                
                if not categories:
                    print("No categories found.")
                else:
                    print("\nProduct Categories:")
                    print(f"{'ID':<4}| {'Name':<20}| {'Products':<8}| {'Description'}")
                    print("-" * 70)
                    
                    for category in categories:
                        print(f"{category['id']:<4}| {category['name']:<20}| {category['product_count']:<8}| {category['description']}")
                
                input("\nPress Enter to continue...")
            
            elif choice == '2':
                name = input("\nCategory Name: ")
                description = input("Description: ")
                
                # Check if category already exists
                existing = self.db.execute_query(
                    "SELECT id FROM categories WHERE name = ?", 
                    (name,)
                )
                
                if existing:
                    print(f"Error: Category '{name}' already exists.")
                else:
                    success = self.db.execute_update(
                        "INSERT INTO categories (name, description) VALUES (?, ?)",
                        (name, description)
                    )
                    
                    if success:
                        print(f"Category '{name}' added successfully.")
                    else:
                        print("Failed to add category.")
                
                input("\nPress Enter to continue...")
            
            elif choice == '3':
                # Code for editing category
                category_id = input("\nEnter category ID to edit: ")
                category = self.db.execute_query(
                    "SELECT * FROM categories WHERE id = ?", 
                    (category_id,)
                )
                
                if not category:
                    print(f"Category with ID {category_id} not found.")
                else:
                    category = category[0]
                    print(f"\nEditing Category: {category['name']}")
                    
                    name = input(f"Name [{category['name']}]: ") or category['name']
                    description = input(f"Description [{category['description']}]: ") or category['description']
                    
                    success = self.db.execute_update(
                        "UPDATE categories SET name = ?, description = ? WHERE id = ?",
                        (name, description, category_id)
                    )
                    
                    if success:
                        print(f"Category updated successfully.")
                    else:
                        print("Failed to update category.")
                
                input("\nPress Enter to continue...")
            
            elif choice == '4':
                # Code for deleting category
                category_id = input("\nEnter category ID to delete: ")
                
                # Check if category has products
                product_count = self.db.execute_query(
                    """
                    SELECT COUNT(*) as count 
                    FROM products p
                    JOIN categories c ON p.category = c.name
                    WHERE c.id = ?
                    """,
                    (category_id,)
                )
                
                if product_count and product_count[0]['count'] > 0:
                    print(f"Error: Cannot delete category with {product_count[0]['count']} products.")
                else:
                    confirm = input("Are you sure you want to delete this category? (y/n): ")
                    
                    if confirm.lower() == 'y':
                        success = self.db.execute_update(
                            "DELETE FROM categories WHERE id = ?",
                            (category_id,)
                        )
                        
                        if success:
                            print("Category deleted successfully.")
                        else:
                            print("Failed to delete category.")
                
                input("\nPress Enter to continue...")
            
            elif choice == '0':
                break
            else:
                print("Invalid option. Please try again.")
