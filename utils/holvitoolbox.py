from datetime import datetime
import logging

from django.core.files.uploadedfile import InMemoryUploadedFile

import xlrd

class ParseError(Exception):
    """Raised when the data has invalid value"""

    pass

logger = logging.getLogger(__name__)
class HolviToolbox:
    """
    Contains various helper methods to handle Holvi data
    """

    @staticmethod
    def parse_account_statement(filename: InMemoryUploadedFile):
        """
        Parses Holvi account statement Excel in new or old header format

        Expected fields:
        "Date"/"Payment date", "Amount", "Currency", "Counterparty", "Description", "Reference",
        "Message", "Filing ID"

        Unused fields:
        "Execution date" after "Payment date"
        """
        sheet = xlrd.open_workbook(file_contents=filename.read()).sheet_by_index(0)

        date_fields = ["Payment date", "Date"]
        date_fields_finnish = ["Maksupvm"]

        fields_keys_english = ["Payment date", "Execution date", "Amount", "Currency", "Counterparty", "Description", "Reference", "Message","Filing ID"]

        fields_keys_finnish = ["Maksupvm", "Kirjauspäivä", "Summa", "Valuutta", "Vastapuoli", "Kuvaus", "Viite", "Viesti", "Arkistointitunnus"]

        headers = []
        items = []
        for row_index, row in enumerate(sheet.get_rows()):

            # Skip summary rows
            if headers == [] and row[0].value not in (date_fields + date_fields_finnish):
                continue
            headers.append(row[0].value)
            if len(headers) == 1:
                if headers[0] in date_fields_finnish:
                    headers = [field.value for field in row]
                    if headers == fields_keys_finnish:
                        headers = fields_keys_english
                    else:
                        raise ParseError("Holvi xls headers did not match expected. " + headers + " + " + fields_keys_finnish)
                else:
                    # Collect header row
                    headers = [field.value for field in row]
            else:
                # Extract row data as dictionary with header row as keys
                item = dict(zip(headers, [field.value for field in row]))

                # Parse payment date
                try:
                    # Try new field name first, present since around 2021-03-21
                    date_parsed = datetime.strptime(
                        item["Payment date"], "%d %b %Y"  # "9 Mar 2021"
                    )
                    # Set time to noon as new format has no payment time
                    item["Date_parsed"] = date_parsed.replace(hour=12, minute=00)
                except KeyError:
                    # Fallback: try old field name, preset in 2020-06-10
                    # If we get second KeyError, file header format is invalid and we let import crash out
                    item["Date_parsed"] = datetime.strptime(
                        item["Date"], "%d %b %Y, %H:%M:%S"  # "8 Jan 2020, 09:35:43"
                    )
                except ValueError:
                    # Parse finnish format date.
                    # If we get second KeyError, file header format is invalid and we let import crash out
                    date_parsed = datetime.strptime(
                        item["Payment date"], "%d.%m.%Y"  # 1.2.2022
                    )
                    item["Date_parsed"] = date_parsed.replace(hour=12, minute=00)


                # Force reference field to be strings
                item["Reference"] = str(item["Reference"])
                item["Message"] = str(item["Message"])

                # Add meta fields
                item["source_file"] = filename
                item["source_row"] = row_index + 1

                items.append(item)

        return items
