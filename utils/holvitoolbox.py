from io import BytesIO

from django.core.files.uploadedfile import InMemoryUploadedFile

from openpyxl import load_workbook
import dateparser


class HolviToolbox:
    """
    Contains various helper methods to handle Holvi data
    """

    @staticmethod
    def parse_account_statement(uploaded_file: InMemoryUploadedFile):
        """
        Parses Holvi account statement Excel in new or old header format. Holvi report system has
        been updated in 05/2022 to use XLSX files instead of XLSX. Parsing Excel reading library has
        been uodated to handle both file types.

        Expected fields:
        "Date"/"Payment date", "Amount", "Currency", "Counterparty", "Description", "Reference",
        "Message", "Filing ID"

        Unused fields:
        "Execution date" after "Payment date"
        """
        sheet = load_workbook(filename=BytesIO(uploaded_file.read())).active

        date_fields = ["Payment date", "Date"]
        headers = []
        items = []
        for row_index, row in enumerate(sheet.values):
            # Skip summary rows
            if headers == [] and row[0] not in date_fields:
                continue

            if headers == []:
                # Collect header row
                headers = list(row)
            else:
                # Extract row data as dictionary with header row as keys
                item = dict(zip(headers, list(row)))

                # Parse payment date
                item["Date_parsed"] = dateparser.parse(item["Payment date"])

                # Force reference field to be strings
                item["Reference"] = str(item["Reference"])
                item["Message"] = str(item["Message"])

                # Add meta fields
                item["source_file"] = uploaded_file.name
                item["source_row"] = str(row_index + 1)

                items.append(item)

        return items
