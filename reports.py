import os
from datetime import datetime, timedelta
import csv

class ReportManager:
    \"\"\"Manages report generation for the vape store system\"\"\"
    
    def __init__(self, db):
        \"\"\"Initialize with database connection\"\"\"
        self.db = db
        self.report_dir = \"reports\"
        
        # Ensure reports directory exists
        if not os.path.exists(self.report_dir):
            os.makedirs(self.report_dir)
    
    def generate_menu(self):
        \"\"\"Display reports menu\"\"\"
        while True:
            print(\"\
===== REPORTS =====\")
            print(\"1. Sales Summary\")
            print(\"2. Product Performance\")
            print(\"3. Inventory Valuation\")
            print(\"4. Low Stock Report\")
            print(\"5. Profit Margin Analysis\")
            print(\"6. Custom Date Range Report\")
            print(\"0. Return to Main Menu\")
            
            choice = input(\"\
Select an option: \")
            
            if choice == '1':
                self.sales_summary_report()
            elif choice == '2':
                self.product_performance_report()
            elif choice == '3':
                self.inventory_valuation_report()
            elif choice == '4':
                self.low_stock_report()
            elif choice == '5':
                self.profit_margin_analysis()
            elif choice == '6':
                self.custom_date_range_report()
            elif choice == '0':
                break
            else:
                print(\"Invalid option. Please try again.\")
    
    def sales_summary_report(self):
        \"\"\"Generate sales summary report\"\"\"
        print(\"\
===== SALES SUMMARY REPORT =====\")
        
        # Get time period
        print(\"Time Period:\")
        print(\"1. Today\")
        print(\"2. Yesterday\")
        print(\"3. This Week\")
        print(\"4. This Month\")
        print(\"5. Last Month\")
        print(\"6. Custom Date Range\")
        
        choice = input(\"\
Select a time period: \")
        
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        if choice == '1':  # Today
            start_date = today
            end_date = today + timedelta(days=1)
            period_name = \"Today\"
        elif choice == '2':  # Yesterday
            start_date = today - timedelta(days=1)
            end_date = today
            period_name = \"Yesterday\"
        elif choice == '3':  # This Week
            start_date = today - timedelta(days=today.weekday())
            end_date = today + timedelta(days=1)
            period_name = \"This Week\"
        elif choice == '4':  # This Month
            start_date = today.replace(day=1)
            end_date = today + timedelta(days=1)
            period_name = \"This Month\"
        elif choice == '5':  # Last Month
            last_month = today.month - 1
            last_month_year = today.year
            if last_month == 0:
                last_month = 12
                last_month_year -= 1
            
            start_date = today.replace(year=last_month_year, month=last_month, day=1)
            end_date = today.replace(day=1)
            period_name = \"Last Month\"
        elif choice == '6':  # Custom Date Range
            try:
                start_str = input(\"Start Date (YYYY-MM-DD): \")
                end_str = input(\"End Date (YYYY-MM-DD): \")
                
                start_date = datetime.strptime(start_str, \"%Y-%m-%d\")
                end_date = datetime.strptime(end_str, \"%Y-%m-%d\") + timedelta(days=1)
                
                period_name = f\"{start_str} to {end_str}\"
            except ValueError:
                print(\"Invalid date format. Please use YYYY-MM-DD.\")
                return
        else:
            print(\"Invalid option.\")
            return
        
        # Fetch sales data for the selected period
        sales_data = self.db.execute_query(\"\"\"
            SELECT 
                COUNT(id) as transaction_count,
                SUM(total_amount) as total_sales,
                SUM(total_cost) as total_cost,
                SUM(total_amount - total_cost) as total_profit,
                AVG(total_amount) as average_sale,
                COUNT(DISTINCT customer_id) as unique_customers
            FROM sales
            WHERE timestamp >= ? AND timestamp < ?
        \"\"\", (start_date.strftime(\"%Y-%m-%d %H:%M:%S\"), 
              end_date.strftime(\"%Y-%m-%d %H:%M:%S\")))
        
        if not sales_data or not sales_data[0]['transaction_count']:
            print(f\"No sales data found for {period_name}.\")
            input(\"\
Press Enter to continue...\")
            return
        
        data = sales_data[0]
        
        # Get top selling products
        top_products = self.db.execute_query(\"\"\"
            SELECT 
                p.name,
                SUM(si.quantity) as quantity_sold,
                SUM(si.price * si.quantity) as total_sales
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            JOIN sales s ON si.sale_id = s.id
            WHERE s.timestamp >= ? AND s.timestamp < ?
            GROUP BY p.id
            ORDER BY quantity_sold DESC
            LIMIT 5
        \"\"\", (start_date.strftime(\"%Y-%m-%d %H:%M:%S\"), 
              end_date.strftime(\"%Y-%m-%d %H:%M:%S\")))
        
        # Get sales by category
        category_sales = self.db.execute_query(\"\"\"
            SELECT 
                p.category,
                SUM(si.quantity) as quantity_sold,
                SUM(si.price * si.quantity) as total_sales
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            JOIN sales s ON si.sale_id = s.id
            WHERE s.timestamp >= ? AND s.timestamp < ?
            GROUP BY p.category
            ORDER BY total_sales DESC
        \"\"\", (start_date.strftime(\"%Y-%m-%d %H:%M:%S\"), 
              end_date.strftime(\"%Y-%m-%d %H:%M:%S\")))
        
        # Display report
        print(f\"\
Sales Summary for {period_name}:\")
        print(f\"Total Sales: ${data['total_sales']:.2f}\")
        print(f\"Total Cost: ${data['total_cost']:.2f}\")
        print(f\"Total Profit: ${data['total_profit']:.2f}\")
        print(f\"Profit Margin: {data['total_profit'] / data['total_sales'] * 100:.2f}%\")
        print(f\"Number of Transactions: {data['transaction_count']}\")
        print(f\"Average Sale: ${data['average_sale']:.2f}\")
        print(f\"Unique Customers: {data['unique_customers']}\")
        
        print(\"\
Top Selling Products:\")
        for i, product in enumerate(top_products, 1):
            print(f\"{i}. {product['name']}: {product['quantity_sold']} units (${product['total_sales']:.2f})\")
        
        print(\"\
Sales by Category:\")
        for category in category_sales:
            print(f\"{category['category']}: ${category['total_sales']:.2f} ({category['quantity_sold']} units)\")
        
        # Export to CSV
        export_choice = input(\"\
Export to CSV? (y/n): \")
        if export_choice.lower() == 'y':
            filename = f\"sales_summary_{period_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv\"
            filepath = os.path.join(self.report_dir, filename)
            
            with open(filepath, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([\"Sales Summary Report\", period_name])
                writer.writerow([])
                writer.writerow([\"Total Sales\", f\"${data['total_sales']:.2f}\"])
                writer.writerow([\"Total Cost\", f\"${data['total_cost']:.2f}\"])
                writer.writerow([\"Total Profit\", f\"${data['total_profit']:.2f}\"])
                writer.writerow([\"Profit Margin\", f\"{data['total_profit'] / data['total_sales'] * 100:.2f}%\"])
                writer.writerow([\"Number of Transactions\", data['transaction_count']])
                writer.writerow([\"Average Sale\", f\"${data['average_sale']:.2f}\"])
                writer.writerow([\"Unique Customers\", data['unique_customers']])
                
                writer.writerow([])
                writer.writerow([\"Top Selling Products\"])
                writer.writerow([\"Rank\", \"Product\", \"Quantity Sold\", \"Total Sales\"])
                for i, product in enumerate(top_products, 1):
                    writer.writerow([i, product['name'], product['quantity_sold'], f\"${product['total_sales']:.2f}\"])
                
                writer.writerow([])
                writer.writerow([\"Sales by Category\"])
                writer.writerow([\"Category\", \"Quantity Sold\", \"Total Sales\"])
                for category in category_sales:
                    writer.writerow([category['category'], category['quantity_sold'], f\"${category['total_sales']:.2f}\"])
            
            print(f\"\
Report exported to {filepath}\")
        
        input(\"\
Press Enter to continue...\")
    
    def product_performance_report(self):
        \"\"\"Generate product performance report\"\"\"
        print(\"\
===== PRODUCT PERFORMANCE REPORT =====\")
        
        # Get time period
        print(\"Time Period:\")
        print(\"1. This Month\")
        print(\"2. Last Month\")
        print(\"3. Last 3 Months\")
        print(\"4. Last 6 Months\")
        print(\"5. This Year\")
        print(\"6. Custom Date Range\")
        
        choice = input(\"\
Select a time period: \")
        
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        if choice == '1':  # This Month
            start_date = today.replace(day=1)
            end_date = today + timedelta(days=1)
            period_name = \"This Month\"
        elif choice == '2':  # Last Month
            last_month = today.month - 1
            last_month_year = today.year
            if last_month == 0:
                last_month = 12
                last_month_year -= 1
            
            start_date = today.replace(year=last_month_year, month=last_month, day=1)
            end_date = today.replace(day=1)
            period_name = \"Last Month\"
        elif choice == '3':  # Last 3 Months
            start_date = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
            start_date = (start_date - timedelta(days=1)).replace(day=1)
            end_date = today + timedelta(days=1)
            period_name = \"Last 3 Months\"
        elif choice == '4':  # Last 6 Months
            start_date = today.replace(day=1)
            for _ in range(5):
                start_date = (start_date - timedelta(days=1)).replace(day=1)
            end_date = today + timedelta(days=1)
            period_name = \"Last 6 Months\"
        elif choice == '5':  # This Year
            start_date = today.replace(month=1, day=1)
            end_date = today + timedelta(days=1)
            period_name = \"This Year\"
        elif choice == '6':  # Custom Date Range
            try:
                start_str = input(\"Start Date (YYYY-MM-DD): \")
                end_str = input(\"End Date (YYYY-MM-DD): \")
                
                start_date = datetime.strptime(start_str, \"%Y-%m-%d\")
                end_date = datetime.strptime(end_str, \"%Y-%m-%d\") + timedelta(days=1)
                
                period_name = f\"{start_str} to {end_str}\"
            except ValueError:
                print(\"Invalid date format. Please use YYYY-MM-DD.\")
                return
        else:
            print(\"Invalid option.\")
            return
        
        # Get product performance data
        products = self.db.execute_query(\"\"\"
            SELECT 
                p.id,
                p.sku,
                p.name,
                p.category,
                p.price,
                p.cost,
                SUM(COALESCE(si.quantity, 0)) as quantity_sold,
                SUM(COALESCE(si.price * si.quantity, 0)) as revenue,
                SUM(COALESCE(si.quantity * p.cost, 0)) as cost_of_goods,
                COUNT(DISTINCT s.id) as appearances_in_sales
            FROM products p
            LEFT JOIN sale_items si ON p.id = si.product_id
            LEFT JOIN sales s ON si.sale_id = s.id AND s.timestamp >= ? AND s.timestamp < ?
            GROUP BY p.id
            ORDER BY revenue DESC
        \"\"\", (start_date.strftime(\"%Y-%m-%d %H:%M:%S\"), 
              end_date.strftime(\"%Y-%m-%d %H:%M:%S\")))
        
        if not products:
            print(\"No product data found.\")
            input(\"\
Press Enter to continue...\")
            return
        
        # Display report
        print(f\"\
Product Performance for {period_name}:\")
        print(f\"{'SKU':<10}| {'Name':<30}| {'Category':<15}| {'Units Sold':<10}| {'Revenue':<12}| {'Profit':<12}| {'Margin %':<8}\")
        print(\"-\" * 100)
        
        for product in products:
            if product['revenue'] > 0:
                profit = product['revenue'] - product['cost_of_goods']
                margin = profit / product['revenue'] * 100
            else:
                profit = 0
                margin = 0
            
            print(f\"{product['sku']:<10}| {product['name'][:28]:<30}| {product['category'][:13]:<15}| {product['quantity_sold']:<10}| ${product['revenue']:<10.2f}| ${profit:<10.2f}| {margin:<7.2f}%\")
        
        # Export to CSV
        export_choice = input(\"\
Export to CSV? (y/n): \")
        if export_choice.lower() == 'y':
            filename = f\"product_performance_{period_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv\"
            filepath = os.path.join(self.report_dir, filename)
            
            with open(filepath, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([\"Product Performance Report\", period_name])
                writer.writerow([])
                writer.writerow([\"SKU\", \"Name\", \"Category\", \"Units Sold\", \"Revenue\", \"Cost\", \"Profit\", \"Margin %\"])
                
                for product in products:
                    if product['revenue'] > 0:
                        profit = product['revenue'] - product['cost_of_goods']
                        margin = profit / product['revenue'] * 100
                    else:
                        profit = 0
                        margin = 0
                    
                    writer.writerow([
                        product['sku'],
                        product['name'],
                        product['category'],
                        product['quantity_sold'],
                        f\"${product['revenue']:.2f}\",
                        f\"${product['cost_of_goods']:.2f}\",
                        f\"${profit:.2f}\",
                        f\"{margin:.2f}%\"
                    ])
            
            print(f\"\
Report exported to {filepath}\")
        
        input(\"\
Press Enter to continue...\")
    
    def inventory_valuation_report(self):
        \"\"\"Generate inventory valuation report\"\"\"
        print(\"\
===== INVENTORY VALUATION REPORT =====\")
        
        # Get inventory data
        inventory = self.db.execute_query(\"\"\"
            SELECT 
                p.id,
                p.sku,
                p.name,
                p.category,
                p.quantity,
                p.cost,
                p.price,
                p.quantity * p.cost as inventory_value,
                p.quantity * p.price as retail_value
            FROM products p
            ORDER BY inventory_value DESC
        \"\"\")
        
        if not inventory:
            print(\"No inventory data found.\")
            input(\"\
Press Enter to continue...\")
            return
        
        # Calculate totals
        total_items = sum(item['quantity'] for item in inventory)
        total_cost = sum(item['inventory_value'] for item in inventory)
        total_retail = sum(item['retail_value'] for item in inventory)
        potential_profit = total_retail - total_cost
        
        # Group by category
        categories = {}
        for item in inventory:
            cat = item['category']
            if cat not in categories:
                categories[cat] = {
                    'items': 0,
                    'cost': 0,
                    'retail': 0
                }
            
            categories[cat]['items'] += item['quantity']
            categories[cat]['cost'] += item['inventory_value']
            categories[cat]['retail'] += item['retail_value']
        
        # Display report
        print(f\"\
Inventory Valuation as of {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:\")
        print(f\"Total Inventory Items: {total_items}\")
        print(f\"Total Inventory Cost: ${total_cost:.2f}\")
        print(f\"Total Retail Value: ${total_retail:.2f}\")
        print(f\"Potential Profit: ${potential_profit:.2f}\")
        print(f\"Average Markup: {(total_retail / total_cost - 1) * 100:.2f}%\")
        
        print(\"\
Valuation by Category:\")
        print(f\"{'Category':<20}| {'Items':<8}| {'Cost Value':<15}| {'Retail Value':<15}| {'% of Total':<10}\")
        print(\"-\" * 75)
        
        for cat, data in sorted(categories.items(), key=lambda x: x[1]['cost'], reverse=True):
            pct_of_total = data['cost'] / total_cost * 100
            print(f\"{cat[:18]:<20}| {data['items']:<8}| ${data['cost']:<13.2f}| ${data['retail']:<13.2f}| {pct_of_total:<9.2f}%\")
        
        # Display top 10 most valuable items
        print(\"\
Top 10 Most Valuable Items (by Cost):\")
        print(f\"{'SKU':<10}| {'Name':<30}| {'Quantity':<8}| {'Cost Value':<12}| {'Retail Value':<12}\")
        print(\"-\" * 80)
        
        for item in sorted(inventory, key=lambda x: x['inventory_value'], reverse=True)[:10]:
            print(f\"{item['sku']:<10}| {item['name'][:28]:<30}| {item['quantity']:<8}| ${item['inventory_value']:<10.2f}| ${item['retail_value']:<10.2f}\")
        
        # Export to CSV
        export_choice = input(\"\
Export to CSV? (y/n): \")
        if export_choice.lower() == 'y':
            filename = f\"inventory_valuation_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv\"
            filepath = os.path.join(self.report_dir, filename)
            
            with open(filepath, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([\"Inventory Valuation Report\", datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                writer.writerow([])
                writer.writerow([\"Total Items\", total_items])
                writer.writerow([\"Total Cost Value\", f\"${total_cost:.2f}\"])
                writer.writerow([\"Total Retail Value\", f\"${total_retail:.2f}\"])
                writer.writerow([\"Potential Profit\", f\"${potential_profit:.2f}\"])
                writer.writerow([\"Average Markup\", f\"{(total_retail / total_cost - 1) * 100:.2f}%\"])
                
                writer.writerow([])
                writer.writerow([\"Valuation by Category\"])
                writer.writerow([\"Category\", \"Items\", \"Cost Value\", \"Retail Value\", \"% of Total\"])
                
                for cat, data in sorted(categories.items(), key=lambda x: x[1]['cost'], reverse=True):
                    pct_of_total = data['cost'] / total_cost * 100
                    writer.writerow([
                        cat,
                        data['items'],
                        f\"${data['cost']:.2f}\",
                        f\"${data['retail']:.2f}\",
                        f\"{pct_of_total:.2f}%\"
                    ])
                
                writer.writerow([])
                writer.writerow([\"Complete Inventory\"])
                writer.writerow([\"SKU\", \"Name\", \"Category\", \"Quantity\", \"Unit Cost\", \"Unit Price\", \"Cost Value\", \"Retail Value\"])
                
                for item in inventory:
                    writer.writerow([
                        item['sku'],
                        item['name'],
                        item['category'],
                        item['quantity'],
                        f\"${item['cost']:.2f}\",
                        f\"${item['price']:.2f}\",
                        f\"${item['inventory_value']:.2f}\",
                        f\"${item['retail_value']:.2f}\"
                    ])
            
            print(f\"\
Report exported to {filepath}\")
        
        input(\"\
Press Enter to continue...\")
    
    def low_stock_report(self):
        \"\"\"Generate low stock report\"\"\"
        print(\"\
===== LOW STOCK REPORT =====\")
        
        # Get low stock items
        low_stock = self.db.execute_query(\"\"\"
            SELECT 
                p.id,
                p.sku,
                p.name,
                p.category,
                p.quantity,
                p.min_stock,
                p.price,
                p.cost,
                (p.min_stock - p.quantity) as units_needed
            FROM products p
            WHERE p.quantity <= p.min_stock
            ORDER BY (p.quantity * 1.0 / p.min_stock), p.name
        \"\"\")
        
        if not low_stock:
            print(\"No products are below minimum stock levels.\")
            input(\"\
Press Enter to continue...\")
            return
        
        # Calculate restock value
        total_restock_cost = sum((item['min_stock'] - item['quantity']) * item['cost'] for item in low_stock if item['quantity'] < item['min_stock'])
        
        # Group by severity
        critical = []
        low = []
        warning = []
        
        for item in low_stock:
            if item['quantity'] == 0:
                critical.append(item)
            elif item['quantity'] <= item['min_stock'] * 0.25:
                critical.append(item)
            elif item['quantity'] <= item['min_stock'] * 0.5:
                low.append(item)
            else:
                warning.append(item)
        
        # Display report
        print(f\"\
Low Stock Report as of {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:\")
        print(f\"Total Products Below Minimum Stock: {len(low_stock)}\")
        print(f\"Products Out of Stock: {len([i for i in low_stock if i['quantity'] == 0])}\")
        print(f\"Estimated Restock Cost: ${total_restock_cost:.2f}\")
        
        print(\"\
CRITICAL (0-25% of minimum):\")
        if critical:
            print(f\"{'SKU':<10}| {'Name':<30}| {'Current':<7}| {'Minimum':<7}| {'Needed':<6}| {'Status':<10}\")
            print(\"-\" * 80)
            
            for item in critical:
                status = \"OUT\" if item['quantity'] == 0 else \"CRITICAL\"
                print(f\"{item['sku']:<10}| {item['name'][:28]:<30}| {item['quantity']:<7}| {item['min_stock']:<7}| {item['units_needed']:<6}| {status:<10}\")
        else:
            print(\"None\")
        
        print(\"\
LOW (26-50% of minimum):\")
        if low:
            print(f\"{'SKU':<10}| {'Name':<30}| {'Current':<7}| {'Minimum':<7}| {'Needed':<6}| {'Status':<10}\")
            print(\"-\" * 80)
            
            for item in low:
                print(f\"{item['sku']:<10}| {item['name'][:28]:<30}| {item['quantity']:<7}| {item['min_stock']:<7}| {item['units_needed']:<6}| {'LOW':<10}\")
        else:
            print(\"None\")
        
        print(\"\
WARNING (51-100% of minimum):\")
        if warning:
            print(f\"{'SKU':<10}| {'Name':<30}| {'Current':<7}| {'Minimum':<7}| {'Needed':<6}| {'Status':<10}\")
            print(\"-\" * 80)
            
            for item in warning:
                print(f\"{item['sku']:<10}| {item['name'][:28]:<30}| {item['quantity']:<7}| {item['min_stock']:<7}| {item['units_needed']:<6}| {'WARNING':<10}\")
        else:
            print(\"None\")
        
        # Export to CSV
        export_choice = input(\"\
Export to CSV? (y/n): \")
        if export_choice.lower() == 'y':
            filename = f\"low_stock_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv\"
            filepath = os.path.join(self.report_dir, filename)
            
            with open(filepath, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([\"Low Stock Report\", datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                writer.writerow([])
                writer.writerow([\"Total Products Below Minimum Stock\", len(low_stock)])
                writer.writerow([\"Products Out of Stock\", len([i for i in low_stock if i['quantity'] == 0])])
                writer.writerow([\"Estimated Restock Cost\", f\"${total_restock_cost:.2f}\"])
                
                writer.writerow([])
                writer.writerow([\"Product List\"])
                writer.writerow([\"SKU\", \"Name\", \"Category\", \"Current Stock\", \"Minimum Stock\", \"Units Needed\", \"Status\", \"Unit Cost\", \"Restock Cost\"])
                
                for item in low_stock:
                    if item['quantity'] == 0:
                        status = \"OUT OF STOCK\"
                    elif item['quantity'] <= item['min_stock'] * 0.25:
                        status = \"CRITICAL\"
                    elif item['quantity'] <= item['min_stock'] * 0.5:
                        status = \"LOW\"
                    else:
                        status = \"WARNING\"
                    
                    writer.writerow([
                        item['sku'],
                        item['name'],
                        item['category'],
                        item['quantity'],
                        item['min_stock'],
                        item['units_needed'],
                        status,
                        f\"${item['cost']:.2f}\",
                        f\"${item['units_needed'] * item['cost']:.2f}\"
                    ])
            
            print(f\"\
Report exported to {filepath}\")
        
        input(\"\
Press Enter to continue...\")
    
    def profit_margin_analysis(self):
        \"\"\"Generate profit margin analysis report\"\"\"
        print(\"\
===== PROFIT MARGIN ANALYSIS =====\")
        
        # Get product margin data
        products = self.db.execute_query(\"\"\"
            SELECT 
                p.id,
                p.sku,
                p.name,
                p.category,
                p.price,
                p.cost,
                p.price - p.cost as margin,
                (p.price - p.cost) / p.price * 100 as margin_percent
            FROM products p
            ORDER BY margin_percent DESC
        \"\"\")
        
        if not products:
            print(\"No product data found.\")
            input(\"\
Press Enter to continue...\")
            return
        
        # Calculate statistics
        avg_margin = sum(p['margin_percent'] for p in products) / len(products)
        
        # Group by category
        categories = {}
        for item in products:
            cat = item['category']
            if cat not in categories:
                categories[cat] = {
                    'count': 0,
                    'total_margin': 0,
                    'lowest': 100,
                    'highest': 0
                }
            
            categories[cat]['count'] += 1
            categories[cat]['total_margin'] += item['margin_percent']
            categories[cat]['lowest'] = min(categories[cat]['lowest'], item['margin_percent'])
            categories[cat]['highest'] = max(categories[cat]['highest'], item['margin_percent'])
        
        for cat in categories:
            categories[cat]['avg_margin'] = categories[cat]['total_margin'] / categories[cat]['count']
        
        # Display report
        print(f\"\
Profit Margin Analysis as of {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:\")
        print(f\"Average Profit Margin: {avg_margin:.2f}%\")
        print(f\"Highest Margin: {max(p['margin_percent'] for p in products):.2f}%\")
        print(f\"Lowest Margin: {min(p['margin_percent'] for p in products):.2f}%\")
        
        print(\"\
Margin by Category:\")
        print(f\"{'Category':<20}| {'Products':<8}| {'Avg Margin':<12}| {'Lowest':<10}| {'Highest':<10}\")
        print(\"-\" * 70)
        
        for cat, data in sorted(categories.items(), key=lambda x: x[1]['avg_margin'], reverse=True):
            print(f\"{cat[:18]:<20}| {data['count']:<8}| {data['avg_margin']:<11.2f}%| {data['lowest']:<9.2f}%| {data['highest']:<9.2f}%\")
        
        # Display products with high margins
        print(\"\
Top 10 Highest Margin Products:\")
        print(f\"{'SKU':<10}| {'Name':<30}| {'Cost':<8}| {'Price':<8}| {'Margin':<8}| {'Margin %':<8}\")
        print(\"-\" * 80)
        
        for item in sorted(products, key=lambda x: x['margin_percent'], reverse=True)[:10]:
            print(f\"{item['sku']:<10}| {item['name'][:28]:<30}| ${item['cost']:<7.2f}| ${item['price']:<7.2f}| ${item['margin']:<7.2f}| {item['margin_percent']:<7`
}