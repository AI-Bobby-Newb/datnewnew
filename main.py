import os
import sys
import pandas as pd
from datetime import datetime
from monthly_sales_analyzer import MonthlySalesAnalyzer

def display_title():
    """Display the program title banner"""
    print("\n" + "=" * 60)
    print("  MONTHLY SALES ANALYZER - VAPE STORE SALES DASHBOARD")
    print("=" * 60)

def main():
    """Main entry point for the monthly sales analyzer"""
    analyzer = MonthlySalesAnalyzer("monthly_sales")
    
    # For command line usage
    if len(sys.argv) > 1:
        test_option = sys.argv[1]
        
        if test_option in ['-h', '--help', 'help']:
            print("\nMONTHLY SALES ANALYZER - COMMAND LINE USAGE")
            print("=" * 60)
            print("python3 main.py [command] [options]")
            print("\nAvailable commands:")
            print("  list              - List all available sales reports")
            print("  top               - Show top 20 products by revenue")
            print("  category          - Show sales breakdown by category")
            print("  monthly           - Show monthly sales analysis")
            print("  search [term]     - Search for products (default: 'mint')")
            print("  help              - Show this help message")
            print("\nExamples:")
            print("  python3 main.py list")
            print("  python3 main.py search strawberry")
            return
        if test_option == "list":
            reports = analyzer.get_available_reports()
            print("\nAvailable Monthly Sales Reports:")
            print("-" * 60)
            
            for i, report_file in enumerate(reports, 1):
                report = analyzer.parse_report(report_file)
                if report:
                    print(f"{i}. {report['month']} {report['year']} - {report_file}")
                else:
                    print(f"{i}. {report_file} (Error: Unable to parse)")
            return
        elif test_option == "top":
            # Show top products
            reports = analyzer.get_available_reports()
            parsed_reports = []
            for report_file in reports:
                report = analyzer.parse_report(report_file)
                if report:
                    parsed_reports.append(report)
            
            if parsed_reports:
                # Combine all data and filter out the "TOTAL" category
                all_data = pd.concat([report['data'] for report in parsed_reports])
                all_data_filtered = all_data[all_data['Category Name'] != 'TOTAL']
                
                # Group by product and calculate totals
                product_sales = all_data_filtered.groupby('Name').agg({
                    'Sold': 'sum',
                    'Net Sales': 'sum'
                }).reset_index()
                
                # Sort by revenue
                top_by_revenue = product_sales.sort_values('Net Sales', ascending=False).head(20)
                
                print("\nTOP 20 PRODUCTS BY REVENUE (ALL REPORTS):")
                for i, (_, row) in enumerate(top_by_revenue.iterrows(), 1):
                    print(f"{i}. {row['Name'][:50]} - ${row['Net Sales']:.2f} ({row['Sold']} units)")
            
            return
        elif test_option == "category":
            # Show category breakdown
            reports = analyzer.get_available_reports()
            parsed_reports = []
            for report_file in reports:
                report = analyzer.parse_report(report_file)
                if report:
                    parsed_reports.append(report)
            
            if parsed_reports:
                # Combine all data and filter out the "TOTAL" category
                all_data = pd.concat([report['data'] for report in parsed_reports])
                all_data_filtered = all_data[all_data['Category Name'] != 'TOTAL']
                total_net_sales = all_data_filtered['Net Sales'].sum()
                
                # Group by category
                category_sales = all_data_filtered.groupby('Category Name').agg({
                    'Sold': 'sum',
                    'Net Sales': 'sum'
                }).sort_values('Net Sales', ascending=False).reset_index()
                
                # Calculate percentages
                category_sales['% of Total'] = (category_sales['Net Sales'] / total_net_sales) * 100
                
                print("\nCATEGORY SALES SUMMARY (ALL REPORTS):")
                print("-" * 60)
                
                for _, row in category_sales.iterrows():
                    print(f"{row['Category Name']:<20} | {row['Sold']:<6} units | ${row['Net Sales']:<10.2f} | {row['% of Total']:<6.2f}%")
            
            return
        elif test_option == "search":
            # Search for products
            search_term = sys.argv[2] if len(sys.argv) > 2 else "mint"
            reports = analyzer.get_available_reports()
            results = []
            
            for report_file in reports:
                report = analyzer.parse_report(report_file)
                if report:
                    df = report['data']
                    # Handle NaN values in the search
                    # Get the matches
                    mask = df['Name'].fillna('').str.lower().str.contains(search_term.lower())
                    if mask.any():
                        # Create a copy to avoid SettingWithCopyWarning
                        matches = df[mask].copy()
                        matches['Report'] = f"{report['month']} {report['year']}"
                        results.append(matches)
            
            if results:
                all_results = pd.concat(results)
                print(f"\nFound {len(all_results)} matches for '{search_term}'")
                print("\nTop 10 matches:")
                
                for i, (_, row) in enumerate(all_results.sort_values('Net Sales', ascending=False).head(10).iterrows(), 1):
                    print(f"{i}. {row['Name']} - {row['Report']} - ${row['Net Sales']:.2f} ({row['Sold']} units)")
            else:
                print(f"No matches found for '{search_term}'")
            
            return
        elif test_option == "monthly":
            # Show monthly sales analysis
            reports = analyzer.get_available_reports()
            parsed_reports = []
            for report_file in reports:
                report = analyzer.parse_report(report_file)
                if report:
                    parsed_reports.append(report)
            
            if len(parsed_reports) < 2:
                print("Not enough valid reports for monthly analysis.")
                return
                
            # Sort reports by date
            month_order = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 
                          'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
            
            def get_sort_key(report):
                month = report['month']
                year = int(report['year'])
                month_num = month_order.get(month[:3], 0)
                return (year, month_num)
            
            sorted_reports = sorted(parsed_reports, key=get_sort_key)
            
            # Calculate monthly totals
            months = []
            total_units = []
            total_sales = []
            
            for report in sorted_reports:
                df = report['data']
                # Filter out the "TOTAL" category to avoid double counting
                df_filtered = df[df['Category Name'] != 'TOTAL']
                
                month_label = f"{report['month']} {report['year']}"
                units = df_filtered['Sold'].sum()
                sales = df_filtered['Net Sales'].sum()
                
                months.append(month_label)
                total_units.append(units)
                total_sales.append(sales)
            
            # Display monthly totals
            print("\nMONTHLY SALES TOTALS:")
            print("=" * 80)
            
            from tabulate import tabulate
            
            data = []
            for i, month in enumerate(months):
                data.append([
                    month,
                    total_units[i],
                    f"${total_sales[i]:.2f}"
                ])
            
            print(tabulate(data, headers=[
                "Month", "Units Sold", "Net Sales"
            ], tablefmt="grid"))
            
            # Calculate and display growth rates if applicable
            if len(sorted_reports) >= 2:
                print("\nMONTH-OVER-MONTH GROWTH RATES:")
                print("=" * 80)
                
                growth_data = []
                for i in range(1, len(sorted_reports)):
                    period = f"{months[i-1]} to {months[i]}"
                    # Units growth
                    if total_units[i-1] > 0:
                        units_growth = ((total_units[i] - total_units[i-1]) / total_units[i-1]) * 100
                        units_growth_str = f"{units_growth:.2f}%"
                    else:
                        units_growth_str = "N/A"
                    
                    # Sales growth
                    if total_sales[i-1] > 0:
                        sales_growth = ((total_sales[i] - total_sales[i-1]) / total_sales[i-1]) * 100
                        sales_growth_str = f"{sales_growth:.2f}%"
                    else:
                        sales_growth_str = "N/A"
                    
                    growth_data.append([period, units_growth_str, sales_growth_str])
                
                print(tabulate(growth_data, headers=[
                    "Period", "Units Growth", "Sales Growth"
                ], tablefmt="grid"))
            
            return
        return
    
    # Normal interactive mode
    while True:
        display_title()
        print("\nMAIN MENU:")
        print("1. Monthly Reports")
        print("2. Product Analysis")
        print("3. Category Analysis")
        print("4. Sales Rankings")
        print("5. Trend Analysis")
        print("6. Export Data")
        print("0. Exit")
        
        choice = input("\nSelect an option: ")
        
        if choice == '1':
            monthly_reports_menu(analyzer)
        elif choice == '2':
            product_analysis_menu(analyzer)
        elif choice == '3':
            category_analysis_menu(analyzer)
        elif choice == '4':
            sales_rankings_menu(analyzer)
        elif choice == '5':
            trend_analysis_menu(analyzer)
        elif choice == '6':
            export_menu(analyzer)
        elif choice == '0':
            print("\nThank you for using the Monthly Sales Analyzer!")
            break
        else:
            print("Invalid option. Please try again.")

