---
description: Create transparent PNG from an existing image file
---

# Create Transparent PNG from Existing Image Workflow

This workflow takes an existing image file and creates a transparent PNG by generating white and black background variants.

## Prerequisites

- Python 3.10+ installed
- uv installed
- pngalpha installed (`uv tool install https://github.com/BK927/transparent-png-python.git`)

## Steps

### 1. Identify Input Image

Identify the path to your existing source image. Ideally, this image should have a relatively simple background, but it's not strictly required.

```
Input Image Path: [path to your image]
```

### 2. Convert to White Background

Use the input image as reference and change only the background to white using AI editing.

```
Use generate_image tool with:
- ImagePaths: [path to input image]
- Prompt: "Change ONLY the background color to pure solid white #FFFFFF. Keep the subject exactly the same - same position, same shape, same style. Only replace the background with pure white background."
```

### 3. Convert to Black Background

Use the white background image (generated in step 2) as reference and change only the background to black. 
(Using the white-bg version as reference often yields better consistency than the original if the original had a complex background)

```
Use generate_image tool with:
- ImagePaths: [path to white background image from step 2]
- Prompt: "Change ONLY the background color to pure solid black #000000. Keep the subject exactly the same - same position, same shape, same style. Only replace the white background with pure black background."
```

### 4. Extract Alpha Channel

Run the pngalpha tool to create the transparent PNG.

// turbo
```bash
pngalpha "<white_background_image_path>" "<black_background_image_path>" "<output_transparent_png_path>"
```

### 5. Verify Result

View the generated transparent PNG file.

```
Use view_file tool on the output PNG path
```
