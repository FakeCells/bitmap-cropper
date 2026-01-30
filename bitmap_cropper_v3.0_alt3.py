import tkinter as tk
from tkinter import filedialog, messagebox, ttk, Toplevel, colorchooser
from PIL import Image, ImageTk, ImageDraw
import os
import subprocess

class BitmapCropperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Bitmap Font Repacker V3.0 (Advanced)")
        self.root.geometry("650x530")
        
        style = ttk.Style()
        style.theme_use('clam')
        
        self.source_image_path = None
        self.source_filename = ""
        self.source_image = None
        self.exceptions = {} 
        self.mask_color = (255, 0, 255) # Default Magenta
        
        try:
            self.root.iconbitmap("bmfr.ico")
        except tk.TclError:
            print("bmfr.ico not found, using built-in app icon.")
        
        # Data
        self.source_image_path = None
        self.source_image = None
        self.preview_image = None 
        self.exceptions = {} # Stores { index: {dx, dy, dw, dh} }

        # --- UI START ---
        
        # 1. File & Base Config
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(padx=10, pady=5, fill="both", expand=True)

        # TAB 1: GENERAL SETTINGS
        self.tab_general = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_general, text="General Settings")

        # 1.1 Source
        self.frame_file = ttk.LabelFrame(self.tab_general, text="1. Import Font", padding=10)
        self.frame_file.pack(padx=10, pady=5, fill="x")
        ttk.Button(self.frame_file, text="Select Image", command=self.load_image).pack(side="left")
        self.lbl_file_status = ttk.Label(self.frame_file, text="No file selected", foreground="gray")
        self.lbl_file_status.pack(side="left", padx=10)

        # 1.2 Base Grid
        self.frame_config = ttk.LabelFrame(self.tab_general, text="2. Base Grid Size", padding=10)
        self.frame_config.pack(padx=10, pady=5, fill="x")
        ttk.Label(self.frame_config, text="Char W:").grid(row=0, column=0)
        self.entry_char_w = ttk.Entry(self.frame_config, width=5); self.entry_char_w.insert(0, "8"); self.entry_char_w.grid(row=0, column=1)
        ttk.Label(self.frame_config, text="Char H:").grid(row=0, column=2)
        self.entry_char_h = ttk.Entry(self.frame_config, width=5); self.entry_char_h.insert(0, "16"); self.entry_char_h.grid(row=0, column=3)

        # 1.3 Global Offsets
        self.frame_gaps = ttk.LabelFrame(self.tab_general, text="3. Global Offsets (Margins/Gaps)", padding=10)
        self.frame_gaps.pack(padx=10, pady=5, fill="x")
        ttk.Label(self.frame_gaps, text="Start Off X:").grid(row=0, column=0); self.entry_off_x = ttk.Entry(self.frame_gaps, width=4); self.entry_off_x.insert(0, "0"); self.entry_off_x.grid(row=0, column=1)
        ttk.Label(self.frame_gaps, text="Start Off Y:").grid(row=0, column=2); self.entry_off_y = ttk.Entry(self.frame_gaps, width=4); self.entry_off_y.insert(0, "0"); self.entry_off_y.grid(row=0, column=3)
        ttk.Label(self.frame_gaps, text="Gap X:").grid(row=1, column=0); self.entry_gap_x = ttk.Entry(self.frame_gaps, width=4); self.entry_gap_x.insert(0, "0"); self.entry_gap_x.grid(row=1, column=1)
        ttk.Label(self.frame_gaps, text="Gap Y:").grid(row=1, column=2); self.entry_gap_y = ttk.Entry(self.frame_gaps, width=4); self.entry_gap_y.insert(0, "0"); self.entry_gap_y.grid(row=1, column=3)

        # 1.4 Output
        self.frame_layout = ttk.LabelFrame(self.tab_general, text="4. Output Spacing", padding=10)
        self.frame_layout.pack(padx=10, pady=5, fill="x")
        self.combo_spacing = ttk.Combobox(self.frame_layout, values=["320x16 (8x8 ref)", "320x48 (16x16 ref)", "320x192 (32x32 ref)", "Custom"], state="readonly")
        self.combo_spacing.current(1)
        self.combo_spacing.pack(fill="x")
        
        # 1.5 Mask color
        self.frame_mask = ttk.LabelFrame(self.tab_general, text="5. Transparency Mask", padding=10)
        self.frame_mask.pack(padx=10, pady=5, fill="x")
        self.mask_enabled = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.frame_mask, text="Enable Color Mask", variable=self.mask_enabled).grid(row=0, column=0, sticky="w")
        ttk.Button(self.frame_mask, text="Pick Mask Color", command=self.pick_mask_color).grid(row=0, column=1, padx=10)
        self.lbl_mask_preview = tk.Label(self.frame_mask, text="      ", bg="#ff00ff", relief="sunken")
        self.lbl_mask_preview.grid(row=0, column=2)

        # TAB 2: EXCEPTIONS
        self.tab_ex = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_ex, text="Individual Exceptions")

        self.lbl_ex_info = ttk.Label(self.tab_ex, text="Fix characters that are bigger than the grid (e.g., hanging comma).", foreground="gray")
        self.lbl_ex_info.pack(pady=5)

        # Selector
        self.frame_ex_sel = ttk.Frame(self.tab_ex)
        self.frame_ex_sel.pack(fill="x", padx=10)
        
        ttk.Label(self.frame_ex_sel, text="Select Char:").pack(side="left")
        
        # Generate ASCII list for spinner: "0 [ ]", "1 [!]", etc.
        self.char_list = []
        for i in range(0, 150): # Standard range covers most game fonts
            char_vis = chr(i + 32) if i + 32 < 127 else "?"
            if i+32 == 32: char_vis = "Space"
            self.char_list.append(f"{i} : [{char_vis}]")
            
        self.combo_char = ttk.Combobox(self.frame_ex_sel, values=self.char_list, state="readonly", width=15)
        self.combo_char.current(12) # Default to comma area
        self.combo_char.pack(side="left", padx=5)

        # Inputs for overrides
        self.frame_ex_opt = ttk.LabelFrame(self.tab_ex, text="Modify Cut Box for this Char", padding=10)
        self.frame_ex_opt.pack(padx=10, pady=10, fill="x")

        # Grid for overrides
        ttk.Label(self.frame_ex_opt, text="Extra Width:", foreground="blue").grid(row=0, column=0)
        self.ex_dw = ttk.Entry(self.frame_ex_opt, width=5); self.ex_dw.insert(0,"0"); self.ex_dw.grid(row=0, column=1)

        ttk.Label(self.frame_ex_opt, text="Extra Height:", foreground="blue").grid(row=0, column=2)
        self.ex_dh = ttk.Entry(self.frame_ex_opt, width=5); self.ex_dh.insert(0,"0"); self.ex_dh.grid(row=0, column=3)

        ttk.Label(self.frame_ex_opt, text="Offset X:", foreground="red").grid(row=1, column=0)
        self.ex_dx = ttk.Entry(self.frame_ex_opt, width=5); self.ex_dx.insert(0,"0"); self.ex_dx.grid(row=1, column=1)

        ttk.Label(self.frame_ex_opt, text="Offset Y:", foreground="red").grid(row=1, column=2)
        self.ex_dy = ttk.Entry(self.frame_ex_opt, width=5); self.ex_dy.insert(0,"0"); self.ex_dy.grid(row=1, column=3)
        
        self.btn_add_ex = ttk.Button(self.frame_ex_opt, text="Set/Update Exception", command=self.add_exception)
        self.btn_add_ex.grid(row=2, column=0, columnspan=4, sticky="we", pady=5)

        # List of active exceptions
        self.tree = ttk.Treeview(self.tab_ex, columns=("ID", "Char", "Mods"), show='headings', height=8)
        self.tree.heading("ID", text="ID"); self.tree.column("ID", width=30)
        self.tree.heading("Char", text="Char"); self.tree.column("Char", width=40)
        self.tree.heading("Mods", text="Modifications"); self.tree.column("Mods", width=200)
        self.tree.pack(padx=10, fill="both", expand=True)
        
        self.btn_del_ex = ttk.Button(self.tab_ex, text="Remove Selected", command=self.remove_exception)
        self.btn_del_ex.pack(pady=5)

        # BOTTOM BUTTONS
        self.frame_actions = ttk.Frame(root)
        self.frame_actions.pack(padx=10, pady=10, fill="x", side="bottom")

        self.btn_preview = ttk.Button(self.frame_actions, text="PREVIEW CUTS", command=self.show_preview)
        self.btn_preview.pack(side="left", fill="x", expand=True, padx=5)

        self.btn_process = ttk.Button(self.frame_actions, text="SAVE", command=self.process_image)
        self.btn_process.pack(side="left", fill="x", expand=True, padx=5)
        
        # TAB 3: PROGRAM CREDITS
        self.tab_about = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_about, text="About")

        # TAB 3 CONTENT
        self.frame_auth = ttk.LabelFrame(self.tab_about, text="Authors", padding=10)
        self.frame_auth.pack(padx=10, pady=10, fill="x")
        self.lbl_auth_info = ttk.Label(self.frame_auth, text="FakeCells Software - Lead programming\nKelleesh24 - Script Supervisor\nLord Louvre - Script Contributions\nThird-party - Betatesting and feedback scripting", foreground="black")
        self.lbl_auth_info.pack(pady=5)
        
        self.frame_libs = ttk.LabelFrame(self.tab_about, text="Software used", padding=10)
        self.frame_libs.pack(padx=10, pady=10, fill="x")
        self.lbl_lib_info = ttk.Label(self.frame_libs, text="Pillow - by Jeffrey A. Clark and others (https://pypi.org/project/pillow/)\nThonny - by Aivar Annamaa (https://thonny.org/)", foreground="black")
        self.lbl_lib_info.pack(pady=5)
        
        self.frame_src = ttk.LabelFrame(self.tab_about, text="Support methods", padding=10)
        self.frame_src.pack(padx=10, pady=10, fill="x")
        self.lbl_src_info = ttk.Label(self.frame_src, text="You can support our project or contributors through our GitHub pages:\nhttps://github.com/fakecells/bitmap-cropper\nhttps://github.com/Kelleesh24/", foreground="black")
        self.lbl_src_info.pack(pady=5)

    # --- LOGIC ---

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.bmp")])
        if file_path:
            self.source_image_path = file_path
            self.source_filename = os.path.splitext(os.path.basename(file_path))[0]
            self.lbl_file_status.config(text=file_path.split("/")[-1], foreground="green")
            self.source_image = Image.open(file_path).convert("RGBA")
    
    def pick_mask_color(self):
        color = colorchooser.askcolor(title="Select background color to remove")
        if color[1]:
            self.mask_color = color[0] 
            self.lbl_mask_preview.config(bg=color[1])

    def add_exception(self):
        try:
            # Parse Selection "12 : [,]"
            sel_str = self.combo_char.get()
            idx = int(sel_str.split(":")[0].strip())
            
            dx = int(self.ex_dx.get())
            dy = int(self.ex_dy.get())
            dw = int(self.ex_dw.get())
            dh = int(self.ex_dh.get())
            
            # Store
            self.exceptions[idx] = {'dx': dx, 'dy': dy, 'dw': dw, 'dh': dh}
            self.refresh_tree()
            messagebox.showinfo("Added", f"Exception set for ID {idx}")
        except ValueError:
            messagebox.showerror("Error", "Inputs must be integers")

    def remove_exception(self):
        sel = self.tree.selection()
        if sel:
            item = self.tree.item(sel[0])
            idx = int(item['values'][0])
            del self.exceptions[idx]
            self.refresh_tree()

    def refresh_tree(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for idx, val in self.exceptions.items():
            char_vis = chr(idx + 32) if idx+32 < 127 else "?"
            mods = f"X:{val['dx']} Y:{val['dy']} W+{val['dw']} H+{val['dh']}"
            self.tree.insert("", "end", values=(idx, char_vis, mods))

    def get_config(self):
        # Gather all basic inputs
        return {
            'cw': int(self.entry_char_w.get()), 'ch': int(self.entry_char_h.get()),
            'offx': int(self.entry_off_x.get()), 'offy': int(self.entry_off_y.get()),
            'gapx': int(self.entry_gap_x.get()), 'gapy': int(self.entry_gap_y.get()),
        }

    def get_crop_boxes(self):
        if not self.source_image: return []
        cfg = self.get_config()
        
        # Determine Grid
        sel = self.combo_spacing.get()
        if "Custom" in sel:
            ref_w = int(self.entry_ref_w.get())
            ref_h = int(self.entry_ref_h.get())
            ref_tile = int(self.entry_ref_tile.get())
        else:
            if "8x8 ref" in sel: ref_w, ref_h, ref_tile = 320, 16, 8
            elif "16x16 ref" in sel: ref_w, ref_h, ref_tile = 320, 48, 16
            elif "32x32 ref" in sel: ref_w, ref_h, ref_tile = 320, 192, 32
            else: ref_w, ref_h, ref_tile = 320, 48, 16
            
        cols = ref_w // ref_tile
        rows = ref_h // ref_tile
        
        boxes = []
        
        # Grid Walking Logic
        cur_y = cfg['offy']
        
        # We calculate total glyphs needed
        total_glyphs = cols * rows
        
        # Iterate simply by index to map flat index -> (row, col) source logic
        # Assuming source is packed row by row
        
        src_w, src_h = self.source_image.size
        stride_x = cfg['cw'] + cfg['gapx']
        stride_y = cfg['ch'] + cfg['gapy']
        
        count = 0
        scan_y = cfg['offy']
        
        while scan_y < src_h and count < total_glyphs:
            scan_x = cfg['offx']
            while scan_x < src_w and count < total_glyphs:
                
                # BASE BOX
                x, y = scan_x, scan_y
                w, h = cfg['cw'], cfg['ch']
                
                # APPLY EXCEPTION?
                if count in self.exceptions:
                    ex = self.exceptions[count]
                    x += ex['dx']
                    y += ex['dy']
                    w += ex['dw']
                    h += ex['dh']
                
                boxes.append((x, y, x+w, y+h))
                
                scan_x += stride_x
                count += 1
            scan_y += stride_y
            
        return boxes, cols, rows

    def show_preview(self):
        try:
            boxes, _, _ = self.get_crop_boxes()
            preview = self.source_image.copy().convert("RGBA")
            draw = ImageDraw.Draw(preview)
            
            for b in boxes:
                draw.rectangle(b, outline="red", width=1)
                
            # Pop up
            top = Toplevel(self.root)
            top.title("Preview Cuts")
            
            # Zoom
            if preview.width < 300: preview = preview.resize((preview.width*2, preview.height*2), Image.NEAREST)
            
            self.tk_prev = ImageTk.PhotoImage(preview)
            ttk.Label(top, image=self.tk_prev).pack()
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
            print("Error:", str(e))

    def process_image(self):
        try:
            boxes, cols, rows = self.get_crop_boxes()
            cfg = self.get_config()
            
            # Create Target
            out_w = cols * cfg['cw']
            out_h = rows * cfg['ch']
            new_img = Image.new("RGBA", (out_w, out_h), (0,0,0,0))
            
            # Crop & Paste
            for idx, box in enumerate(boxes):
                if idx >= cols*rows: break
                
                glyph = self.source_image.crop(box)
                
            # Mask color logic
            if self.mask_enabled.get():
                glyph = glyph.convert("RGBA")
                datas = glyph.getdata()
                newData = []
                for item in datas:
                    # If pixel matches mask color, set Alpha to 0
                    if item[0] == self.mask_color[0] and item[1] == self.mask_color[1] and item[2] == self.mask_color[2]:
                        newData.append((0, 0, 0, 0))
                    else:
                        newData.append(item)
                    glyph.putdata(newData)
                    
                # Calculate paste position
                r = idx // cols
                c = idx % cols
                px = c * cfg['cw']
                py = r * cfg['ch']
                
                # Logic: If glyph is BIGGER than target slot, we assume it's an overlay
                # and paste it at px, py (top-left aligned). 
                # If user added offset in exception, it was to FIND the glyph in source.
                # If they want to offset it in TARGET, that's different, but standard repacking 
                # usually aligns top-left of the cell.
                
                new_img.paste(glyph, (px, py), glyph) # Use glyph as mask for transparency
                
            default_name = f"{self.source_filename}-repacked.png" if self.source_image_path else "repacked_font.png"
                
            save_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                initialfile=default_name,
                filetypes=[("PNG Image", "*.png")])
            
            if save_path:
                new_img.save(save_path)
                msg = (f"The repacked charset has been saved succesfully!\n\n"
                       f"Grid Layout: {cols} Cols x {rows} Rows\n"
                       f"Output Size: {out_w}x{out_h}\n\n"
                       f"Saved to: {save_path}")
                messagebox.showinfo("Done", msg)
                
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = BitmapCropperApp(root)
    root.mainloop()