def monthly_reports_menu(analyzer):
    """Menu for monthly report options"""
    while True:
        display_title()
        print("\nMONTHLY REPORTS MENU:")
        print("1. View Available Reports")
        print("2. View Full Month Report")
        print("3. Compare Monthly Reports")
        print("4. Monthly Growth Analysis")
        print("0. Back to Main Menu")
        
        choice = input("\nSelect an option: ")
        
        if choice == '1':
            analyzer.list_available_reports()
        elif choice == '2':
            analyzer.view_report_details()
        elif choice == '3':
            analyzer.compare_reports()
        elif choice == '4':
            analyzer.monthly_growth_analysis()
        elif choice == '0':
            break
        else:
            print("Invalid option. Please try again.")

def product_analysis_menu(analyzer):
    """Menu for product analysis options"""
    while True:
        display_title()
        print("\nPRODUCT ANALYSIS MENU:")
        print("1. Search Products")
        print("2. Top Selling Products")
        print("3. Worst Selling Products")
        print("4. Product Performance Over Time")
        print("5. New Products Analysis")
        print("0. Back to Main Menu")
        
        choice = input("\nSelect an option: ")
        
        if choice == '1':
            analyzer.search_products()
        elif choice == '2':
            analyzer.top_selling_products()
        elif choice == '3':
            analyzer.worst_selling_products()
        elif choice == '4':
            analyzer.product_performance_over_time()
        elif choice == '5':
            analyzer.new_products_analysis()
        elif choice == '0':
            break
        else:
            print("Invalid option. Please try again.")

