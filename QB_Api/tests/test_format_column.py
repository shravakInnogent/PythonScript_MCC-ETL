import pytest
from main import format_column_name

class TestFormatColumnName:
    def test_abbreviation_expansion(self):
        assert format_column_name("BillAddr_City") == "Bill_Address_City"
        assert format_column_name("CurrencyRef_value") == "Currency_Reference_value"
        assert format_column_name("PrimaryEmailAddr") == "Primary_Email_Address"

    def test_no_double_replacement(self):
        assert format_column_name("Address") == "Address"
        assert format_column_name("Number") == "Number"

    def test_camel_case_splitting(self):
        assert format_column_name("BalanceWithJobs") == "Balance_With_Jobs"
        assert format_column_name("CompanyName") == "Company_Name"

    def test_existing_underscores(self):
        assert format_column_name("Bill_Address") == "Bill_Address"
        assert format_column_name("Meta_Data_CreateTime") == "Meta_Data_Create_Time"