import bpy, bmesh, mathutils, blf, math
from bpy_extras import view3d_utils
from mathutils import Vector, Matrix, Quaternion

_modal_active = False

class GRIDMAP_OT_generate(bpy.types.Operator):
    bl_idname = "gridmap.generate"
    bl_label = "Generate GridMap"

    def execute(self, context):
        scene = context.scene
        settings = scene.gridmap_settings

        if not settings.piece_collection:
            self.report({'ERROR'}, "No piece collection selected.")
            return {'CANCELLED'}

        # 1. Create a new collection for the GridMap
        gridmap_col = bpy.data.collections.new("GridMap")
        context.collection.children.link(gridmap_col)

        # 2. Create the GridMap mesh object
        mesh = bpy.data.meshes.new("GridMap_Mesh")
        obj = bpy.data.objects.new("GridMap_Object", mesh)
        gridmap_col.objects.link(obj)

        # 3. Store configuration & cell data
        obj["gridmap_cell_size"] = settings.cell_size
        obj["cells"] = {}  # dict: { "layer_x_y": "PieceObjectName" }

        # 4. Initialize mesh with an empty bmesh
        bm = bmesh.new()
        bm.faces.layers.string.new("cell_key")
        bm.to_mesh(mesh)
        bm.free()

        # 5. Select and enter Edit Mode
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')

        # 6. Create visual grid
        self._create_grid(context)

        return {'FINISHED'}

    def _create_grid(self, context):
        pass 


def _get_or_create_material_slot(obj, material):
    # Return the slot index for material on obj, adding a slot if needed.
    if material is None: return 0

    for i, slot in enumerate(obj.material_slots):
        if slot.material == material: return i

    # Not found: append a new slot.
    obj.data.materials.append(material)
    return len(obj.material_slots) - 1


class GRIDMAP_OT_place_piece(bpy.types.Operator):
    bl_idname = "gridmap.place_piece"
    bl_label = "Place Piece"
    bl_options = {"REGISTER", "UNDO"}

    piece_name: bpy.props.StringProperty()
    cell_coord: bpy.props.IntVectorProperty(size=3)
    rotation: bpy.props.FloatVectorProperty(size=4)

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != "MESH":
            self.report({"ERROR"}, "No active GridMap mesh object.")
            return {"CANCELLED"}
   
        # --- 1. Determine target cell -------------------------------------
        settings = context.scene.gridmap_settings
        size = settings.cell_size
        cell_coord = self.cell_coord
        cell_key = f"{cell_coord[0]}_{cell_coord[1]}_{cell_coord[2]}"
        
        # --- 2. Fetch the source piece -------------------------------------
        source = bpy.data.objects.get(self.piece_name)
        if source is None or source.type != "MESH":
            self.report({"ERROR"}, f"Piece '{self.piece_name}' not found.")
            return {"CANCELLED"}

        mat = source.active_material
        mat_index = _get_or_create_material_slot(obj, mat)

        # center + rotation for proper placement
        R = Quaternion(self.rotation).to_matrix()
        c_local = sum((Vector(c) for c in source.bound_box), Vector()) / 8.0

        # --- 3. Merge geometry into the GridMap mesh -----------------------
        # Get the source mesh data.
        source_mesh = source.to_mesh()
        if source_mesh is None:
            self.report({"ERROR"}, "Could not get mesh data from piece.")
            return {"CANCELLED"}

        # Work on the edit-mode bmesh.
        bm = bmesh.from_edit_mesh(obj.data)
        key_layer = bm.faces.layers.string.get("cell_key") or bm.faces.layers.string.new("cell_key")

        offset = Vector(cell_coord) * size
       
        vert_map = {}
        for v in source_mesh.vertices:
            co = R @ (v.co - c_local) + c_local + offset
            vert_map[v.index] = bm.verts.new(co)

        bm.verts.ensure_lookup_table()

        for poly in source_mesh.polygons:
            try:
                new_face = bm.faces.new(
                    [vert_map[vi] for vi in poly.vertices]
                )
                new_face.material_index = mat_index
                new_face[key_layer] = cell_key.encode("utf-8")
            except ValueError:
                pass

        bmesh.update_edit_mesh(obj.data)
        source.to_mesh_clear()

        # --- 4. Record cell → piece name -----------------------------------
        cells = obj.get("cells", {})
        cells[cell_key] = self.piece_name
        obj["cells"] = cells

        return {"FINISHED"}


