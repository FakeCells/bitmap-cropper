# Bitmap Font Cropper / Repacker (BMFC / BMFR)

<img width="128" height="128" alt="bmfr" src="https://github.com/user-attachments/assets/5d87ff8a-2c8a-424f-b896-67c319e94623" />

This is a tool created using Python that repacks your charsets into a charset that it's compatible with OldSkool DemoMaker or CODEF spacing formats, following also the ASCII character order format (320x16, 320x48, 320x192).

## Notes:

This tool is intended to be used in OldSkool DemoMaker or CODEF projects, or others that have an ASCII character order format.
It's recommneded the use of charsets that have the ASCII character order format in order to reduce repacking mismatches (extra characters, character index errors, etc...) (ex: From The Spriters Resource or bmf.wz.cz), altough you can configure the output files with the avaliable options in the program.

## Main Information:

### Program Features:

Note: Some of these features can be found in later versions, specified after a feature description.
* Charset Configuration: You can input the source file, the size (base grid) of your font characters (e.g., 8x16 or 21x21) and a mask color **(masking only in v4.0 and later versions).**
* Charset Spacing: The program crops the characters by the size of each character that has been set earlier, and multiply it by a determined quantity of times by the X and Y size of the charset spacing (example: font has 8x16 size and charset spacing is 320x48 (16x16), multiply 8x20 x and 16x3 y to fill the image, making the output file with size of 160x48).
* Charset Offset Controls: You can handle the charset cropping offsets (wrapping) in the X and Y axis, size above (top headers/margins), and size under (line gap) and horizontal spacings. **(v2.0 and later)**
* Region Limit Controls (Regions of interest): You can limit where the program can crop the characters (in X and Y axis coordinates) in order to avoid errors related to mixed fonts (if there is a charset with multiple fonts in a single file). It defines a bounding box (Start X/Y, End X/Y) that makes the scanner completely ignore anything outside this box. **(v4.0 and later)**
* Individual exceptions: A space gaps manager for individual characters (a per-character override), that has a visual list of customized characters and options to handle characters that are outside the grid lines. **(v3.0 and later)**
* Character Relocation: A manager for scrambled character source indexes that relocates them into a target index slot. **(v4.0 and later)**
* Output options: The main feature of the program, where you can set the output spacing to three types of reference grid formats: 8x8 - 320x16 (20x2 grid), 16x16 - 320x48 (20x3 grid), 32x32 - 320x192 (10x6 grid) **(v2.0 and later)**, the output scale, start Idx offset and padding options **(v4.0 and later)**, and custom grid scaling by column and row values **(v6.0 and later).**
* Previsualization Window: It's just a preview of the crops/cuts, relocation targets, individual exception offsets and grid limits. Along with mouse coordinates info, zoom options, and other data related with the charset settings. **(v2.0 and later)**

## How to use (Basic Functions):

### 1. Import and transparency:

Location: Tab 1: "General Settings" > "Section 1 (Import Font & Mask Transparency)"

The general settings to get started with the font repack.

- Select Image: As the name of this option, this allows you to load your source font sheet (.png, .bmp, .jpg).
- Set Mask Color: If your source image has a background color (e.g., bright pink or black) that you want to be transparent in the final file, follow the instructions:

1. Check the box "Enable mask" to activate transparency.
2. Click Set Mask Color.
3. Pick the background color from the color chooser.

### 2. Defining the Grid

Location: Tab 1: "General Settings" > "Section 2: Base Grid Size & Orientation"

This tells the program how big (width and height in pixels) one character is supposed to be, and from where the grid is going to be scanned.

- Char W / Char H: Input the width and height of a single character (e.g., 8 width and 16 height).
- Scan Dir (Orientation):
1. Horizontal (Z-pattern): Scans left-to-right, then moves down to the next line. (Standard for most charsets).
2. Vertical (N-pattern): Scans top-to-bottom, then moves right to the next column. (Used for some vertical charsets).

### 3. Handling Messy Sources (Offsets & Gaps)

Location: Tab 1: "General Settings" > "Section 3: Global Offsets (Wrapping) & Gaps"

Most ripped fonts aren't perfectly aligned. Use these settings to line up your grid.

