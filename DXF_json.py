import ezdxf
import json
import os
import tempfile


def advanced_drawing_to_dict(drawing):
    """
    Convert an ezdxf Drawing object to a detailed dictionary representation.

    Args:
        drawing (ezdxf.Drawing): The ezdxf Drawing object to convert

    Returns:
        dict: A comprehensive dictionary representation of the drawing
    """
    drawing_dict = {
        "dxf_version": drawing.dxfversion,
        "encoding": drawing.encoding,
        "header_vars": {},
        "entities": [],
        "blocks": {},
        "layers": {},
        "styles": {},
        "linetypes": {},
    }

    # Correctly extract header variables
    for key in drawing.header:
        try:
            drawing_dict["header_vars"][key] = str(drawing.header.get(key))
        except Exception as e:
            drawing_dict["header_vars"][key] = f"Unable to serialize: {str(e)}"

    # Entities extraction (similar to previous implementation)
    for entity in drawing.modelspace():
        entity_details = {
            "type": entity.dxftype(),
            "handle": entity.dxf.handle,
            "layer": entity.dxf.layer,
            "raw_dxf_attribs": {},
        }

        # Extract all DXF attributes
        for attrib in dir(entity.dxf):
            if not attrib.startswith("_"):
                try:
                    value = getattr(entity.dxf, attrib)
                    # Attempt to convert to a serializable format
                    entity_details["raw_dxf_attribs"][attrib] = str(value)
                except Exception as e:
                    entity_details["raw_dxf_attribs"][attrib] = str(e)

        drawing_dict["entities"].append(entity_details)

    # Blocks extraction
    for block in drawing.blocks:
        block_info = {"name": block.name, "entities": []}
        for entity in block:
            entity_details = {"type": entity.dxftype(), "raw_dxf_attribs": {}}
            for attrib in dir(entity.dxf):
                if not attrib.startswith("_"):
                    try:
                        value = getattr(entity.dxf, attrib)
                        entity_details["raw_dxf_attribs"][attrib] = str(value)
                    except Exception as e:
                        entity_details["raw_dxf_attribs"][attrib] = str(e)
            block_info["entities"].append(entity_details)
        drawing_dict["blocks"][block.name] = block_info

    # Layers extraction
    for layer in drawing.layers:
        drawing_dict["layers"][layer.dxf.name] = {
            "color": layer.dxf.color,
            "linetype": layer.dxf.linetype,
            "line_weight": layer.dxf.lineweight,
            "plot_style_name": layer.dxf.plot_style_name,
        }

    # Styles extraction
    for style in drawing.styles:
        drawing_dict["styles"][style.dxf.name] = {
            "height": style.dxf.height,
            "width": style.dxf.width,
            "font": style.dxf.font,
            "oblique_angle": style.dxf.oblique_angle,
        }

    # Linetypes extraction
    for linetype in drawing.linetypes:
        drawing_dict["linetypes"][linetype.name] = {
            "description": linetype.description,
            "pattern_length": linetype.pattern_length,
        }

    return drawing_dict


def restore_drawing_from_dict(drawing_dict):
    """
    Restore an ezdxf Drawing object from a dictionary representation.

    Args:
        drawing_dict (dict): Dictionary representation of the drawing

    Returns:
        ezdxf.Drawing: Reconstructed drawing object
    """
    # Create a new drawing with the original version
    doc = ezdxf.new(dxfversion=drawing_dict["dxf_version"])

    # Restore header variables
    for key, value in drawing_dict["header_vars"].items():
        try:
            # Remove 'Unable to serialize:' prefix if present
            if value.startswith("Unable to serialize:"):
                continue
            doc.header[key] = value
        except Exception as e:
            print(f"Could not restore header variable {key}: {e}")

    # Rest of the restoration method remains the same as in the previous implementation
    # (Layers, styles, linetypes, blocks, entities restoration)

    # Restore layers
    for layer_name, layer_info in drawing_dict["layers"].items():
        layer = doc.layers.add(layer_name)
        layer.dxf.color = layer_info["color"]
        layer.dxf.linetype = layer_info["linetype"]
        layer.dxf.lineweight = layer_info.get("line_weight", 0)
        layer.dxf.plot_style_name = layer_info.get("plot_style_name", "")

    # Restore styles
    for style_name, style_info in drawing_dict["styles"].items():
        style = doc.styles.add(style_name)
        style.dxf.height = style_info["height"]
        style.dxf.width = style_info["width"]
        style.dxf.font = style_info.get("font", "")
        style.dxf.oblique_angle = style_info.get("oblique_angle", 0)

    # Restore linetypes
    for linetype_name, linetype_info in drawing_dict["linetypes"].items():
        doc.linetypes.add(name=linetype_name, description=linetype_info["description"])

    # Restore blocks
    for block_name, block_info in drawing_dict["blocks"].items():
        block = doc.blocks.add(block_name)
        for entity_info in block_info["entities"]:
            # Recreate entities in the block
            entity_type = entity_info["type"]
            entity = block.add_entity(entity_type)

            # Restore entity attributes
            for attr, value in entity_info["raw_dxf_attribs"].items():
                try:
                    setattr(entity.dxf, attr, value)
                except Exception as e:
                    print(f"Could not restore attribute {attr} for {entity_type}: {e}")

    # Restore entities in modelspace
    modelspace = doc.modelspace()
    for entity_info in drawing_dict["entities"]:
        entity_type = entity_info["type"]
        entity = modelspace.add_entity(entity_type)

        # Restore entity attributes
        for attr, value in entity_info["raw_dxf_attribs"].items():
            try:
                setattr(entity.dxf, attr, value)
            except Exception as e:
                print(f"Could not restore attribute {attr} for {entity_type}: {e}")

    return doc


def save_drawing_to_json(drawing, filename):
    """
    Save drawing to a JSON file.

    Args:
        drawing (ezdxf.Drawing): Drawing object to save
        filename (str): Path to save the JSON file
    """
    drawing_dict = advanced_drawing_to_dict(drawing)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(drawing_dict, f, indent=2)


def load_drawing_from_json(filename):
    """
    Load drawing from a JSON file.

    Args:
        filename (str): Path to the JSON file

    Returns:
        ezdxf.Drawing: Restored drawing object
    """
    with open(filename, "r", encoding="utf-8") as f:
        drawing_dict = json.load(f)
    return restore_drawing_from_dict(drawing_dict)


def main():
    # Example usage
    try:
        # Open an existing DXF file
        doc = ezdxf.readfile("./files/restroom.dxf")

        # Create a temporary JSON file
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".json"
        ) as temp_json:
            # Save drawing to JSON
            drawing_dict = advanced_drawing_to_dict(doc)
            json.dump(drawing_dict, temp_json, indent=2)
            temp_json_path = temp_json.name

        # Restore drawing from JSON
        restored_doc = load_drawing_from_json(temp_json_path)

        # Save restored drawing
        restored_doc.saveas("./files/modified_restroom.dxf")

        # Clean up temporary file
        os.unlink(temp_json_path)

        print("Drawing successfully serialized and restored!")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