class GRIDMAP_OT_place_modal(bpy.types.Operator):
    bl_idname = "gridmap.place_modal"
    bl_label = "Place Pieces (Modal)"
    bl_options = {"REGISTER", "UNDO"}

    piece_name: bpy.props.StringProperty()
    mode: bpy.props.EnumProperty(items=[
            ("PLACE", "Place", ""),
            ("DELETE", "Delete", ""),
        ], default="PLACE")

    def invoke(self, context, event):
        global _modal_active
        if _modal_active:
            # Already placing; just update the active piece and return.
            s = context.scene.gridmap_settings
            if self.piece_name:
                s.active_piece = self.piece_name
            
            return {"FINISHED"}
        _modal_active = True

        s = context.scene.gridmap_settings

        # Set the active piece from the button click, *once*.
        if self.piece_name:
            s.active_piece = self.piece_name

        self.ghost_obj = None
        self._ghost_mat = None
        self._current_piece = None
        self._last_cell = None
        
        self._c_local = None
        self._rotation_matrix = Matrix.Identity(3)

        args = (self, context)
        self._draw_handle = bpy.types.SpaceView3D.draw_handler_add(
            self._draw_text, args, 'WINDOW', 'POST_PIXEL'
        )

        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        return self.invoke(context, None)

    def modal(self, context, event):
        s = context.scene.gridmap_settings
        ROT_STEP = math.pi / 2

        # Cancel on Esc / Right‑click
        if event.type == "ESC" or (event.type == "RIGHTMOUSE" and event.value == "PRESS" and event.ctrl):
            bpy.types.SpaceView3D.draw_handler_remove(self._draw_handle, 'WINDOW')
            self._cleanup_ghost(context)
            return {"CANCELLED"}

        # Recreate ghost when the active piece changes
        if (s.active_piece != self._current_piece) or (s.edit_mode != self._current_mode):
            self._cleanup_ghost(context)
            self._current_piece = s.active_piece
            self._current_mode = s.edit_mode
            if s.edit_mode == "DELETE" or s.active_piece:
                self._last_cell = self._get_cell_coord(context, event)
                self.ghost_obj = self._create_ghost(context, s.active_piece)
                self._update_ghost_position(s.cell_size)

        # Update ghost position to the hovered cell
        if event.type == "MOUSEMOVE" and self.ghost_obj:
            self._last_cell = self._get_cell_coord(context, event)
            if self._last_cell:
                self.ghost_obj.location = Vector(self._last_cell) * s.cell_size

        if event.type in {"W", "A", "S", "D"} and event.value == "PRESS":
            if event.type == "W":   Δ = Matrix.Rotation(-ROT_STEP, 3, 'X')
            elif event.type == "S": Δ = Matrix.Rotation( ROT_STEP, 3, 'X')
            elif event.type == "A": Δ = Matrix.Rotation(-ROT_STEP, 3, 'Z')
            elif event.type == "D": Δ = Matrix.Rotation( ROT_STEP, 3, 'Z')
            self._rotation_matrix = Δ @ self._rotation_matrix
        
            if self.ghost_obj:
                self.ghost_obj.rotation_mode = 'QUATERNION'
                self.ghost_obj.rotation_quaternion = self._rotation_matrix.to_quaternion()
                if self._last_cell is not None:
                    self._update_ghost_position(s.cell_size)
            context.area.tag_redraw()

        if event.type == "LEFTMOUSE" and event.value == "PRESS":
            quat = self._rotation_matrix.to_quaternion()
            if self.mode == "DELETE" and self._last_cell:
                bpy.ops.gridmap.delete_piece(
                    cell_coord=self._last_cell,
                    cell_key=f"{self._last_cell[0]}_{self._last_cell[1]}_{self._last_cell[2]}",
                )
            elif s.active_piece and self._last_cell:
                bpy.ops.gridmap.place_piece(
                    piece_name=s.active_piece,
                    cell_coord=self._last_cell,
                    rotation=quat[:],
                )

        return {'RUNNING_MODAL'}

    def _get_cell_coord(self, context, event):
        # Get mouse coordinates
        mouse_pos = (event.mouse_region_x, event.mouse_region_y)
        region = context.region
        region3d = context.space_data.region_3d
        settings = context.scene.gridmap_settings
        
        # Calculate ray
        view_point = view3d_utils.region_2d_to_origin_3d(region, region3d, mouse_pos)
        view_vector = view3d_utils.region_2d_to_vector_3d(region, region3d, mouse_pos)
        
        # Raycast to grid plane (example assumes X/Y plane at z=0)
        # You can adjust the plane based on your grid orientation
        from mathutils.geometry import intersect_line_plane
        hit = intersect_line_plane(view_point, view_point + view_vector, 
                                   Vector((0,0,0)), Vector((0,0,1)))
        
        if hit:
            cell = context.scene.gridmap_settings.cell_size
            return (round(hit.x / cell), round(hit.y / cell), round(settings.level))
        return None

    def _create_ghost(self, context, piece_name):
        s = context.scene.gridmap_settings
        if self.mode == "DELETE":
            bm = bmesh.new()
            bmesh.ops.create_cube(bm, size=s.cell_size)
            mesh = bpy.data.meshes.new("__ghost_delete_mesh")

            bm.to_mesh(mesh)
            bm.free()

            ghost = bpy.data.objects.new("__ghost_delete", mesh)
            context.collection.objects.link(ghost)

            ghost.hide_render = True
            ghost.hide_select = True
            ghost.show_in_front = True
            ghost.display_type = "WIRE"

            self.ghost_obj = ghost
            return ghost
            

        source = bpy.data.objects.get(piece_name)
        if source is None or source.type != "MESH":
            return None

        # get center
        bb = source.bound_box
        c_local = sum((Vector(c) for c in bb), Vector()) / 8.0

        # 1. Duplicate the object as a ghost
        ghost = source.copy()
        ghost.name = f"__ghost_{piece_name}"
        ghost.data = source.data
        
        self._c_local = c_local

        # 2. Link into the current view layer's active collection.
        context.collection.objects.link(ghost)

        # 3. Make it non-interactive / non-renderable.
        ghost.hide_render = True
        ghost.hide_select = True
        ghost.show_in_front = True

        # 4. Give it a translucent "hologram" material.
        ghost_mat = bpy.data.materials.new("__ghost_mat")
        ghost_mat.use_nodes = True
        bsdf = ghost_mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.2, 0.8, 1.0, 1.0)
            bsdf.inputs["Alpha"].default_value = 0.35
            bsdf.inputs["Emission Color"].default_value = (0.2, 0.8, 1.0, 1.0)
            bsdf.inputs["Emission Strength"].default_value = 0.5
        ghost_mat.blend_method = "BLEND"      # Eevee translucency
        ghost_mat.show_transparent_back = False

        # Replace material slots on the ghost only (object-linked slots)
        ghost.data = source.data.copy()       # copy so we don't touch the source mesh
        ghost.data.materials.clear()
        ghost.data.materials.append(ghost_mat)

        self._ghost_material = ghost_mat      # keep ref for cleanup
        return ghost

    def _update_ghost_position(self, cell_size):
        if self.ghost_obj is None or self._last_cell is None or self._c_local is None:
            return
        p = Vector(self._last_cell) * cell_size
        R = self._rotation_matrix
        self.ghost_obj.location = p - R @ self._c_local

    def _cleanup_ghost(self, context):
        if getattr(self, "ghost_obj", None):
            mesh = self.ghost_obj.data
            bpy.data.objects.remove(self.ghost_obj, do_unlink=True)
            if mesh and mesh.users == 0:
                bpy.data.meshes.remove(mesh)
            self.ghost_obj = None
        if getattr(self, "_ghost_material", None):
            if self._ghost_material.users == 0:
                bpy.data.materials.remove(self._ghost_material)
            self._ghost_material = None
        global _modal_active
        _modal_active = False

    def _draw_text(self, self_op, context):
        font_id = 0  # Default font
        blf.position(font_id, 20, 20, 0)  # Lower-left corner
        blf.size(font_id, 20.0)
        blf.color(font_id, 0.82, 0.82, 0.82, 1.0)
        blf.draw(font_id, "Esc / Ctrl + RMB to cancel. WASD to rotate.")

