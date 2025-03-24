import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
from monthly_sales_analyzer import MonthlySalesAnalyzer

# Page configuration
st.set_page_config(
    page_title="Vape Store Sales Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize analyzer
@st.cache_resource
def get_analyzer():
    return MonthlySalesAnalyzer("reports")

analyzer = get_analyzer()

# Get reports data
@st.cache_data
def get_reports():
    reports = []
    for report_file in analyzer.get_available_reports():
        report = analyzer.parse_report(report_file)
        if report:
            reports.append(report)
    # Note: We're relying on the chronological ordering from analyzer.get_available_reports()
    # But still sorting here to ensure consistency
    return sorted(reports, key=lambda x: (x['year'], {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 
                                                     'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8, 
                                                     'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}.get(x['month'], 0)))

reports = get_reports()

# Create combined dataframe with all sales data
@st.cache_data
def get_combined_data(reports):
    all_dfs = []
    
    # Create month order mapping for sorting
    month_order = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
                   'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}
    
    for report in reports:
        df = report['data'].copy()
        # Filter out TOTAL category
        df = df[df['Category Name'] != 'TOTAL']
        
        # Set month display format
        df['Month'] = f"{report['month']} {report['year']}"
        
        # Create sort key in YYYY-MM format for proper chronological sorting
        month_num = month_order.get(report['month'], '00')
        df['MonthSort'] = f"{report['year']}-{month_num}"
        
        # Store the numeric month value for additional sorting if needed
        df['MonthIndex'] = int(month_num)
        df['Year'] = int(report['year'])
        
        all_dfs.append(df)
    
    if all_dfs:
        return pd.concat(all_dfs)
    return pd.DataFrame()

combined_df = get_combined_data(reports)

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select Page", [
    "Dashboard Overview", 
    "Monthly Analysis", 
    "Product Analysis", 
    "Category Analysis",
    "Top Products"
])

# Time filter in sidebar
st.sidebar.title("Time Filter")

# Define a function to sort months chronologically
def get_month_year_key(month_year_str):
    # Create a map of months to their numeric values
    month_num = {
        'January': '01', 'February': '02', 'March': '03', 'April': '04', 'May': '05', 'June': '06',
        'July': '07', 'August': '08', 'September': '09', 'October': '10', 'November': '11', 'December': '12',
        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
        'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
    }
    
    parts = month_year_str.split()
    if len(parts) == 2:
        month, year = parts
        month_val = month_num.get(month, '00')
        return f"{year}-{month_val}"
    return ""

# Get and sort months chronologically
if not combined_df.empty and 'Month' in combined_df.columns:
    # Get all unique months
    all_months = combined_df['Month'].unique().tolist()
    # Sort them chronologically using our custom function
    months = sorted(all_months, key=get_month_year_key)
else:
    months = []  # Set to empty list if no data or no Month column

# Add a historical timeline display
st.sidebar.markdown("### Historical Timeline")

if not months:
    st.sidebar.warning("No reports found or data loading error. Check the monthly_sales directory.")
else:
    st.sidebar.markdown("Available Reports:")
    
    # Group months by year for better organization
def group_months_by_year(months_list):
    years_dict = {}
    for month in months_list:
        parts = month.split()
        month_name = parts[0]
        year = parts[1]
        if year not in years_dict:
            years_dict[year] = []
        years_dict[year].append(month_name)
    return years_dict

# Display months organized by year
if months:  # Only process if we have data
    years_dict = group_months_by_year(months)
    for year in sorted(years_dict.keys(), reverse=True):  # Newest years first
        month_names = years_dict[year]
        # Sort months within the year
        month_order = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                      'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
        sorted_months = sorted(month_names, key=lambda m: month_order.get(m, 0))
        month_list = ", ".join(sorted_months)
        st.sidebar.markdown(f"**{year}**: {month_list}")

# Create select all/none options
st.sidebar.markdown("### Filter Options")
all_option = st.sidebar.checkbox("Select All Months", True)

if all_option:
    selected_months = months
else:
    selected_months = st.sidebar.multiselect("Select Specific Months", months)

# Filter data based on selections
filtered_df = combined_df[combined_df['Month'].isin(selected_months)]

# Date range
min_date = filtered_df['MonthSort'].min() if not filtered_df.empty else ""
max_date = filtered_df['MonthSort'].max() if not filtered_df.empty else ""
date_range = f"{min_date} to {max_date}" if min_date and max_date else "All Time"

#---------------------------
# DASHBOARD OVERVIEW PAGE
#---------------------------
if page == "Dashboard Overview":
    st.title("Vape Store Sales Dashboard")
    st.subheader(f"Sales Overview - {date_range}")
    
    # Summary metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    total_sales = filtered_df['Net Sales'].sum()
    total_units = filtered_df['Sold'].sum()
    avg_price = total_sales / total_units if total_units > 0 else 0
    unique_products = filtered_df['Name'].nunique()
    
    col1.metric("Total Sales", f"${total_sales:,.2f}")
    col2.metric("Units Sold", f"{total_units:,}")
    col3.metric("Average Price", f"${avg_price:.2f}")
    col4.metric("Unique Products", f"{unique_products:,}")
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Monthly Sales Trend")
        # First get the total sales by month
        monthly_sales = filtered_df.groupby('Month').agg({
            'Net Sales': 'sum'
        }).reset_index()
        
        # For bar chart display, manually sort by year and month
        # Create a map of months to their numeric values
        month_num = {
            'January': '01', 'February': '02', 'March': '03', 'April': '04', 'May': '05', 'June': '06',
            'July': '07', 'August': '08', 'September': '09', 'October': '10', 'November': '11', 'December': '12',
            'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
            'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
        }
        
        # Sort based on year and month
        # First create a sort key for each month
        def get_month_year_key(month_year_str):
            parts = month_year_str.split()
            if len(parts) == 2:
                month, year = parts
                month_val = month_num.get(month, '00')
                return f"{year}-{month_val}"
            return ""
            
        # Sort the months manually for display
        correct_month_order = sorted(monthly_sales['Month'].unique().tolist(), key=get_month_year_key)
        
        fig = px.bar(
            monthly_sales, 
            x='Month', 
            y='Net Sales',
            title="Monthly Sales",
            labels={'Net Sales': 'Net Sales ($)', 'Month': ''},
            color_discrete_sequence=['#1f77b4'],
            text_auto='.2s',
            category_orders={'Month': correct_month_order}
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Top Categories")
        category_sales = filtered_df.groupby('Category Name')['Net Sales'].sum().reset_index()
        category_sales = category_sales.sort_values('Net Sales', ascending=False).head(5)
        
        fig = px.pie(
            category_sales, 
            values='Net Sales', 
            names='Category Name',
            title="Sales by Category",
            hole=0.4
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Bottom row charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top 10 Products by Revenue")
        top_products = filtered_df.groupby('Name')['Net Sales'].sum().reset_index()
        top_products = top_products.sort_values('Net Sales', ascending=False).head(10)
        
        fig = px.bar(
            top_products,
            x='Net Sales',
            y='Name',
            orientation='h',
            title="Top 10 Products by Revenue",
            labels={'Net Sales': 'Net Sales ($)', 'Name': ''},
            text_auto='.2s'
        )
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Top 10 Products by Units Sold")
        top_units = filtered_df.groupby('Name')['Sold'].sum().reset_index()
        top_units = top_units.sort_values('Sold', ascending=False).head(10)
        
        fig = px.bar(
            top_units,
            x='Sold',
            y='Name',
            orientation='h',
            title="Top 10 Products by Units Sold",
            labels={'Sold': 'Units Sold', 'Name': ''},
            text_auto='.2s',
            color_discrete_sequence=['#2ca02c']
        )
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)

#---------------------------
# MONTHLY ANALYSIS PAGE
#---------------------------
elif page == "Monthly Analysis":
    st.title("Monthly Sales Analysis")
    st.subheader(f"Analysis Period: {date_range}")
    
    # Monthly comparison
    monthly_data = filtered_df.groupby('Month').agg({
        'Net Sales': 'sum',
        'Sold': 'sum'
    }).reset_index()
    
    # Sort by our custom function for chronological ordering
    monthly_data['SortKey'] = monthly_data['Month'].apply(get_month_year_key)
    monthly_data = monthly_data.sort_values('SortKey', ascending=True)
    
    # Calculate month-over-month growth
    if len(monthly_data) > 1:
        monthly_data['Sales Growth'] = monthly_data['Net Sales'].pct_change() * 100
        monthly_data['Units Growth'] = monthly_data['Sold'].pct_change() * 100
    
    # Two column layout for charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Net Sales by Month")
        # Get the months in correct chronological order
        month_order = monthly_data['Month'].tolist()
        
        fig = px.line(
            monthly_data,
            x='Month',
            y='Net Sales',
            markers=True,
            title="Monthly Sales Trend",
            labels={'Net Sales': 'Net Sales ($)', 'Month': ''},
            category_orders={'Month': month_order}
        )
        # Add data points labels
        fig.update_traces(texttemplate='$%{y:.2f}', textposition='top center')
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Units Sold by Month")
        # Get the months in correct chronological order
        month_order = monthly_data['Month'].tolist()
        
        fig = px.line(
            monthly_data,
            x='Month',
            y='Sold',
            markers=True,
            title="Monthly Units Sold",
            labels={'Sold': 'Units Sold', 'Month': ''},
            color_discrete_sequence=['#2ca02c'],
            category_orders={'Month': month_order}
        )
        # Add data points labels
        fig.update_traces(texttemplate='%{y}', textposition='top center')
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    
    # Growth rate chart if enough data
    if len(monthly_data) > 1 and 'Sales Growth' in monthly_data.columns:
        st.subheader("Month-over-Month Growth")
        growth_df = monthly_data.copy()
        growth_df = growth_df.dropna(subset=['Sales Growth'])
        
        fig = go.Figure()
        # Sort by chronological order
        growth_df['SortKey'] = growth_df['Month'].apply(get_month_year_key)
        growth_df = growth_df.sort_values('SortKey', ascending=True)
        
        # Get the correct month order for the chart
        month_order = sorted(growth_df['Month'].unique().tolist(), key=get_month_year_key)
        
        fig.add_trace(go.Bar(
            x=growth_df['Month'],
            y=growth_df['Sales Growth'],
            name='Sales Growth %',
            marker_color=['red' if x < 0 else 'green' for x in growth_df['Sales Growth']]
        ))
        
        # Set the category order
        fig.update_layout(xaxis={'categoryorder': 'array', 'categoryarray': month_order})
        
        fig.update_layout(
            title="Month-over-Month Sales Growth (%)",
            xaxis_title="",
            yaxis_title="Growth %",
            xaxis_tickangle=-45
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Monthly performance table
    st.subheader("Monthly Performance")
    display_df = monthly_data.copy()
    
    # Format columns for display
    display_df['Net Sales'] = display_df['Net Sales'].apply(lambda x: f"${x:,.2f}")
    display_df['Sold'] = display_df['Sold'].apply(lambda x: f"{x:,}")
    
    if 'Sales Growth' in display_df.columns:
        display_df['Sales Growth'] = display_df['Sales Growth'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A")
    
    st.dataframe(display_df, use_container_width=True)

#---------------------------
# PRODUCT ANALYSIS PAGE
#---------------------------
elif page == "Product Analysis":
    st.title("Product Performance Analysis")
    st.subheader(f"Analysis Period: {date_range}")
    
    # Filter options for products
    col1, col2 = st.columns(2)
    with col1:
        # Get unique categories
        categories = sorted(filtered_df['Category Name'].unique().tolist())
        selected_category = st.selectbox("Filter by Category", ["All Categories"] + categories)
    
    # Apply category filter
    if selected_category != "All Categories":
        product_df = filtered_df[filtered_df['Category Name'] == selected_category]
    else:
        product_df = filtered_df
    
    # Product search box
    search_term = st.text_input("Search Products", "")
    
    if search_term:
        product_df = product_df[product_df['Name'].str.contains(search_term, case=False, na=False)]
    
    # Product performance metrics
    st.subheader("Product Performance")
    
    # Group by product
    product_perf = product_df.groupby('Name').agg({
        'Net Sales': 'sum',
        'Sold': 'sum',
        'Category Name': 'first'  # Get the first category for each product
    }).reset_index()
    
    # Calculate average price
    product_perf['Avg Price'] = product_perf['Net Sales'] / product_perf['Sold']
    
    # Sort by revenue (default)
    product_perf = product_perf.sort_values('Net Sales', ascending=False)
    
    # Top 10 products visualization
    top_products = product_perf.head(10)
    
    if not top_products.empty:
        # Bar chart for top products
        fig = px.bar(
            top_products,
            x='Name',
            y='Net Sales',
            color='Category Name',
            title=f"Top 10 Products by Revenue {f'in {selected_category}' if selected_category != 'All Categories' else ''}",
            labels={'Net Sales': 'Net Sales ($)', 'Name': '', 'Category Name': 'Category'},
            text_auto='.2s'
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
        
        # Scatter plot showing units sold vs revenue
        st.subheader("Units Sold vs Revenue")
        scatter_df = product_perf[product_perf['Sold'] > 0].copy()  # Exclude products with 0 sales
        
        if not scatter_df.empty:
            fig = px.scatter(
                scatter_df,
                x='Sold',
                y='Net Sales',
                color='Category Name',
                size='Avg Price',
                hover_name='Name',
                title="Product Performance Map",
                labels={
                    'Net Sales': 'Net Sales ($)',
                    'Sold': 'Units Sold',
                    'Category Name': 'Category',
                    'Avg Price': 'Avg Price ($)'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Display product table
    st.subheader("Product Details")
    
    # Format the data for display
    display_df = product_perf.copy()
    display_df['Net Sales'] = display_df['Net Sales'].apply(lambda x: f"${x:,.2f}")
    display_df['Avg Price'] = display_df['Avg Price'].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "N/A")
    
    st.dataframe(display_df, use_container_width=True)

#---------------------------
# CATEGORY ANALYSIS PAGE
#---------------------------
elif page == "Category Analysis":
    st.title("Category Analysis")
    st.subheader(f"Analysis Period: {date_range}")
    
    # Calculate category metrics
    category_data = filtered_df.groupby('Category Name').agg({
        'Net Sales': 'sum',
        'Sold': 'sum',
        'Name': pd.Series.nunique  # Count unique products in each category
    }).reset_index()
    
    # Calculate percentage of total sales
    total_sales = category_data['Net Sales'].sum()
    category_data['Percent of Sales'] = (category_data['Net Sales'] / total_sales * 100)
    
    # Calculate average price per unit
    category_data['Avg Price'] = category_data['Net Sales'] / category_data['Sold']
    
    # Sort by revenue
    category_data = category_data.sort_values('Net Sales', ascending=False)
    
    # Rename Name column to Products
    category_data = category_data.rename(columns={'Name': 'Products'})
    
    # Two column layout for charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Category Sales Distribution")
        fig = px.pie(
            category_data, 
            values='Net Sales',
            names='Category Name',
            title="Sales by Category",
            hole=0.4
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Top Categories by Revenue")
        top_categories = category_data.head(10)
        
        fig = px.bar(
            top_categories,
            x='Category Name',
            y='Net Sales',
            color='Category Name',
            title="Revenue by Category",
            labels={'Net Sales': 'Net Sales ($)', 'Category Name': ''},
            text_auto='.2s'
        )
        fig.update_layout(xaxis_tickangle=-45, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    # Category metrics over time
    st.subheader("Category Performance Over Time")
    
    # Get top 5 categories by sales
    top_categories = category_data.head(5)['Category Name'].tolist()
    selected_categories = st.multiselect(
        "Select Categories to Compare",
        options=category_data['Category Name'].tolist(),
        default=top_categories
    )
    
    if selected_categories:
        # Filter data for selected categories and group by month
        cat_time_data = filtered_df[filtered_df['Category Name'].isin(selected_categories)]
        cat_trend = cat_time_data.groupby(['Month', 'Category Name']).agg({
            'Net Sales': 'sum'
        }).reset_index()
        
        # Category performance over time with chronological ordering
        cat_trend = cat_time_data.groupby(['Month', 'Category Name']).agg({
            'Net Sales': 'sum'
        }).reset_index()
        
        # Sort by our chronological month order
        cat_trend['SortKey'] = cat_trend['Month'].apply(get_month_year_key)
        cat_trend = cat_trend.sort_values('SortKey', ascending=True)
        
        # Get the correct month order for the chart
        month_order = sorted(cat_trend['Month'].unique().tolist(), key=get_month_year_key)
        
        fig = px.line(
            cat_trend,
            x='Month',
            y='Net Sales',
            color='Category Name',
            markers=True,
            title="Category Sales Trends Over Time",
            labels={'Net Sales': 'Net Sales ($)', 'Month': ''},
            category_orders={'Month': month_order}
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    
    # Display category table
    st.subheader("Category Details")
    
    # Format the data for display
    display_df = category_data.copy()
    display_df['Net Sales'] = display_df['Net Sales'].apply(lambda x: f"${x:,.2f}")
    display_df['Avg Price'] = display_df['Avg Price'].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "N/A")
    display_df['Percent of Sales'] = display_df['Percent of Sales'].apply(lambda x: f"{x:.2f}%")
    
    st.dataframe(display_df, use_container_width=True)

#---------------------------
# TOP PRODUCTS PAGE
#---------------------------
elif page == "Top Products":
    st.title("Top Products Analysis")
    st.subheader(f"Analysis Period: {date_range}")
    
    # Tab layout for different rankings
    tab1, tab2, tab3 = st.tabs(["By Revenue", "By Units Sold", "By Profit Margin"])
    
    # Get product metrics
    product_data = filtered_df.groupby(['Name', 'Category Name']).agg({
        'Net Sales': 'sum',
        'Sold': 'sum'
    }).reset_index()
    
    # Calculate average price
    product_data['Avg Price'] = product_data['Net Sales'] / product_data['Sold']
    
    with tab1:
        st.subheader("Top Products by Revenue")
        
        # Number of products to show
        top_n = st.slider("Number of products to display", 5, 50, 20, key="revenue_slider")
        
        # Get top products by revenue
        top_by_rev = product_data.sort_values('Net Sales', ascending=False).head(top_n)
        
        # Bar chart for top products
        fig = px.bar(
            top_by_rev,
            y='Name',
            x='Net Sales',
            color='Category Name',
            orientation='h',
            title=f"Top {top_n} Products by Revenue",
            labels={'Net Sales': 'Net Sales ($)', 'Name': '', 'Category Name': 'Category'},
            text_auto='.2s'
        )
        fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=600)
        st.plotly_chart(fig, use_container_width=True)
        
        # Display table with top products
        display_df = top_by_rev.copy()
        display_df['Net Sales'] = display_df['Net Sales'].apply(lambda x: f"${x:,.2f}")
        display_df['Avg Price'] = display_df['Avg Price'].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "N/A")
        
        st.dataframe(display_df, use_container_width=True)
    
    with tab2:
        st.subheader("Top Products by Units Sold")
        
        # Number of products to show
        top_n = st.slider("Number of products to display", 5, 50, 20, key="units_slider")
        
        # Get top products by units sold
        top_by_units = product_data.sort_values('Sold', ascending=False).head(top_n)
        
        # Bar chart for top products
        fig = px.bar(
            top_by_units,
            y='Name',
            x='Sold',
            color='Category Name',
            orientation='h',
            title=f"Top {top_n} Products by Units Sold",
            labels={'Sold': 'Units Sold', 'Name': '', 'Category Name': 'Category'},
            text_auto='.2s'
        )
        fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=600)
        st.plotly_chart(fig, use_container_width=True)
        
        # Display table with top products
        display_df = top_by_units.copy()
        display_df['Net Sales'] = display_df['Net Sales'].apply(lambda x: f"${x:,.2f}")
        display_df['Avg Price'] = display_df['Avg Price'].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "N/A")
        
        st.dataframe(display_df, use_container_width=True)
    
    with tab3:
        st.subheader("Top Products by Average Price")
        
        # Number of products to show
        top_n = st.slider("Number of products to display", 5, 50, 20, key="margin_slider")
        
        # Minimum units sold filter to avoid outliers
        min_units = st.slider("Minimum units sold", 1, 50, 5)
        
        # Filter products with enough units sold and sort by average price
        top_by_margin = product_data[product_data['Sold'] >= min_units].sort_values('Avg Price', ascending=False).head(top_n)
        
        # Bar chart for top products
        fig = px.bar(
            top_by_margin,
            y='Name',
            x='Avg Price',
            color='Category Name',
            orientation='h',
            title=f"Top {top_n} Products by Average Price (min {min_units} units sold)",
            labels={'Avg Price': 'Average Price ($)', 'Name': '', 'Category Name': 'Category'},
            text_auto='.2s'
        )
        fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=600)
        st.plotly_chart(fig, use_container_width=True)
        
        # Display table with top products
        display_df = top_by_margin.copy()
        display_df['Net Sales'] = display_df['Net Sales'].apply(lambda x: f"${x:,.2f}")
        display_df['Avg Price'] = display_df['Avg Price'].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "N/A")
        
        st.dataframe(display_df, use_container_width=True)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.info(
    """
    This dashboard visualizes vape store monthly sales data.
    Data is read from CSV files in the reports directory.
    """
)