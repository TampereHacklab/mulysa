from io import BytesIO
import re

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
        "Value date", "Booking date", "Amount", "Currency", "Counterparty", "Description", "Reference",
        "Message", "Filing ID"
        """
        sheet = load_workbook(filename=BytesIO(uploaded_file.read())).active

        date_fields = ["Value date", "Payment date", "Date"]
        date_found = False
        date_error = None
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
                for field_name in date_fields:
                    try:
                        item["Date_parsed"] = dateparser.parse(item[field_name])
                        date_found = True
                        break
                    except KeyError as exc:
                        date_error = exc

                # Reraise last date field not found exception if none found
                if not date_found:
                    raise date_error

                if not item["Reference"]:
                    match = re.search(r"\b0*(\d+)\b", str(item["Message"]))
                    if match:
                        item["Reference"] = match.group(1)
                        item["Message"] = (
                            item["Message"] + " (reference extracted from message)"
                        )

                # Force reference field to be strings
                item["Reference"] = str(item["Reference"])
                item["Message"] = str(item["Message"])

                # Add meta fields
                item["source_file"] = uploaded_file.name
                item["source_row"] = str(row_index + 1)

                items.append(item)

        return items