class GRIDMAP_OT_level_step(bpy.types.Operator):
    bl_idname = "gridmap.level_step"
    bl_label = "Change Grid Level"
    bl_options = {"REGISTER", "UNDO"}

    delta: bpy.props.IntProperty(default=1)

    def execute(self, context):
        s = context.scene.gridmap_settings
        s.level = max(0, s.level + self.delta)
        return {"FINISHED"}

class GRIDMAP_OT_clean_up(bpy.types.Operator):
    bl_idname = "gridmap.clean_up"
    bl_label = "Clean Up GridMap"
    bl_options = {"REGISTER", "UNDO"}


    def execute(self, context):
        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)

        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
        bmesh.update_edit_mesh(obj.data)

        return {"FINISHED"}

class GRIDMAP_OT_delete_piece(bpy.types.Operator):
    bl_idname = "gridmap.delete_piece"
    bl_label = "Delete Piece"
    bl_options = {"REGISTER", "UNDO"}

    piece_name: bpy.props.StringProperty()
    cell_coord: bpy.props.IntVectorProperty(size=3)
    cell_key: bpy.props.StringProperty()

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != "MESH":
            return {"CANCELLED"}

        bm = bmesh.from_edit_mesh(obj.data)
        layer = bm.faces.layers.string.get("cell_key")
        target = self.cell_key.encode("utf-8")
        if layer is None:
            return {"CANCELLED"}

        doomed = [f for f in bm.faces if f[layer] == target]
        if not doomed:
            return {"CANCELLED"}

        bmesh.ops.delete(bm, geom=doomed, context="FACES")

        # also remove any verts that are now orphans
        orphan_verts = [v for v in bm.verts if not v.link_faces]
        if orphan_verts:
            bmesh.ops.delete(bm, geom=orphan_verts, context="VERTS")

        bmesh.update_edit_mesh(obj.data)

        # drop the cell record
        cells = obj.get("cells", {})
        cells.pop(self.cell_key, None)
        obj["cells"] = cells

        return {"FINISHED"}