def category_analysis_menu(analyzer):
    """Menu for category analysis options"""
    while True:
        display_title()
        print("\nCATEGORY ANALYSIS MENU:")
        print("1. Sales by Category")
        print("2. Category Growth Analysis")
        print("3. Top Products in Category")
        print("4. Category Comparison")
        print("0. Back to Main Menu")
        
        choice = input("\nSelect an option: ")
        
        if choice == '1':
            analyzer.sales_by_category()
        elif choice == '2':
            analyzer.category_growth_analysis()
        elif choice == '3':
            analyzer.top_products_by_category()
        elif choice == '4':
            analyzer.compare_categories()
        elif choice == '0':
            break
        else:
            print("Invalid option. Please try again.")

def sales_rankings_menu(analyzer):
    """Menu for sales rankings options"""
    while True:
        display_title()
        print("\nSALES RANKINGS MENU:")
        print("1. Top 20 Products by Revenue")
        print("2. Top 20 Products by Units Sold")
        print("3. Products with Zero Sales")
        print("4. High Revenue / Low Unit Products")
        print("5. Low Revenue / High Unit Products")
        print("0. Back to Main Menu")
        
        choice = input("\nSelect an option: ")
        
        if choice == '1':
            analyzer.top_products_by_revenue()
        elif choice == '2':
            analyzer.top_products_by_units()
        elif choice == '3':
            analyzer.zero_sales_products()
        elif choice == '4':
            analyzer.high_revenue_low_unit_products()
        elif choice == '5':
            analyzer.low_revenue_high_unit_products()
        elif choice == '0':
            break
        else:
            print("Invalid option. Please try again.")

def trend_analysis_menu(analyzer):
    """Menu for trend analysis options"""
    while True:
        display_title()
        print("\nTREND ANALYSIS MENU:")
        print("1. Monthly Sales Trends")
        print("2. Category Trends")
        print("3. Seasonal Product Analysis")
        print("4. Growth Rate Analysis")
        print("0. Back to Main Menu")
        
        choice = input("\nSelect an option: ")
        
        if choice == '1':
            analyzer.monthly_sales_trends()
        elif choice == '2':
            analyzer.category_trends()
        elif choice == '3':
            analyzer.seasonal_product_analysis()
        elif choice == '4':
            analyzer.growth_rate_analysis()
        elif choice == '0':
            break
        else:
            print("Invalid option. Please try again.")

def export_menu(analyzer):
    """Menu for export options"""
    while True:
        display_title()
        print("\nEXPORT MENU:")
        print("1. Export Monthly Report Summary")
        print("2. Export Overall Sales Summary")
        print("3. Export Category Summary")
        print("4. Export Product Rankings")
        print("5. Export Custom Report")
        print("0. Back to Main Menu")
        
        choice = input("\nSelect an option: ")
        
        if choice == '1':
            analyzer.export_monthly_report()
        elif choice == '2':
            analyzer.export_summary()
        elif choice == '3':
            analyzer.export_category_summary()
        elif choice == '4':
            analyzer.export_product_rankings()
        elif choice == '5':
            analyzer.export_custom_report()
        elif choice == '0':
            break
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()
