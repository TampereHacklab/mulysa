from datetime import datetime
import xlrd

class HolviToolbox:
    """
    Contains various helper methods to handle Holvi data
    """
    @staticmethod
    def parse_account_statement(filename):
        """
        Parses Holvi account statement Excel

        Expected fields:
        "Date", "Amount", "Currency", "Counterparty", "Description", "Reference",
        "Message", "Filing ID"
        """
        sheet = xlrd.open_workbook(filename).sheet_by_index(0)

        headers = []
        items = []
        for row_index, row in enumerate(sheet.get_rows()):
            # Skip summary rows
            if headers == [] and row[0].value != 'Date':
                continue

            if headers == []:
                # Collect header row
                headers = [field.value for field in row]
            else:
                # Extract row data as dictionary with header row as keys
                item = dict(
                    zip(
                        headers,
                        [field.value for field in row]
                    )
                )

                # Parse payment date
                item['Date_parsed'] = datetime.strptime(
                    item['Date'],
                    '%d %b %Y, %H:%M:%S' # 8 Jan 2020, 09:35:43
                )

                # Force reference field to be strings
                item['Reference'] = str(item['Reference'])
                item['Message'] = str(item['Message'])

                # Add meta fields
                item['source_file'] = filename
                item['source_row'] = row_index + 1

                items.append(item)

        return items

