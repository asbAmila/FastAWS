from fastapi import FastAPI
from PIL import Image
import requests
from io import BytesIO
import io
from PIL import Image, ImageDraw, ImageFont
from PIL import ImageColor

import httpx
import os
import base64
import json
import random
from fastapi.responses import StreamingResponse


import google.generativeai as genaii
app = FastAPI()




@app.get('/hello')
async def root():
    return {'example' : 'This is an example', 'data':0}

@app.get('/gemini/')
async def disDamge():

    #image_path = filepath

    image_path = "Img\Vz2.jpg"

    genaii.configure(api_key="AIzaSyBx_T-BRtydVXI-9JBpZmtvXP4bF7c7V-0")
    model = genaii.GenerativeModel("gemini-2.0-flash-exp")
    with open(image_path, 'rb') as f:
        image_data = f.read()

    prompt = "Explain damage of this vehicale and find the model, make and model year"
    response = model.generate_content([{'mime_type':'image/jpeg', 'data': base64.b64encode(image_data).decode('utf-8')}, prompt])

    def stream():
        for chunk in response:
            yield 'data: %s\n\n' % json.dumps({ "text": chunk.text })

    return stream(), {'Content-Type': 'text/event-stream'}

@app.get("/items/{filepath:path}")
async def read_item(filepath: str):
    return {"item_id": filepath}

bounding_box_system_instructions = """
    Return bounding boxes as a JSON array with labels. Never return masks or code fencing. limit to only the most suitable damage area with a minimum of 1 and maximum 10.
    If an object is present multiple times, name them according to their unique characteristic (colors, size, position, unique characteristics, etc..).
      """

from google.genai import types

safety_settings = [
    types.SafetySetting(
        category="HARM_CATEGORY_DANGEROUS_CONTENT",
        threshold="BLOCK_ONLY_HIGH",
    ),
]

additional_colors = [colorname for (colorname, colorcode) in ImageColor.colormap.items()]

from google import genai


client = genai.Client(api_key="AIzaSyBx_T-BRtydVXI-9JBpZmtvXP4bF7c7V-0")

model_name = "gemini-2.0-flash-exp"



@app.post("/2dbox")
async def imageBounding(name: str):
    
#name: str
    def plot_bounding_boxes(im, bounding_boxes):
        """
        Plots bounding boxes on an image with markers for each a name, using PIL, normalized coordinates, and different colors.

        Args:
            img_path: The path to the image file.
            bounding_boxes: A list of bounding boxes containing the name of the object
            and their positions in normalized [y1 x1 y2 x2] format.
        """

        # Load the image
        img = im
        width, height = img.size
        print(img.size)
        # Create a drawing object
        draw = ImageDraw.Draw(img)

        # Define a list of colors
        colors = [
        'red',
        'green',
        'blue',
        'yellow',
        'orange',
        'pink',
        'purple',
        'brown',
        'gray',
        'beige',
        'turquoise',
        'cyan',
        'magenta',
        'lime',
        'navy',
        'maroon',
        'teal',
        'olive',
        'coral',
        'lavender',
        'violet',
        'gold',
        'silver',
        ] + additional_colors

        # Parsing out the markdown fencing
        bounding_boxes = parse_json(bounding_boxes)

        font_folder = 'Font'
        font_file = 'NotoSans_Condensed-Regular.ttf'
        font_path = os.path.join(font_folder, font_file)

        font = ImageFont.truetype(font_path, size=14)

        # Iterate over the bounding boxes
        for i, bounding_box in enumerate(json.loads(bounding_boxes)):
        # Select a color from the list
            color = colors[i % len(colors)]

            # Convert normalized coordinates to absolute coordinates
            abs_y1 = int(bounding_box["box_2d"][0]/1000 * height)
            abs_x1 = int(bounding_box["box_2d"][1]/1000 * width)
            abs_y2 = int(bounding_box["box_2d"][2]/1000 * height)
            abs_x2 = int(bounding_box["box_2d"][3]/1000 * width)

            if abs_x1 > abs_x2:
                abs_x1, abs_x2 = abs_x2, abs_x1

            if abs_y1 > abs_y2:
                abs_y1, abs_y2 = abs_y2, abs_y1

            # Draw the bounding box
            draw.rectangle(
                ((abs_x1, abs_y1), (abs_x2, abs_y2)), outline=color, width=4
            )

            # Draw the text
            if "label" in bounding_box:
                draw.text((abs_x1 + 8, abs_y1 + 6), bounding_box["label"], fill=color, font=font)

        # Display the image
        # img.show()

    #     buffered = io.BytesIO()
    #     img.save(buffered, format="PNG")  # Or "JPEG", or whatever format you like.
    #     img_str = base64.b64encode(buffered.getvalue()).decode()
    # # Return the base64 encoded image string
    #     return img_str
        # img.save("output_image.png", format="PNG")  # Save the image locally
        # print("Image saved as 'output_image.png'")
        # return "output_image.png"

        # Save the image to a BytesIO stream
        img_stream = io.BytesIO()
        im.save(img_stream, format="PNG")
        img_stream.seek(0)

    # Return the image as a StreamingResponse
        return StreamingResponse(img_stream, media_type="image/png")

     
    # @title Parsing JSON output
    def parse_json(json_output):
        # Parsing out the markdown fencing
        lines = json_output.splitlines()
        for i, line in enumerate(lines):
            if line == "```json":
                json_output = "\n".join(lines[i+1:])  # Remove everything before "```json"
                json_output = json_output.split("```")[0]  # Remove everything after the closing "```"
                break  # Exit the loop once "```json" is found
        return json_output
    
    #image = name

    image = "https://fastapitestcf.s3.ap-southeast-1.amazonaws.com/Vz2.jpg"
    #image = "Img\\" + name

    prompt = "Accurately detect the 2D bounding boxes areas of this vehicle each damaged(e.g., dents, scratches, cracks) area and vehicle(with colour)"  

    # img = Image.open(BytesIO(open(image, "rb").read()))
    # im = Image.open(image).resize((1024, int(1024 * img.size[1] / img.size[0])), Image.Resampling.LANCZOS)

    #for url open AWS s3
    response = requests.get(image)
    img = Image.open(BytesIO(response.content))
    im = img.resize((1024, int(1024 * img.size[1] / img.size[0])), Image.Resampling.LANCZOS)


    # Run model to find bounding boxes
    response = client.models.generate_content(
        model=model_name,
        contents=[prompt, im],
        config = types.GenerateContentConfig(
            system_instruction=bounding_box_system_instructions,
            temperature=2.0,
            safety_settings=safety_settings,
        )
    )
    

    #return {'data' : response.text}

    response = plot_bounding_boxes(im, response.text)

    return  response


    



