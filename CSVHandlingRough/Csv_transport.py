import pandas as pd
import re
from datetime import datetime

# Configure pandas display options for better output visibility
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)


def process_csv_data():
    """
    function to read CSV, apply transformations, and save the output.
    Processes CSV data with column formatting, validation, and date conversion.
    """
    # Read CSV file
    df = pd.read_csv("/Users/shravakjain/Library/CloudStorage/OneDrive-Personal/Xero_Data/Contacts_20260112_174755.csv")
    
    # print(df.head)
    # print(df.columns.tolist())
    # print(df.dtypes)
    # print(df.shape)
    
    # --------------------------- Displaying Data ---------------------
    print(df)

    # print(df.head(11).T)  # It print column vertically and values horizontally
    # print(df[["ContactID", "Name"]].head())  # To print specific columns from top
    # print(df[["ContactID", "Name"]].tail())  # To print specific columns from end

    # Standardizing column names (alternative approach)
    # df.columns = (
    #     df.columns
    #     .str.strip()
    #     .str.lower()
    #     .str.replace(" ", "_")
    # )
    # print(df)

    # Apply transformations
    df = format_column_names(df)
    print(df)

    df = add_validation_columns(df)
    print(df)

    df = convert_utc_to_local_time(df)
    print(df)

    # Save transformed data with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"/Users/shravakjain/Library/CloudStorage/OneDrive-Personal/Xero_Data/Contacts_20260112_174755_{timestamp}.csv"
    df.to_csv(output_path, index=False)
    print(f"\nData successfully saved to: {output_path}")


# ---------------------------- Rename Column ------------------------
def format_column_names(df):
    """
    Format column names by expanding abbreviations and adding underscores.
    Also fills null values with 'Not available'.
    
    Args:
        df: Input DataFrame
    
    Returns:
        DataFrame with formatted column names
    """
    # df = df[["ContactID", "ContactNumber"]]
    # df.rename(columns={
    #     "ContactID": "Contact_ID",
    #     "ContactNumber": "Contact_Number"
    # }, inplace=True)

    # Fill null fields with placeholder text
    df.fillna("Not available", inplace=True)

    # Use regex with word boundaries to match only complete abbreviations
    replacements = [
        (r'ID(?![a-z])', 'ID'),
        (r'Addr(?![a-z])', 'Address'),
        (r'Ref(?![a-z])', 'Reference'),
        (r'Desc(?![a-z])', 'Description'),
        (r'Amt(?![a-z])', 'Amount'),
        (r'Acct(?![a-z])', 'Account'),
        (r'Curr(?![a-z])', 'Currency'),
        (r'Pmt(?![a-z])', 'Payment'),
        (r'Inv(?![a-z])', 'Invoice'),
        (r'Emp(?![a-z])', 'Employee'),
        (r'Cust(?![a-z])', 'Customer'),
        (r'Tel(?![a-z])', 'Telephone'),
        (r'Txn(?![a-z])', 'Transaction'),
        (r'Num(?![a-z])', 'Number')
    ]

    # Process each column name
    new_columns = {}
    for column_name in df.columns:
        formatted_name = column_name
        # Apply abbreviation replacements
        for pattern, replacement in replacements:
            formatted_name = re.sub(pattern, replacement, formatted_name)

        # Add underscores before capitals (but not if underscore already exists)
        formatted_name = re.sub(r'(?<!_)(?=[A-Z])', '_', formatted_name)

        # Remove leading underscore if it exists
        if formatted_name.startswith('_'):
            formatted_name = formatted_name[1:]

        new_columns[column_name] = formatted_name

    df.rename(columns=new_columns, inplace=True)
    return df


# --------------------------- Adding New Column ------------------------
def add_validation_columns(df):
    """
    Add new columns to the DataFrame including source identifier and validation.

    Args:
        df: Input DataFrame
    
    Returns:
        DataFrame with new columns added
    """
    # df["Source"] = "XeroDataSource"  # This adds new column at the end of the table
    df.insert(1, "Source", "XeroDataSource")  # This adds new column at specific index
    print(df)

    # ------------------- Conditional / Derived Column -----------------------

    # This add new column with value based on the column "Contact_Number" length
    # df["Contact_Number_Validate"] = df["Contact_Number"].apply(
    #     lambda x: "Valid" if len(str(x)) == 10 else "Invalid"
    # )

    # This also add new column based on the condition but get inserted at specific index
    df.insert(3, "Contact_Number_Validate", df["Contact_Number"].apply(
        lambda x: "Valid" if len(str(x)) == 10 else "Invalid"
    ))
    return df


# -------------- Formatting Date and Time -----------
def convert_utc_to_local_time(df):
    """
    Convert UTC date from milliseconds to datetime and convert to Asia/Kolkata timezone.
    
    Args:
        df: Input DataFrame
    
    Returns:
        DataFrame with formatted date column
    """
    # Extract numeric timestamp from string
    df["Updated_Date_U_T_C"] = (df["Updated_Date_U_T_C"]
                                .astype(str)  # It forces every value to become a string
                                .str.extract(r"(\d+)"))  # \d -> digits(0-9), + -> one or more, () -> capture group

    # Convert milliseconds to datetime
    df["Updated_Date_U_T_C"] = pd.to_datetime(
        df["Updated_Date_U_T_C"],
        unit='ms',
        utc=True,
        errors='coerce'
    )
    
    # Convert timezone from UTC to Asia/Kolkata
    df["Updated_Date_U_T_C"] = df["Updated_Date_U_T_C"].dt.tz_convert("Asia/Kolkata")
    return df


if __name__ == '__main__':
    process_csv_data()
