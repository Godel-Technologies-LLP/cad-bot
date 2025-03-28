import ezdxf
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np
import os
import random


def generate_layer_colors(doc):
    """Generate a unique color for each layer in the document."""
    layers = doc.layers
    return {
        layer.dxf.name: (random.random(), random.random(), random.random())
        for layer in layers
    }


def extract_lines(entity, insert_point=(0, 0), layer_colors=None):
    """Extract line segments from a DXF entity."""
    dxftype = entity.dxftype()
    x_offset, y_offset = insert_point
    layer = entity.dxf.layer
    color = layer_colors.get(layer, (0, 0, 0))

    if dxftype == "LINE":
        start = (entity.dxf.start.x + x_offset, entity.dxf.start.y + y_offset)
        end = (entity.dxf.end.x + x_offset, entity.dxf.end.y + y_offset)
        return [[start, end]], color

    elif dxftype in ["CIRCLE", "ARC"]:
        center = (entity.dxf.center.x + x_offset, entity.dxf.center.y + y_offset)
        radius = entity.dxf.radius
        start_angle = np.radians(getattr(entity.dxf, "start_angle", 0))
        end_angle = np.radians(getattr(entity.dxf, "end_angle", 360))
        theta = np.linspace(start_angle, end_angle, 100)
        points = np.column_stack(
            [center[0] + radius * np.cos(theta), center[1] + radius * np.sin(theta)]
        )
        return [
            (tuple(points[i]), tuple(points[i + 1])) for i in range(len(points) - 1)
        ], color

    elif dxftype in ["POLYLINE", "LWPOLYLINE"]:
        points = [(p[0] + x_offset, p[1] + y_offset) for p in entity.get_points()]
        if entity.is_closed and points:
            points.append(points[0])
        return [(points[i], points[i + 1]) for i in range(len(points) - 1)], color

    return [], color


def process_dimension(entity, layer_colors):
    """Process dimension entities and extract geometric elements and text."""
    lines = []
    annotations = []
    try:
        for e in entity.virtual_entities():  # Explode dimension into primitives
            entity_lines, color = extract_lines(e, layer_colors=layer_colors)
            lines.extend(entity_lines)

        # Extract dimension text and position
        if hasattr(entity.dxf, "text_midpoint"):
            text_position = (
                entity.dxf.text_midpoint.x,
                entity.dxf.text_midpoint.y,
            )
            dim_text = str(round(float(entity.get_measurement()), 2))
            annotations.append({"position": text_position, "text": dim_text})
    except AttributeError:
        pass
    return lines, annotations


def plot_dxf(doc, msp, output_path, dpi=300, bg_color="#F5F5F5"):
    """Plot all entities including dimensions with text."""
    os.makedirs(output_path, exist_ok=True)
    all_lines, all_colors = [], []
    dimension_lines, dimension_colors = [], []
    all_annotations = []
    layer_colors = generate_layer_colors(doc)

    for entity in msp:
        layer = entity.dxf.layer
        color = layer_colors.get(layer, (0, 0, 0))

        if entity.dxftype() == "INSERT":
            insert_point = (entity.dxf.insert.x, entity.dxf.insert.y)
            block = doc.blocks.get(entity.dxf.name)
            for e in block:
                lines, _ = extract_lines(e, insert_point, layer_colors)
                all_lines.extend(lines)
                all_colors.extend([color] * len(lines))

        elif entity.dxftype() in ["DIMENSION", "ROTATED_DIMENSION"]:
            dim_lines, dim_annotations = process_dimension(entity, layer_colors)
            dimension_lines.extend(dim_lines)
            dimension_colors.extend([(0, 0, 0.8)] * len(dim_lines))  # Dark blue
            all_annotations.extend(dim_annotations)

        else:
            lines, line_color = extract_lines(entity, layer_colors=layer_colors)
            all_lines.extend(lines)
            all_colors.extend([line_color] * len(lines))

    if not all_lines and not dimension_lines and not all_annotations:
        print("No entities found to plot.")
        return

    fig, ax = plt.subplots(figsize=(10, 10), facecolor=bg_color)
    ax.set_aspect("equal")
    ax.axis("off")

    # Plot non-dimension lines (thicker)
    lc = LineCollection(
        all_lines, colors=all_colors, linewidths=1.0
    )  # Increased linewidth
    ax.add_collection(lc)

    # Plot dimension lines (dark blue)
    lc_dim = LineCollection(dimension_lines, colors=dimension_colors, linewidths=0.5)
    ax.add_collection(lc_dim)

    # Plot dimension text annotations
    for annotation in all_annotations:
        ax.annotate(
            annotation["text"],
            annotation["position"],
            color="black",
            fontsize=8,
            ha="center",
            va="center",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.7),
        )

    # Set plot limits based on all entities
    all_points = np.concatenate(all_lines + dimension_lines, axis=0)
    min_x, min_y = np.min(all_points, axis=0)
    max_x, max_y = np.max(all_points, axis=0)
    margin = (max(max_x - min_x, max_y - min_y)) * 0.05
    ax.set_xlim(min_x - margin, max_x + margin)
    ax.set_ylim(min_y - margin, max_y + margin)

    plt.savefig(
        os.path.join(output_path, "dxf_plot.png"),
        dpi=dpi,
        bbox_inches="tight",
        pad_inches=0.1,
    )
    plt.close()


if __name__ == "__main__":
    doc = ezdxf.readfile("./files/restroom.dxf")
    msp = doc.modelspace()
    plot_dxf(doc, msp, "./files")