- Wrap Offset X / Y: shifts the starting position of the scan. (v5.0 and later versions uses Smart Wrapping. If you shift the image, parts that go off the edge "wrap around" to the other side. This is useful if a font starts halfway through the image, and that's the reason why the charset seems to be moving at the wrap offset coordinates)
- Gap X / Y: Adds spacing between cuts. (Example: If characters have a 1-pixel line separating them, set Gap X to 1.)

### 4. Focusing the Scan (Source Region Limits)

Location: Tab 1: "General Settings" > "Section 4: Source Region Limits (Optional)"

If your image contains extra graphics (like a game logo, UI elements or even more fonts in one file) that you don't want to include, use this section to set a limit between the desired font and the additional graphics (Check the "Enable Limits" checkbox first if you are about to use this feature):

- Start X / Start Y: The top-left corner where scanning begins.
- End X / End Y: The bottom-right corner where scanning stops.

Tip: Use the Preview Window to find these coordinates easily by hovering your mouse.

<img width="281" height="226" alt="bmfr5_region_limits" src="https://github.com/user-attachments/assets/7d66ec4e-fa5d-4459-af1c-294ba94e1f09" />

Source region limit usage example (from BMFR v5.0)

### 5. Output Configuration:

Location: Tab 1: "General Settings" > "Section 5: Output Spacing, Padding & Scaling"

Controls how the output file will look, tweaking options like the Layout Preset, Output Scale, Padding Coordinates and Idx offset.

- Layout Preset: Choose standard formats like 320x48 (16x16 ref) (common for retro demos) or Custom formats (custom columns and rows).
- Output Scale: Resizes the final image (e.g., 2.0x doubles the size), using "Nearest Neighbor" scaling.
- Pad X / Pad Y: Adds empty space inside each character cell in the output. (Example: A 8x8 char with Pad X: 2 becomes 10x8 in the output file.)
- Start Idx Offset: Leaves empty slots at the beginning of the output grid. (Example: If there's no "Space" in the first character slot, set the "Idx Offset" to 32 to skip the first 32 ASCII slots (control characters), so your font starts at "Space".)

## How to use (Advanced Functions):

### 1. Fixing Broken Characters (Exceptions)

Location: Tab 2: "Individual Exceptions"

Use this for characters that don't fit the standard grid (e.g., a hanging "j" or a wide "w"). 

- Select Source Char Index: Choose the ID of the problem character (e.g., ID 12 is often ",").
- Extra Width/Height: Expands the cut box for just this character.
- Offset X/Y: Moves the cut box for just this character.
- Set/Update Exception: It's just the button to set or update the exception.

<img width="321" height="316" alt="bmfr6_exceptions" src="https://github.com/user-attachments/assets/c5994b7c-d2e6-437a-8ac5-43c588b987dd" />
<img width="281" height="226" alt="bmfr6_exceptions_preview" src="https://github.com/user-attachments/assets/6d98ee5c-8c6e-4feb-9258-a31615702cc2" />

Character exceptions usage example (from BMFR v6.0)

### 2. Reordering Characters (Relocation)

Location: Tab 2: "Character Relocation"

Use this if the font characters are scrambled or not in ASCII order.

- Put Source ID: The order the character appears in the original image (e.g., the 5th character scanned is 'A', so ID=4).
- Into Target Position: Where it should be in the final file (e.g., 'A' is usually ASCII 65, or index 33 in some sets (OSDM, CODEF sets)).
- Set Mapping: The button to set the mapping/relocation.

<img width="321" height="316" alt="bmfr6_relocation" src="https://github.com/user-attachments/assets/b2810088-5d69-446a-8801-fe9010e8a8ce" />
<img width="281" height="226" alt="bmfr6_relocation_preview" src="https://github.com/user-attachments/assets/8564c3e6-0716-48b0-aaf5-070943c38d04" />

Character relocation usage example (from BMFR v6.0)

## Acknowledgements:
### Authors:
- FakeCells Software - Lead programming
- @Kelleesh24 - Script Supervisor
- Lord Louvre - Script Contributions
- Third-party - Betatesting and feedback scripting
### Software used:
This software was made using the Pillow Python library licensed under the MIT-CMU open source license.

Pillow by Jeffrey A. Clark and others (https://pypi.org/project/pillow/) (https://github.com/python-pillow/Pillow/)
