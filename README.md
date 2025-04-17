# Cost Management Dashboard

A comprehensive cost management solution with database integration for tracking receipts, sales, recipes, and inventory.

## Features

- SQLite database integration
- Dynamic property management
- Interactive data visualization
- Cost analysis and reporting
- Recipe management
- Data export capabilities

## Installation

1. Install required packages:
   ```
   pip install -r requirements.txt
   ```

2. Place your data files in the same directory:
   - ABGN Item Receipt by Group 2024-2025.xlsx
   - ABGN Beverage Recipe MMK (Oct'24)Update.xls
   - ABGN Sale by Items Feb-2025.xlsx
   - ABGN-A La Carte Menu Cost ( Updating )24,25.xlsx
   - ABGN One Line Store for Feb'25.xlsx

3. Run the app:
   ```
   streamlit run cost_management_app.py
   ```

## Features

### Data Management
- Add new properties to any table
- View and export table data
- Data validation and cleaning

### Cost Analysis
- Monthly and item group analysis
- Cost trends visualization
- Detailed cost metrics

### Recipe Management
- Recipe cost analysis
- Cost percentage tracking
- Recipe details management

### Reporting
- Cost summary reports
- Recipe cost analysis
- Inventory status reports
- Export capabilities

## Database Schema

The application uses SQLite with the following tables:

1. receipts
2. sales
3. recipes
4. inventory

Each table can be extended with new properties as needed through the UI.

## Usage

1. Start the application
2. Use the navigation sidebar to access different sections
3. Add new properties as needed in the Data Management section
4. Generate and export reports from the Reports section

## Notes

- The database (cost_management.db) is created automatically
- New properties can be added to any table at runtime
- All data can be exported to CSV format