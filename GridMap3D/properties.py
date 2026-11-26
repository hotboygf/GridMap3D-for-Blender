# properties.py
import bpy


class GRIDMAP_PG_settings(bpy.types.PropertyGroup):
    piece_collection: bpy.props.PointerProperty(
        name="Piece Collection",
        type=bpy.types.Collection,
        description="Collection containing the meshes used as GridMap pieces",
    )
    cell_size: bpy.props.FloatProperty(
        name="Cell Size",
        default=2.0,
        min=0.01,
        description="Size of a single grid cell",
    )
    level: bpy.props.IntProperty(
        name="Level",
        default=0,
        description="Current vertical layer (0 = ground)",
    )
    active_piece: bpy.props.StringProperty(
        name="Active Piece",
        description="Piece that will be placed with the next click",
    )
    edit_mode: bpy.props.EnumProperty(
        name="Edit Mode",
        items=[
            ("PLACE", "Place", ""),
            ("DELETE", "Delete", ""),
        ],
        default="PLACE"
    )


def register():
    # Ensure the PropertyGroup class is registered first
    if not getattr(GRIDMAP_PG_settings, "is_registered", False):
        bpy.utils.register_class(GRIDMAP_PG_settings)
    # Then bind to Scene
    bpy.types.Scene.gridmap_settings = bpy.props.PointerProperty(
        type=GRIDMAP_PG_settings
    )

def unregister():
    del bpy.types.Scene.gridmap_settings
    bpy.utils.unregister_class(GRIDMAP_PG_settings)