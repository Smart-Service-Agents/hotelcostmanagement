import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
from datetime import datetime
import calendar
import warnings
warnings.filterwarnings('ignore')

class CostManagementDB:
    def __init__(self):
        self.db_name = 'cost_management.db'
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_name, check_same_thread=False)

    def init_db(self):
        conn = self.get_connection()
        c = conn.cursor()

        # Receipts Table
        c.execute("""
            CREATE TABLE IF NOT EXISTS receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                store TEXT,
                item_group TEXT,
                item_code TEXT,
                item_name TEXT,
                uom TEXT,
                qty REAL,
                rate REAL,
                value REAL,
                cost_center TEXT,
                user TEXT,
                hotel TEXT,
                month TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Sales Table
        c.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                item_code TEXT,
                item_name TEXT,
                quantity REAL,
                rate REAL,
                value REAL,
                discount REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Recipes Table
        c.execute("""
            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_code TEXT,
                item_name TEXT,
                selling_price REAL,
                cost_price REAL,
                cost_percentage REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Inventory Table
        c.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_code TEXT,
                item_name TEXT,
                opening_balance REAL,
                receipts REAL,
                issues REAL,
                closing_balance REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def add_column_if_not_exists(self, table, column, col_type="TEXT"):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute(f"PRAGMA table_info({table})")
        columns = [info[1] for info in c.fetchall()]
        if column not in columns:
            c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
            conn.commit()
        conn.close()

    def process_and_store_receipt_data(self, df):
        conn = self.get_connection()
        df.to_sql('receipts', conn, if_exists='replace', index=False)
        conn.close()

    def process_and_store_sales_data(self, df):
        conn = self.get_connection()
        df.to_sql('sales', conn, if_exists='replace', index=False)
        conn.close()

    def process_and_store_recipe_data(self, df):
        conn = self.get_connection()
        df.to_sql('recipes', conn, if_exists='replace', index=False)
        conn.close()

    def get_receipt_data(self):
        conn = self.get_connection()
        df = pd.read_sql_query("SELECT * FROM receipts", conn)
        conn.close()
        return df

    def get_sales_data(self):
        conn = self.get_connection()
        df = pd.read_sql_query("SELECT * FROM sales", conn)
        conn.close()
        return df

    def get_recipe_data(self):
        conn = self.get_connection()
        df = pd.read_sql_query("SELECT * FROM recipes", conn)
        conn.close()
        return df

class CostManagementApp:
    def __init__(self):
        st.set_page_config(page_title="Cost Management Dashboard", layout="wide")
        self.db = CostManagementDB()
        self.load_data()

    def load_data(self):
        try:
            # Load Receipt Data
            self.receipt_data = pd.read_excel("ABGN Item Receipt by Group 2024-2025.xlsx")
            self.receipt_data['Date'] = pd.to_datetime(self.receipt_data['Date'], format='%d/%m/%Y', errors='coerce')
            self.db.process_and_store_receipt_data(self.receipt_data)

            # Load Sales Data
            self.sales_data = pd.read_excel("ABGN Sale by Items Feb-2025.xlsx", skiprows=2)
            self.sales_data = self.sales_data.dropna(how='all')
            self.db.process_and_store_sales_data(self.sales_data)

            # Load Recipe Data
            self.beverage_recipe = pd.read_excel("ABGN Beverage Recipe MMK (Oct'24)Update.xls", skiprows=2)
            self.beverage_recipe = self.beverage_recipe.dropna(how='all')
            self.db.process_and_store_recipe_data(self.beverage_recipe)

        except Exception as e:
            st.error(f"Error loading data: {str(e)}")

    def main(self):
        st.title("Cost Management Dashboard")

        # Sidebar for navigation
        st.sidebar.title("Navigation")
        page = st.sidebar.radio("Select Page", 
            ["Overview", "Data Management", "Cost Analysis", "Recipe Management", "Reports"])

        if page == "Overview":
            self.show_overview_page()
        elif page == "Data Management":
            self.show_data_management_page()
        elif page == "Cost Analysis":
            self.show_cost_analysis_page()
        elif page == "Recipe Management":
            self.show_recipe_management_page()
        elif page == "Reports":
            self.show_reports_page()

    def show_overview_page(self):
        st.header("Overview Dashboard")

        # Get latest data from database
        receipt_df = self.db.get_receipt_data()

        # Create three columns for KPIs
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Receipt Value", 
                     f"{receipt_df['Value'].sum():,.0f} MMK",
                     "Monthly Average")

        with col2:
            st.metric("Total Items", 
                     f"{receipt_df['Item Code'].nunique():,}",
                     "Unique Items")

        with col3:
            st.metric("Average Transaction Value", 
                     f"{receipt_df['Value'].mean():,.0f} MMK",
                     "Per Receipt")

        # Monthly Trend Chart
        st.subheader("Monthly Cost Trends")
        monthly_data = receipt_df.groupby('MONTH')['Value'].sum().reset_index()
        fig = px.line(monthly_data, x='MONTH', y='Value',
                     title='Monthly Cost Trends')
        st.plotly_chart(fig, use_container_width=True)

        # Top Items
        st.subheader("Top Items by Value")
        top_items = receipt_df.groupby('Item Name')['Value'].sum().sort_values(ascending=False).head(10)
        fig = px.bar(top_items, title='Top 10 Items by Value')
        st.plotly_chart(fig, use_container_width=True)

    def show_data_management_page(self):
        st.header("Data Management")

        # Add new property to database
        st.subheader("Add New Property")
        col1, col2 = st.columns(2)
        with col1:
            table_name = st.selectbox("Select Table", 
                ["receipts", "sales", "recipes", "inventory"])
        with col2:
            new_column = st.text_input("New Column Name")

        col3, col4 = st.columns(2)
        with col3:
            column_type = st.selectbox("Column Type", 
                ["TEXT", "REAL", "INTEGER", "TIMESTAMP"])
        with col4:
            if st.button("Add Column"):
                try:
                    self.db.add_column_if_not_exists(table_name, new_column, column_type)
                    st.success(f"Added column {new_column} to {table_name}")
                except Exception as e:
                    st.error(f"Error adding column: {str(e)}")

        # View/Edit Data
        st.subheader("View Data")
        selected_table = st.selectbox("Select Table to View", 
            ["receipts", "sales", "recipes", "inventory"])

        if selected_table == "receipts":
            df = self.db.get_receipt_data()
        elif selected_table == "sales":
            df = self.db.get_sales_data()
        elif selected_table == "recipes":
            df = self.db.get_recipe_data()

        if not df.empty:
            st.dataframe(df)

            # Export data
            if st.button("Export to CSV"):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"{selected_table}.csv",
                    mime="text/csv"
                )

    def show_cost_analysis_page(self):
        st.header("Cost Analysis")

        # Get data from database
        receipt_df = self.db.get_receipt_data()

        # Filters
        col1, col2 = st.columns(2)
        with col1:
            selected_month = st.selectbox("Select Month", 
                sorted(receipt_df['MONTH'].unique()))
        with col2:
            selected_group = st.selectbox("Select Item Group", 
                sorted(receipt_df['Item Group'].unique()))

        # Filtered data
        filtered_data = receipt_df[
            (receipt_df['MONTH'] == selected_month) &
            (receipt_df['Item Group'] == selected_group)
        ]

        # Display metrics
        st.subheader("Cost Metrics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Cost", 
                     f"{filtered_data['Value'].sum():,.0f} MMK")
        with col2:
            st.metric("Average Cost", 
                     f"{filtered_data['Value'].mean():,.0f} MMK")
        with col3:
            st.metric("Item Count", 
                     f"{filtered_data['Item Code'].nunique():,}")

        # Cost Trends
        st.subheader("Cost Trends")
        daily_costs = filtered_data.groupby('Date')['Value'].sum().reset_index()
        fig = px.line(daily_costs, x='Date', y='Value',
                     title=f'Daily Cost Trends - {selected_group}')
        st.plotly_chart(fig, use_container_width=True)

        # Display detailed data
        st.subheader("Detailed Cost Data")
        st.dataframe(filtered_data)

    def show_recipe_management_page(self):
        st.header("Recipe Management")

        # Get recipe data from database
        recipe_df = self.db.get_recipe_data()

        # Display recipe analysis
        st.subheader("Recipe Cost Analysis")

        # Recipe filters
        selected_recipe = st.selectbox("Select Recipe", 
            recipe_df['Item Name'].unique())

        # Display recipe details
        recipe_details = recipe_df[recipe_df['Item Name'] == selected_recipe]
        if not recipe_details.empty:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Selling Price", 
                         f"{recipe_details['Selling Price'].iloc[0]:,.0f} MMK")
            with col2:
                st.metric("Cost Price", 
                         f"{recipe_details['Cost Price'].iloc[0]:,.0f} MMK")
            with col3:
                st.metric("Cost Percentage", 
                         f"{recipe_details['Cost Percentage'].iloc[0]:.2%}")

    def show_reports_page(self):
        st.header("Reports")

        report_type = st.selectbox("Select Report Type", 
            ["Cost Summary", "Recipe Cost Analysis", "Inventory Status"])

        if report_type == "Cost Summary":
            self.generate_cost_summary_report()
        elif report_type == "Recipe Cost Analysis":
            self.generate_recipe_cost_report()
        elif report_type == "Inventory Status":
            self.generate_inventory_report()

    def generate_cost_summary_report(self):
        st.subheader("Cost Summary Report")

        # Get data from database
        receipt_df = self.db.get_receipt_data()

        # Generate summary metrics
        summary_data = receipt_df.groupby('Item Group').agg({
            'Value': ['sum', 'mean', 'count'],
            'Qty': 'sum'
        }).round(2)

        st.dataframe(summary_data)

        # Export report
        if st.button("Export Report"):
            csv = summary_data.to_csv()
            st.download_button(
                label="Download Report",
                data=csv,
                file_name="cost_summary_report.csv",
                mime="text/csv"
            )

    def generate_recipe_cost_report(self):
        st.subheader("Recipe Cost Analysis Report")
        recipe_df = self.db.get_recipe_data()
        st.dataframe(recipe_df)

    def generate_inventory_report(self):
        st.subheader("Inventory Status Report")
        st.info("Inventory reporting coming soon...")

if __name__ == "__main__":
    app = CostManagementApp()
    app.main()
