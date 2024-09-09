import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd


class Sheet:
    def __init__(self, sheet_num, source_num, length, width):
        self.sheet_num = sheet_num  # Unique identifier for the sheet
        self.source_num = source_num
        self.length = length
        self.width = width
        self.layouts = []  # Store layouts for this sheet
        self.available_areas = [(0, 0, length, width)]  # List of available areas (x, y, width, height)


class GlassSource:
    def __init__(self, source_num, length, width, qty, cost):
        self.source_num = source_num
        self.length = length
        self.width = width
        self.total_qty = qty  # Total number of sheets available
        self.cost = cost
        self.remaining_pieces = qty  # Number of sheets remaining
        self.sheets = []  # List of Sheet objects used from this source


class GlassPart:
    def __init__(self, part_num, length, width, qty):
        self.part_num = part_num
        self.length = length
        self.width = width
        self.qty = qty


def parse_input():
    sources_data = pd.read_csv('glass_sources.csv')
    # iterate through the sources_data and create GlassSource objects
    sources = []
    for index, row in sources_data.iterrows():
        sources.append(
            GlassSource(row['Source Number'], row['Length(mm)'], row['Width(mm)'], row['Qty'], row['Cost per each']))

    parts_data = pd.read_csv('glass_parts.csv')
    # iterate through the parts_data and create GlassPart objects
    parts = []
    for index, row in parts_data.iterrows():
        parts.append(GlassPart(row['Part Number'], row['Length(mm)'], row['Width(mm)'], row['Qty']))

    return sources, parts


# Function to fit a part in the available areas using guillotine cutting
def guillotine_cut_part(sheet, part):
    for area in sorted(sheet.available_areas, key=lambda a: a[2] * a[3], reverse=True):
        x, y, available_width, available_height = area

        # Check if part fits in the available area (normal orientation)
        if part.length <= available_width and part.width <= available_height:
            # Place the part and split the remaining space
            sheet.layouts.append((part.part_num, x, y, part.length, part.width, 'normal'))

            # Split the remaining area into right and bottom areas
            new_areas = [
                (x + part.length, y, available_width - part.length, part.width),  # Right split
                (x, y + part.width, available_width, available_height - part.width)  # Bottom split
            ]
            # Remove the used area and update available areas
            sheet.available_areas.remove(area)
            # Add new areas that have positive width and height
            sheet.available_areas.extend([a for a in new_areas if a[2] > 0 and a[3] > 0])

            return True

        # Check if part fits in rotated orientation
        if part.width <= available_width and part.length <= available_height:
            # Place the part rotated and split the remaining space
            sheet.layouts.append((part.part_num, x, y, part.width, part.length, 'rotated'))

            # Split the remaining area into right and bottom areas
            new_areas = [
                (x + part.width, y, available_width - part.width, part.length),  # Right split
                (x, y + part.length, available_width, available_height - part.length)  # Bottom split
            ]
            # Remove the used area and update available areas
            sheet.available_areas.remove(area)
            # Add new areas that have positive width and height
            sheet.available_areas.extend([a for a in new_areas if a[2] > 0 and a[3] > 0])

            return True

    # If no fitting area was found, return False
    return False


def fit_parts_into_sources(sources, parts):

    sheet_counter = 1  # To assign unique identifiers to sheets

    # Try to place each part in a source
    for part in parts:
        for _ in range(part.qty):  # Handle each part individually based on its quantity
            placed = False
            for source in sources:
                if source.remaining_pieces > 0:
                    # Try placing the part on existing sheets first
                    for sheet in source.sheets:
                        if guillotine_cut_part(sheet, part):
                            placed = True
                            break
                    if placed:
                        break
                    # If not placed, create a new sheet and try placing the part
                    if source.remaining_pieces > 0:
                        new_sheet = Sheet(sheet_num=sheet_counter, source_num=source.source_num, length=source.length, width=source.width)
                        sheet_counter += 1
                        source.sheets.append(new_sheet)
                        source.remaining_pieces -= 1
                        if guillotine_cut_part(new_sheet, part):
                            placed = True
                            break
                if placed:
                    break
            if not placed:
                print(f"Warning: Part {part.part_num} could not be placed on any source.")
    return sources


# Function to visualize the layouts using Matplotlib
def visualize_layouts(sources):
    total_sheets = sum(len(source.sheets) for source in sources)
    cols = 2  # Number of columns in the plot grid
    rows = (total_sheets + cols - 1) // cols  # Calculate number of rows needed

    fig, axs = plt.subplots(rows, cols, figsize=(12, rows * 6))
    fig.suptitle("Glass Cutting Layouts")

    if rows == 1 and cols == 1:
        axs = [[axs]]
    elif rows == 1 or cols == 1:
        axs = [axs]

    sheet_idx = 0
    for source in sources:
        for sheet in source.sheets:
            row = sheet_idx // cols
            col = sheet_idx % cols
            ax = axs[row][col] if rows > 1 else axs[col]

            ax.set_title(f"Source {source.source_num} - Sheet {sheet.sheet_num} (L:{sheet.length}, W:{sheet.width})")
            ax.set_xlim(0, sheet.length)
            ax.set_ylim(0, sheet.width)
            ax.set_aspect('equal')
            ax.invert_yaxis()  # Invert y-axis for correct display

            for layout in sheet.layouts:
                part_num, x, y, length, width, orientation = layout
                rect = patches.Rectangle((x, y), length, width, linewidth=1, edgecolor='black', facecolor='lightblue')
                ax.add_patch(rect)
                ax.text(x + length / 2, y + width / 2, f"P{part_num}", color="black", ha="center", va="center", fontsize=8)
            sheet_idx += 1

    # Hide any unused subplots
    for idx in range(sheet_idx, rows * cols):
        row = idx // cols
        col = idx % cols
        fig.delaxes(axs[row][col] if rows > 1 else axs[col])

    plt.tight_layout()
    plt.show()


def optimizer(sources, parts):
    # sort the sources by cost, Ascending
    sources = sorted(sources, key=lambda x: x.cost)
    # sort the parts by area, Descending
    parts = sorted(parts, key=lambda x: x.length * x.width, reverse=True)

    # Fit parts into sources using guillotine cutting
    optimized_sources = fit_parts_into_sources(sources, parts)

    # Visualize the layouts
    visualize_layouts(optimized_sources)
    print()


_sources, _parts = parse_input()
optimizer(_sources, _parts)
