---
description: Create transparent PNG from AI-generated images (from prompt)
---

# Create Transparent PNG from Prompt Workflow

This workflow generates a new image from a text prompt and then converts it to a transparent PNG.

## Prerequisites

- Python 3.10+ installed
- uv installed
- pngalpha installed (`uv tool install https://github.com/BK927/transparent-png-python.git`)

## Steps

### 1. Generate Base Image on Neutral Background

First, generate your subject on a solid color background that contrasts with the subject (avoid white/black).

Example colors: blue (#0066CC), green (#00CC66), purple (#6600CC)

```
Use generate_image tool with your subject description + "on a solid [color] background #[hex]"
```

### 2. Convert to White Background

Use the generated image as input and change only the background to white.

```
Use generate_image tool with:
- ImagePaths: [path to base image from step 1]
- Prompt: "Change ONLY the background color to pure solid white #FFFFFF. Keep the subject exactly the same - same position, same shape, same style. Only replace the [color] background with pure white background."
```

### 3. Convert to Black Background

Use the white background image as input and change only the background to black.

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

View the generated transparent PNG file to verify the alpha extraction worked correctly.

```
Use view_file tool on the output PNG path
```
