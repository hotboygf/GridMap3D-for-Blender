# panels.py
import bpy

class GRIDMAP_PT_setup(bpy.types.Panel):
    bl_label = "GridMap Setup"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "GridMap"

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.gridmap_settings

        box = layout.box()
        box.prop(settings, "piece_collection")
        box.prop(settings, "cell_size")
        layout.operator("gridmap.generate", text="Generate GridMap")


class GRIDMAP_PT_pieces(bpy.types.Panel):
    bl_label = "GridMap Pieces"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "GridMap"

    @classmethod
    def poll(cls, context):
        return context.mode == "EDIT_MESH"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.gridmap_settings
        source = settings.piece_collection

         # Level selector
        row = layout.row(align=True)
        row.label(text="Level:")
        row.prop(settings, "level", text="")
        # +/- buttons for quick nudging
        sub = row.row(align=True)
        op = sub.operator("gridmap.level_step", text="", icon="TRIA_DOWN")
        op.delta = -1
        op = sub.operator("gridmap.level_step", text="", icon="TRIA_UP")
        op.delta = 1

        if source is None:
            layout.label(text="No piece collection selected.", icon="INFO")
            return

        if settings.active_piece:
            layout.label(text=f"Placing: {settings.active_piece}", icon="CURSOR")
        else:
            layout.label(text="Select a piece below, then click in the viewport.")
        layout.separator()

        row = layout.row(align=True)
        op = row.operator("gridmap.place_modal", text="Add", icon="ADD")
        op.mode = "PLACE"
        op = row.operator("gridmap.place_modal", text="Remove", icon="REMOVE")
        op.mode = "DELETE"
        layout.separator()
        
        layout.label(text="Piece Library:")
        # List every mesh object in the source collection as a button.
        for obj in source.objects:
            if obj.type != "MESH":
                continue
            op = layout.operator(
                "gridmap.place_modal",
                text=obj.name
            )
            op.piece_name = obj.name

        layout.separator()
        layout.label(text="Cleanup:")
        layout.operator("gridmap.clean_up", text="Merge Duplicate Vertices", icon="AUTOMERGE_ON")