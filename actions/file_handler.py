import ezdxf
import math
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from typing import List, Tuple


class DXFProcessor:
    """Handles DXF file operations, in-memory caching, and image conversion."""

    _instance = None

    def __new__(cls, file_path="./files/restroom.dxf"):
        """Ensure only one instance exists per DXF file."""
        if cls._instance is None or cls._instance.file_path != file_path:
            cls._instance = super(DXFProcessor, cls).__new__(cls)
            cls._instance._initialize(file_path)
        return cls._instance

    def _initialize(self, file_path: str):
        """Load DXF file into memory once."""
        self.file_path = file_path
        self.doc = ezdxf.readfile(file_path)
        self.msp = self.doc.modelspace()

    def get_entities_by_layer(self, layer_name: str) -> List:
        """Fetch all entities from a given layer."""
        entities = []
        for e in self.msp:
            if e.dxf.layer == layer_name:
                entities.append(e)
        return entities

    def get_points_from_layer(
        self, layer_name: str
    ) -> List[Tuple[float, float, float]]:
        """Fetch all POINT entities from a given layer."""
        return [
            (e.dxf.location.x, e.dxf.location.y, e.dxf.location.z)
            for e in self.get_entities_by_layer(layer_name)
            if e.dxftype() == "POINT"
        ]

    def move_objects(self, object: str, distance: float):
        """Move all objects in object_layer along the vector between two points in point_layer."""
        objects = self.get_entities_by_layer("A10_Wood- Door Window Ventilator")
        points = self.get_points_from_layer("A02_Wall")

        if len(points) != 2:
            raise ValueError("Point layer must contain exactly two points.")

        move_vector = self.get_vector_from_two_points(points[0], points[1])
        move_vector = tuple(coord * distance for coord in move_vector)

        for obj in objects:
            if hasattr(obj, "dxf"):
                obj.translate(*move_vector)

    def save(self, output_path: str):
        """Save the modified DXF file."""
        self.doc.saveas(output_path)
        print(f"Modified DXF saved to {output_path}")

    @staticmethod
    def get_vector_from_two_points(
        p1: Tuple[float, float, float], p2: Tuple[float, float, float]
    ) -> Tuple[float, float, float]:
        """Compute the unit vector from p1 to p2."""
        dx, dy, dz = p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2]
        length = math.sqrt(dx**2 + dy**2 + dz**2)
        return (dx / length, dy / length, dz / length) if length != 0 else (0, 0, 0)

    def convert_to_image(
        self,
        layers=None,
        dpi=300,
        bg_color="white",
        line_color="black",
        padding_factor=0.5,
    ):
        """Convert a DXF file to an image with only specified layers."""
        try:
            available_layers = [layer.dxf.name for layer in self.doc.layers]
            if layers and "list" in layers:
                print("Available layers in the DXF file:")
                for layer in available_layers:
                    print(f"- {layer}")
                return False

            fig = plt.figure(figsize=(10, 10), facecolor=bg_color)
            ax = fig.add_axes([0, 0, 1, 1])
            ax.set_aspect("equal")
            ax.axis("off")

            lines = []
            for e in self.msp:
                if layers and e.dxf.layer not in layers:
                    continue

                if e.dxftype() == "LINE":
                    lines.append(
                        [(e.dxf.start[0], e.dxf.start[1]), (e.dxf.end[0], e.dxf.end[1])]
                    )
                elif e.dxftype() == "CIRCLE":
                    center, radius = e.dxf.center, e.dxf.radius
                    theta = np.linspace(0, 2 * np.pi, 100)
                    x, y = center[0] + radius * np.cos(theta), center[
                        1
                    ] + radius * np.sin(theta)
                    points = np.column_stack([x, y])
                    circle_segments = [
                        (
                            (points[i][0], points[i][1]),
                            (points[i + 1][0], points[i + 1][1]),
                        )
                        for i in range(len(points) - 1)
                    ]
                    lines.extend(circle_segments)
                elif e.dxftype() in ["ARC", "POLYLINE", "LWPOLYLINE"]:
                    points = [(p[0], p[1]) for p in e.points()]
                    if e.is_closed:
                        points.append(points[0])
                    poly_segments = [
                        (points[i], points[i + 1]) for i in range(len(points) - 1)
                    ]
                    lines.extend(poly_segments)

            if lines:
                ax.add_collection(
                    LineCollection(lines, colors=line_color, linewidths=0.5)
                )
                all_points = np.array([point for line in lines for point in line])
                if all_points.any():
                    min_x, min_y = np.min(all_points, axis=0)
                    max_x, max_y = np.max(all_points, axis=0)
                    width, height = max_x - min_x, max_y - min_y
                    center_x, center_y = (min_x + max_x) / 2, (min_y + max_y) / 2
                    max_dim = max(width, height) * (1 + padding_factor * 2)
                    ax.set_xlim(center_x - max_dim / 2, center_x + max_dim / 2)
                    ax.set_ylim(center_y - max_dim / 2, center_y + max_dim / 2)
                plt.savefig(
                    "./files/moved_room.png",
                    dpi=dpi,
                    bbox_inches="tight",
                    pad_inches=0.5,
                )
                plt.close()
                print(f"DXF converted to image: {'./files/moved_room.png'}")
                return True
            else:
                print("No entities found in the specified layers.")
                plt.close()
                return False
        except Exception as e:
            print(f"Error converting DXF to image: {str(e)}")
            return False
