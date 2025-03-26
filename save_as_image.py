import ezdxf
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np


def dxf_to_image(
    dxf_path, output_path, layers=None, dpi=300, bg_color="white", line_color="black"
):
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    fig, ax = plt.subplots(figsize=(10, 10), facecolor=bg_color)
    ax.set_aspect("equal")
    ax.axis("off")
    lines = []
    texts = []
    dim_positions = set()

    def add_entity(e, insert_point=(0, 0)):
        if e.dxftype() == "LINE":
            lines.append(
                [
                    (e.dxf.start.x + insert_point[0], e.dxf.start.y + insert_point[1]),
                    (e.dxf.end.x + insert_point[0], e.dxf.end.y + insert_point[1]),
                ]
            )
        elif e.dxftype() in ["CIRCLE", "ARC"]:
            center = (
                e.dxf.center.x + insert_point[0],
                e.dxf.center.y + insert_point[1],
            )
            radius = e.dxf.radius
            start_angle = np.radians(getattr(e.dxf, "start_angle", 0))
            end_angle = np.radians(getattr(e.dxf, "end_angle", 360))
            theta = np.linspace(start_angle, end_angle, 100)
            points = np.column_stack(
                [center[0] + radius * np.cos(theta), center[1] + radius * np.sin(theta)]
            )
            lines.extend(
                [
                    (tuple(points[i]), tuple(points[i + 1]))
                    for i in range(len(points) - 1)
                ]
            )
        elif e.dxftype() in ["POLYLINE", "LWPOLYLINE"]:
            points = (
                [
                    (p[0] + insert_point[0], p[1] + insert_point[1])
                    for p in e.get_points()
                ]
                if hasattr(e, "get_points")
                else []
            )
            if e.is_closed and points:
                points.append(points[0])
            lines.extend([(points[i], points[i + 1]) for i in range(len(points) - 1)])
        elif e.dxftype() == "DIMENSION":
            try:
                dim_value = (
                    round(float(e.get_measurement()), 2)
                    if hasattr(e, "get_measurement")
                    else ""
                )
                pos = (
                    e.dxf.text_midpoint.x + insert_point[0],
                    e.dxf.text_midpoint.y + insert_point[1],
                )
                if dim_value and pos not in dim_positions:
                    # texts.append((pos[0], pos[1], str(dim_value), "red"))
                    dim_positions.add(pos)
                for entity in e.virtual_entities():
                    add_entity(entity, insert_point)
            except Exception:
                pass
        elif e.dxftype() == "MTEXT":
            texts.append(
                (
                    e.dxf.insert.x + insert_point[0],
                    e.dxf.insert.y + insert_point[1],
                    e.dxf.text,
                    line_color,
                )
            )
        # elif e.dxftype() == "INSERT":
        #     process_block(e)

    def process_block(insert_entity):
        block_name = insert_entity.dxf.name
        insert_point = (insert_entity.dxf.insert.x, insert_entity.dxf.insert.y)
        block = doc.blocks.get(block_name)
        if not block:
            return
        for entity in block:
            add_entity(entity, insert_point)

    for e in msp:
        if layers and e.dxf.layer not in layers:
            continue
        add_entity(e, insert_point=(0, 0))

    if lines:
        ax.add_collection(LineCollection(lines, colors=line_color, linewidths=0.5))
        all_points = np.array([pt for line in lines for pt in line])
        min_x, min_y = np.min(all_points, axis=0)
        max_x, max_y = np.max(all_points, axis=0)
        margin_x, margin_y = (max_x - min_x) * 0.05, (max_y - min_y) * 0.05
        ax.set_xlim(min_x - margin_x, max_x + margin_x)
        ax.set_ylim(min_y - margin_y, max_y + margin_y)

    for x, y, text, color in texts:
        ax.text(x, y, text, fontsize=6, color=color, ha="center", va="center")

    plt.savefig(output_path, dpi=dpi, bbox_inches="tight", pad_inches=0.1)
    plt.close()
    return True


if __name__ == "__main__":
    dxf_to_image("./restroom.dxf", "./image.png")
